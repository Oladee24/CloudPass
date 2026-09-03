from datetime import datetime, timezone

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from app import db


def utc_now():
    return datetime.now(timezone.utc)


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=utc_now, nullable=False)
    reset_token = db.Column(db.String(64), unique=True, nullable=True, index=True)
    reset_token_expires_at = db.Column(db.DateTime, nullable=True)

    bookings = db.relationship("Booking", back_populates="user", cascade="all, delete-orphan")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"<User {self.email}>"


class BusRoute(db.Model):
    __tablename__ = "bus_routes"

    id = db.Column(db.Integer, primary_key=True)
    departure = db.Column(db.String(100), nullable=False)
    destination = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    available_seats = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=utc_now, nullable=False)

    bookings = db.relationship("Booking", back_populates="route")

    __table_args__ = (
        db.UniqueConstraint("departure", "destination", name="uq_bus_route_departure_destination"),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "departure": self.departure,
            "destination": self.destination,
            "price": float(self.price),
            "available_seats": self.available_seats,
        }

    def __repr__(self):
        return f"<BusRoute {self.departure} to {self.destination}>"


class SavedRoute(db.Model):
    __tablename__ = "saved_routes"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    route_id = db.Column(db.Integer, db.ForeignKey("bus_routes.id"), nullable=False)
    saved_at = db.Column(db.DateTime, default=utc_now, nullable=False)

    user = db.relationship("User")
    route = db.relationship("BusRoute")

    __table_args__ = (
        db.UniqueConstraint("user_id", "route_id", name="uq_saved_route_user_route"),
    )

    def __repr__(self):
        return f"<SavedRoute user={self.user_id} route={self.route_id}>"


class Booking(db.Model):
    __tablename__ = "bookings"

    id = db.Column(db.Integer, primary_key=True)
    booking_reference = db.Column(db.String(24), unique=True, nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    route_id = db.Column(db.Integer, db.ForeignKey("bus_routes.id"), nullable=False)
    price_paid = db.Column(db.Numeric(10, 2), nullable=False)
    status = db.Column(db.String(20), default="confirmed", nullable=False)
    booked_at = db.Column(db.DateTime, default=utc_now, nullable=False)

    user = db.relationship("User", back_populates="bookings")
    route = db.relationship("BusRoute", back_populates="bookings")

    @property
    def ticket_id(self):
        return f"TICKET-{self.id:06d}"

    def to_dict(self):
        return {
            "id": self.id,
            "ticket_id": self.ticket_id,
            "booking_reference": self.booking_reference,
            "passenger_name": self.user.username,
            "route": self.route.to_dict(),
            "price_paid": float(self.price_paid),
            "status": self.status,
            "booked_at": self.booked_at.isoformat(),
        }

    def __repr__(self):
        return f"<Booking {self.booking_reference}>"