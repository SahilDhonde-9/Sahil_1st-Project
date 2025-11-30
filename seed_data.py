from models import Base, engine, SessionLocal, Attraction
from sqlalchemy import select

# Basic curated data (with image paths)
SEED_ATTRACTIONS = [
    # Mumbai
    ("Mumbai", "Gateway of India", "history", 1.5, 18.9220, 72.8347, "assets/gateway-of-india.jpg"),
    ("Mumbai", "Chhatrapati Shivaji Maharaj Terminus", "architecture", 1.5, 18.9402, 72.8356, "assets/cst.jpg"),
    ("Mumbai", "Marine Drive", "nature", 2.0, 18.9430, 72.8238, "assets/mumbai/marine.jpg"),
    ("Mumbai", "Elephanta Caves", "history", 3.0, 18.9647, 72.9315, "assets/caves.jpg"),
    ("Mumbai", "Siddhivinayak Temple", "temple", 1.0, 19.0176, 72.8305, "assets/Siddhivinayak Temple.jpg"),
    ("Mumbai", "Haji Ali Dargah", "religion", 1.2, 18.9823, 72.8087, "assets/hq720.jpg"),
    ("Mumbai", "Colaba Causeway", "shopping", 1.5, 18.9223, 72.8336, "assets/Colaba Causeway.jpg"),
    ("Mumbai", "Juhu Beach", "nature", 1.8, 19.0988, 72.8267, "assets/Juhu Beach.jpg"),
    ("Mumbai", "Chhatrapati Shivaji Maharaj Vastu Sangrahalaya", "history", 2.0, 18.9278, 72.8322, "assets/museum.jpg"),
    ("Mumbai", "Global Vipassana Pagoda", "religion", 2.5, 19.2250, 72.7930, "assets/pagoda.jpg"),
    ("Mumbai", "Film City", "entertainment", 3.0, 19.1670, 72.8628, "assets/filmcity.jpg"),
    ("Mumbai", "Powai Lake", "nature", 1.5, 19.1199, 72.9070, "assets/powai.jpg"),
    ("Mumbai", "EsselWorld", "entertainment", 4.0, 19.2760, 72.8070, "assets/esselworld.jpg"),
    ("Mumbai", "Kanheri Caves", "history", 2.5, 19.2150, 72.9200, "assets/kanheri.jpg"),
    ("Mumbai", "Bandra Worli Sea Link", "architecture", 1.0, 19.0360, 72.8160, "assets/sea link.jpg"),
    ("Mumbai", "Dharavi Slum Tour", "culture", 2.0, 19.0400, 72.8500, "assets/dharavi.jpg"),

    # Pune
    ("Pune", "Shaniwar Wada", "history", 1.5, 18.5196, 73.8553, "assets/pune/shaniwarwada.jpg"),
    ("Pune", "Aga Khan Palace", "history", 1.5, 18.5525, 73.9034, "assets/pune/agakhan.jpg"),
    ("Pune", "Sinhagad Fort", "nature", 3.0, 18.3663, 73.7559, "assets/pune/sinhagad.jpg"),
    ("Pune", "Dagadusheth Halwai Ganapati Temple", "temple", 1.0, 18.5164, 73.8554, "assets/pune/dagadusheth.jpg"),
    ("Pune", "Pataleshwar Cave Temple", "temple", 1.0, 18.5304, 73.8462, "assets/pune/pataleshwar.jpg"),
    ("Pune", "FC Road (Shopping)", "shopping", 1.5, 18.5208, 73.8419, "assets/pune/fc_road.jpg"),
    ("Pune", "Raja Dinkar Kelkar Museum", "history", 2.0, 18.5120, 73.8510, "assets/pune/kelkar.jpg"),
    ("Pune", "Parvati Hill", "nature", 1.5, 18.4980, 73.8400, "assets/pune/parvati.jpg"),
    ("Pune", "Katraj Snake Park", "nature", 2.0, 18.4500, 73.8600, "assets/pune/katraj.jpg"),
    ("Pune", "Osho International Meditation Resort", "religion", 2.5, 18.5600, 73.9000, "assets/pune/osho.jpg"),
    ("Pune", "Phoenix Market City", "shopping", 3.0, 18.5600, 73.9200, "assets/pune/phoenix.jpg"),
    ("Pune", "National War Memorial Southern Command", "history", 1.0, 18.5300, 73.8700, "assets/pune/war_memorial.jpg"),
    ("Pune", "Appu Ghar Amusement Park", "entertainment", 4.0, 18.6200, 73.7800, "assets/pune/appu_ghar.jpg"),

    # Nashik
    ("Nashik", "Trimbakeshwar Temple", "temple", 2.0, 19.9408, 73.5291, "assets/nashik/trimbakeshwar.jpg"),
    ("Nashik", "Sula Vineyards", "food", 2.5, 20.0112, 73.7336, "assets/nashik/sula.jpg"),
    ("Nashik", "Panchavati", "religion", 1.5, 20.0059, 73.7906, "assets/nashik/panchavati.jpg"),
    ("Nashik", "Pandav Leni Caves", "history", 1.5, 20.0069, 73.7796, "assets/nashik/pandavleni.jpg"),
    ("Nashik", "Anjneri Hill", "nature", 3.0, 19.9640, 73.6373, "assets/nashik/anjneri.jpg"),
    ("Nashik", "Kalaram Temple", "temple", 1.0, 20.0000, 73.7800, "assets/nashik/kalaram.jpg"),
    ("Nashik", "Ramkund", "religion", 1.0, 20.0000, 73.7800, "assets/nashik/ramkund.jpg"),
    ("Nashik", "Coin Museum", "history", 1.5, 20.0000, 73.7800, "assets/nashik/coin_museum.jpg"),
    ("Nashik", "Dudhsagar Falls (Nashik)", "nature", 2.0, 20.0000, 73.7800, "assets/nashik/dudhsagar.jpg"),
    ("Nashik", "Saptashrungi Devi Temple", "temple", 2.5, 20.0000, 73.7800, "assets/nashik/saptashrungi.jpg"),
    ("Nashik", "Sita Gufa", "religion", 1.0, 20.0000, 73.7800, "assets/nashik/sita_gufa.jpg"),
    ("Nashik", "Sundarnarayan Temple", "temple", 1.0, 20.0000, 73.7800, "assets/nashik/sundarnarayan.jpg"),
]

def seed():
    Base.metadata.create_all(engine)
    session = SessionLocal()

    # Only seed once
    existing = session.execute(select(Attraction)).first()
    if existing:
        session.close()
        return

    for city, name, cat, dur, lat, lon, img in SEED_ATTRACTIONS:
        a = Attraction(city=city, name=name, category=cat, duration_hours=dur, lat=lat, lon=lon, image_path=img)
        session.add(a)
    session.commit()
    session.close()

if __name__ == "__main__":
    seed()
