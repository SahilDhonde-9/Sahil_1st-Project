import math
from datetime import datetime, timedelta
from typing import List, Dict, Any
from models import SessionLocal, Attraction, TripItem

DAILY_HOURS = 7.0

def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    c = 2*math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R*c  # kilometers

CITY_CENTERS = {
    "Mumbai": (18.9388, 72.8354),
    "Pune": (18.5204, 73.8567),
    "Nashik": (19.9975, 73.7898),
}

def filter_attractions(all_attractions: List[Attraction], interests: List[str]) -> List[Attraction]:
    if not interests:
        return all_attractions
    filtered = [a for a in all_attractions if a.category.lower() in interests]
    if len(filtered) < 4:
        # backfill with popular places if too few
        names = {a.name for a in filtered}
        for a in all_attractions:
            if a.name not in names:
                filtered.append(a)
            if len(filtered) >= max(6, len(all_attractions)//2):
                break
    return filtered

def plan_itinerary(city: str, start_date: str, days: int, interests_csv: str, trip_id: int):
    session = SessionLocal()
    try:
        attractions = session.query(Attraction).filter(Attraction.city == city).all()
        interests = [i.strip().lower() for i in interests_csv.split(',') if i.strip()]
        candidates = filter_attractions(attractions, interests)

        # Greedy nearest-neighbor per day, respecting time budget
        center = CITY_CENTERS.get(city, (candidates[0].lat, candidates[0].lon))
        remaining = set(a.id for a in candidates)
        current_date = datetime.strptime(start_date, "%Y-%m-%d")
        for day in range(1, days+1):
            day_hours = 0.0
            day_items = []
            cur_lat, cur_lon = center

            while remaining:
                # pick nearest remaining
                nearest = None
                nearest_dist = 1e9
                for aid in list(remaining):
                    a = next(x for x in candidates if x.id == aid)
                    d = haversine(cur_lat, cur_lon, a.lat, a.lon)
                    if d < nearest_dist and day_hours + a.duration_hours <= DAILY_HOURS:
                        nearest, nearest_dist = a, d
                if nearest is None:
                    break
                day_items.append(nearest)
                remaining.remove(nearest.id)
                cur_lat, cur_lon = nearest.lat, nearest.lon
                day_hours += nearest.duration_hours

            # save TripItems with naive times (start 9:00)
            start_time = datetime.combine(current_date, datetime.min.time()) + timedelta(hours=9)
            t = start_time
            for idx, a in enumerate(day_items, start=1):
                st = t
                et = t + timedelta(hours=a.duration_hours)
                session.add(TripItem(trip_id=trip_id, day=day, order_index=idx,
                                     attraction_id=a.id,
                                     start_time=st.strftime("%H:%M"),
                                     end_time=et.strftime("%H:%M")))
                t = et
            session.commit()
            current_date += timedelta(days=1)

    finally:
        session.close()