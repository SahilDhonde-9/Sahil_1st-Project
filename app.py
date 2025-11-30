from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, abort, send_file
from models import Base, engine, SessionLocal, Trip, TripItem, Attraction, User, PackingItem
from seed_data import seed
from itinerary import plan_itinerary
import os
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from io import BytesIO
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.lib import colors
from datetime import datetime

app = Flask(__name__)
app.secret_key = "dev-secret"  # for flash messages, should be a strong random key in production

# Flask-Login setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    session = SessionLocal()
    user = session.query(User).get(int(user_id))
    session.close()
    return user

# Ensure DB exists and seed attractions
with app.app_context():
    Base.metadata.create_all(engine)
    seed()

def get_session():
    return SessionLocal()

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        session = get_session()
        existing_user = session.query(User).filter_by(username=username).first()
        if existing_user:
            flash("Username already exists. Please choose a different one.")
            session.close()
            return redirect(url_for('signup'))
        
        new_user = User(username=username)
        new_user.set_password(password)
        session.add(new_user)
        session.commit()
        login_user(new_user)
        flash("Account created and logged in successfully!")
        session.close()
        return redirect(url_for('trips'))
    return render_template("signup.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        session = get_session()
        user = session.query(User).filter_by(username=username).first()
        session.close()
        if user and user.check_password(password):
            login_user(user)
            flash("Logged in successfully!")
            return redirect(url_for('trips'))
        else:
            flash("Invalid username or password.")
    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.")
    return redirect(url_for('index'))

@app.route("/trips")
@login_required
def trips():
    session = get_session()
    trips = session.query(Trip).filter_by(user_id=current_user.id).order_by(Trip.id.desc()).all()
    session.close()
    return render_template("trips.html", trips=trips)


@app.route("/create_trip", methods=["GET"])
@login_required
def create_trip_form():
    return render_template("create_trip.html")

@app.route("/plan", methods=["POST"])
@login_required
def plan():
    name = request.form.get("name", "My Trip")
    city = request.form.get("city", "Mumbai")
    start_date = request.form.get("start_date", "2025-09-01")
    days = int(request.form.get("days", "2"))
    interests = request.form.getlist("interests")
    interests_csv = ",".join(interests)
    budget = float(request.form.get("budget", 0.0)) # Get budget from form

    session = get_session()
    try:
        trip = Trip(name=name, city=city, start_date=start_date, days=days, interests=interests_csv, user_id=current_user.id, budget=budget)
        session.add(trip)
        session.commit()

        plan_itinerary(city=city, start_date=start_date, days=days, interests_csv=interests_csv, trip_id=trip.id)

        flash("Trip created successfully!")
        return redirect(url_for("view_trip", trip_id=trip.id))
    finally:
        session.close()

@app.route("/trip/<int:trip_id>")
@login_required
def view_trip(trip_id):
    session = get_session()
    try:
        trip = session.query(Trip).filter_by(id=trip_id, user_id=current_user.id).first()
        if not trip:
            abort(404)
        items = session.query(TripItem).filter(TripItem.trip_id==trip_id).order_by(TripItem.day, TripItem.order_index).all()
        packing_items = session.query(PackingItem).filter_by(trip_id=trip_id).all() # Fetch packing items

        # Dummy cost estimation (can be more sophisticated)
        food_cost_per_day = 500
        travel_cost_per_day = 1000
        entry_cost_per_day = 300
        estimated_cost_per_day = food_cost_per_day + travel_cost_per_day + entry_cost_per_day
        total_estimated_cost = estimated_cost_per_day * trip.days

        budget_remaining = trip.budget - total_estimated_cost
        budget_percentage_used = (total_estimated_cost / trip.budget) * 100 if trip.budget > 0 else 0
        budget_percentage_used = min(100, max(0, budget_percentage_used)) # Cap between 0 and 100

        # Build day-wise structure and map points
        days = {}
        for it in items:
            a = session.get(Attraction, it.attraction_id)
            days.setdefault(it.day, []).append({
                "name": a.name,
                "lat": a.lat,
                "lon": a.lon,
                "start": it.start_time,
                "end": it.end_time,
                "category": a.category,
                "duration": a.duration_hours
            })
        return render_template("itinerary.html", trip=trip, days=days, packing_items=packing_items,
                               estimated_cost_per_day=estimated_cost_per_day, total_estimated_cost=total_estimated_cost,
                               budget_remaining=budget_remaining, budget_percentage_used=budget_percentage_used)
    finally:
        session.close()

@app.route("/add_packing_item/<int:trip_id>", methods=["POST"])
@login_required
def add_packing_item(trip_id):
    session = get_session()
    try:
        trip = session.query(Trip).filter_by(id=trip_id, user_id=current_user.id).first()
        if not trip:
            abort(404)
        item_name = request.form.get("item_name")
        if item_name:
            new_item = PackingItem(trip_id=trip.id, item_name=item_name)
            session.add(new_item)
            session.commit()
            flash("Packing item added!")
        return redirect(url_for('view_trip', trip_id=trip.id))
    finally:
        session.close()

@app.route("/toggle_packing_item/<int:item_id>", methods=["POST"])
@login_required
def toggle_packing_item(item_id):
    session = get_session()
    try:
        item = session.query(PackingItem).filter_by(id=item_id).first()
        if not item:
            abort(404)
        # Ensure the item belongs to the current user's trip
        if item.trip.user_id != current_user.id:
            return jsonify({"success": False, "message": "Unauthorized"}), 403

        item.is_packed = not item.is_packed
        session.commit()
        return jsonify({"success": True, "is_packed": item.is_packed})
    finally:
        session.close()

@app.route("/delete/<int:trip_id>", methods=["POST"])
@login_required
def delete_trip(trip_id):
    session = get_session()
    try:
        trip_to_delete = session.query(Trip).filter_by(id=trip_id, user_id=current_user.id).first()
        if not trip_to_delete:
            abort(404)
        session.query(TripItem).filter(TripItem.trip_id==trip_to_delete.id).delete()
        session.query(PackingItem).filter(PackingItem.trip_id==trip_to_delete.id).delete() # Delete associated packing items
        session.delete(trip_to_delete)
        session.commit()
        flash("Trip deleted.")
        return redirect(url_for("trips"))
    finally:
        session.close()

@app.route("/download_itinerary/<int:trip_id>")
@login_required
def download_itinerary(trip_id):
    session = get_session()
    try:
        trip = session.query(Trip).filter_by(id=trip_id, user_id=current_user.id).first()
        if not trip:
            abort(404)
        items = session.query(TripItem).filter(TripItem.trip_id==trip_id).order_by(TripItem.day, TripItem.order_index).all()

        # Build day-wise structure for PDF
        days_data = {}
        for it in items:
            a = session.get(Attraction, it.attraction_id)
            days_data.setdefault(it.day, []).append({
                "name": a.name,
                "category": a.category,
                "start": it.start_time,
                "end": it.end_time,
                "duration": a.duration_hours
            })

        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, rightMargin=inch/2, leftMargin=inch/2, topMargin=inch/2, bottomMargin=inch/2)
        styles = getSampleStyleSheet()
        story = []

        # Title
        story.append(Paragraph(f"Trip Itinerary: {trip.name}", styles['h1']))
        story.append(Spacer(1, 0.2 * inch))

        # Trip Details
        story.append(Paragraph(f"City: {trip.city}", styles['h3']))
        story.append(Paragraph(f"Start Date: {trip.start_date}", styles['h3']))
        story.append(Paragraph(f"Days: {trip.days}", styles['h3']))
        story.append(Paragraph(f"Interests: {trip.interests or '—'}", styles['h3']))
        story.append(Spacer(1, 0.4 * inch))

        # Day-wise Itinerary
        for day_num in sorted(days_data.keys()):
            story.append(Paragraph(f"Day {day_num}", styles['h2']))
            story.append(Spacer(1, 0.1 * inch))
            if days_data[day_num]:
                for item in days_data[day_num]:
                    story.append(Paragraph(f"- {item['name']} ({item['start']} - {item['end']}) - {item['category']} ({item['duration']:.1f}h)", styles['Normal']))
                story.append(Spacer(1, 0.2 * inch))
            else:
                story.append(Paragraph("No activities planned for this day.", styles['Normal']))
                story.append(Spacer(1, 0.2 * inch))
            story.append(PageBreak())

        # Map Placeholder
        story.append(Paragraph("Map Snapshot: [Map visualization would go here]", styles['h2']))
        story.append(Paragraph("Due to limitations, a dynamic map snapshot cannot be generated in the PDF. Please refer to the web application for interactive maps.", styles['Normal']))
        story.append(Spacer(1, 0.2 * inch))

        doc.build(story)
        buffer.seek(0)

        return send_file(buffer, mimetype='application/pdf', as_attachment=True, download_name=f'{trip.name}_itinerary.pdf')
    finally:
        session.close()

if __name__ == "__main__":
    app.run(debug=True)
