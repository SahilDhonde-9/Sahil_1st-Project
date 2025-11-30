from __future__ import annotations
from sqlalchemy import create_engine, Column, Integer, String, Float, Date, ForeignKey, Boolean
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from sqlalchemy.orm import Mapped, mapped_column
import os
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

DB_PATH = os.path.join(os.path.dirname(__file__), "trip.db")
engine = create_engine(f"sqlite:///{DB_PATH}", echo=False, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
Base = declarative_base()

class User(Base, UserMixin):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(128), nullable=False)

    trips: Mapped[list["Trip"]] = relationship("Trip", back_populates="user")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_id(self):
        return str(self.id)

class Trip(Base):
    __tablename__ = "trips"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(80))
    city: Mapped[str] = mapped_column(String(40))
    start_date: Mapped[str] = mapped_column(String(20))  # store as string for simplicity
    days: Mapped[int] = mapped_column(Integer)
    interests: Mapped[str] = mapped_column(String(120))  # comma separated
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    budget: Mapped[float] = mapped_column(Float, nullable=True, default=0.0)

    user: Mapped["User"] = relationship("User", back_populates="trips")
    packing_items: Mapped[list["PackingItem"]] = relationship("PackingItem", back_populates="trip", cascade="all, delete-orphan")

class PackingItem(Base):
    __tablename__ = "packing_items"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    trip_id: Mapped[int] = mapped_column(Integer, ForeignKey("trips.id"))
    item_name: Mapped[str] = mapped_column(String(120), nullable=False)
    is_packed: Mapped[bool] = mapped_column(Boolean, default=False)

    trip: Mapped["Trip"] = relationship("Trip", back_populates="packing_items")

class Attraction(Base):
    __tablename__ = "attractions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    city: Mapped[str] = mapped_column(String(40))
    name: Mapped[str] = mapped_column(String(120))
    category: Mapped[str] = mapped_column(String(40))    # one primary category
    duration_hours: Mapped[float] = mapped_column(Float) # typical time spent
    lat: Mapped[float] = mapped_column(Float)
    lon: Mapped[float] = mapped_column(Float)
    image_path: Mapped[str] = mapped_column(String(200), nullable=True)   # 👈 नवीन कॉलम

class TripItem(Base):
    __tablename__ = "trip_items"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    trip_id: Mapped[int] = mapped_column(Integer)
    day: Mapped[int] = mapped_column(Integer)
    order_index: Mapped[int] = mapped_column(Integer)
    attraction_id: Mapped[int] = mapped_column(Integer)
    start_time: Mapped[str] = mapped_column(String(10))
    end_time: Mapped[str] = mapped_column(String(10))
