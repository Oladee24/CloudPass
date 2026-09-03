import base64
import io
import secrets
import smtplib
from datetime import datetime, timedelta, timezone
from decimal import Decimal, ROUND_HALF_UP
from email.message import EmailMessage

import qrcode
from flask import current_app, url_for
from sqlalchemy.exc import IntegrityError

from app import db
from app.models import Booking, BusRoute, SavedRoute, User
from app.validators import ValidationError, normalize_email, normalize_text, positive_decimal, positive_int


MONEY = Decimal("0.01")


def money(value):
    return Decimal(value).quantize(MONEY, rounding=ROUND_HALF_UP)


def generate_booking_reference():
    safe_token = secrets.token_urlsafe(9).replace("-", "").replace("_", "")
    return f"CP-{safe_token[:10].upper()}"


def register_user(username, email, password):
    username = normalize_text(username, "username")
    email = normalize_email(email)
    password = str(password or "")
    if len(password) < 6:
        raise ValidationError("Password must be at least 6 characters long")

    user = User(username=username, email=email)
    user.set_password(password)
    db.session.add(user)
    try:
        db.session.commit()
    except IntegrityError as exc:
        db.session.rollback()
        raise ValidationError("A user with this username or email already exists") from exc
    return user


def authenticate_user(email, password):
    user = User.query.filter_by(email=normalize_email(email)).first()
    if not user or not user.check_password(str(password or "")):
        raise ValidationError("Invalid email or password")
    return user


def create_bus_route(departure, destination, price, available_seats):
    route = BusRoute(
        departure=normalize_text(departure, "departure").title(),
        destination=normalize_text(destination, "destination").title(),
        price=money(positive_decimal(price, "price")),
        available_seats=positive_int(available_seats, "available_seats"),
    )
    db.session.add(route)
    try:
        db.session.commit()
    except IntegrityError as exc:
        db.session.rollback()
        raise ValidationError("This bus route already exists") from exc
    return route


def book_route(user, route_id):
    route = BusRoute.query.filter_by(id=positive_int(route_id, "route_id")).with_for_update().one_or_none()
    if not route:
        raise ValidationError("Selected route was not found")
    if route.available_seats <= 0:
        raise ValidationError("No seats are available on this route")

    booking = Booking(
        booking_reference=generate_booking_reference(),
        user=user,
        route=route,
        price_paid=money(route.price),
        status="confirmed",
    )
    route.available_seats -= 1
    db.session.add(booking)

    try:
        db.session.commit()
    except IntegrityError as exc:
        db.session.rollback()
        raise ValidationError("Booking could not be completed. Please try again") from exc
    return booking


def toggle_saved_route(user, route_id):
    """Save a route for a user, or un-save it if it's already saved.

    Returns True if the route is now saved, False if it was just removed.
    """
    route_id = positive_int(route_id, "route_id")
    existing = SavedRoute.query.filter_by(user_id=user.id, route_id=route_id).first()

    if existing:
        db.session.delete(existing)
        db.session.commit()
        return False

    if not BusRoute.query.get(route_id):
        raise ValidationError("Selected route was not found")

    db.session.add(SavedRoute(user_id=user.id, route_id=route_id))
    try:
        db.session.commit()
    except IntegrityError as exc:
        db.session.rollback()
        raise ValidationError("This route is already saved") from exc
    return True


def get_saved_route_ids(user):
    if not user or not getattr(user, "is_authenticated", False):
        return set()
    rows = SavedRoute.query.filter_by(user_id=user.id).all()
    return {row.route_id for row in rows}


RESET_TOKEN_TTL_MINUTES = 30


def request_password_reset(email):
    """Start a password reset for the given email, if an account exists.

    Always succeeds silently for unknown emails so the caller can show the
    same generic message either way (this avoids revealing which emails
    are registered).
    """
    try:
        email = normalize_email(email)
    except ValidationError:
        return

    user = User.query.filter_by(email=email).first()
    if not user:
        return

    token = secrets.token_urlsafe(32)
    user.reset_token = token
    user.reset_token_expires_at = datetime.now(timezone.utc) + timedelta(minutes=RESET_TOKEN_TTL_MINUTES)
    db.session.commit()

    reset_link = url_for("main.reset_password", token=token, _external=True)
    _send_password_reset_email(user, reset_link)


def _send_password_reset_email(user, reset_link):
    message = EmailMessage()
    message["Subject"] = "Reset your CloudPass password"
    message["From"] = current_app.config.get("MAIL_DEFAULT_SENDER")
    message["To"] = user.email
    message.set_content(
        f"Hi {user.username},\n\n"
        f"Use this link to reset your CloudPass password. It expires in "
        f"{RESET_TOKEN_TTL_MINUTES} minutes:\n\n{reset_link}\n\n"
        "If you didn't request this, you can safely ignore this email."
    )

    host = current_app.config.get("MAIL_SERVER")
    username = current_app.config.get("MAIL_USERNAME")

    if not host or not username:
        # No SMTP configured - this is expected in local development.
        # Log the link instead so the reset flow still works end to end.
        current_app.logger.info("Password reset link for %s: %s", user.email, reset_link)
        print(f"[DEV] Password reset link for {user.email}: {reset_link}")
        return

    port = current_app.config.get("MAIL_PORT", 587)
    password = current_app.config.get("MAIL_PASSWORD")
    use_tls = current_app.config.get("MAIL_USE_TLS", True)

    with smtplib.SMTP(host, port) as server:
        if use_tls:
            server.starttls()
        server.login(username, password)
        server.send_message(message)


def reset_password_with_token(token, new_password, confirm_password):
    token = (token or "").strip()
    user = User.query.filter_by(reset_token=token).first() if token else None

    if not user or not user.reset_token_expires_at:
        raise ValidationError("This reset link is invalid or has expired")

    expires_at = user.reset_token_expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at < datetime.now(timezone.utc):
        raise ValidationError("This reset link is invalid or has expired")

    new_password = str(new_password or "")
    if len(new_password) < 6:
        raise ValidationError("Password must be at least 6 characters long")
    if new_password != str(confirm_password or ""):
        raise ValidationError("Passwords do not match")

    user.set_password(new_password)
    user.reset_token = None
    user.reset_token_expires_at = None
    db.session.commit()
    return user


def generate_ticket_qr_code(booking):
    """Return a base64 PNG data URI encoding this booking's key details."""
    payload = (
        "CloudPass Ticket\n"
        f"Reference: {booking.booking_reference}\n"
        f"Passenger: {booking.user.username}\n"
        f"Route: {booking.route.departure} -> {booking.route.destination}\n"
        f"Booked: {booking.booked_at.strftime('%Y-%m-%d %H:%M')} UTC"
    )
    qr = qrcode.QRCode(border=1, box_size=6)
    qr.add_data(payload)
    qr.make(fit=True)
    image = qr.make_image(fill_color="black", back_color="white")

    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


def cancel_booking(user, booking_reference):
    booking = Booking.query.filter_by(
        booking_reference=booking_reference,
        user_id=user.id,
    ).first()
    if not booking:
        raise ValidationError("Ticket not found")

    route = booking.route
    if route:
        route.available_seats += 1

    db.session.delete(booking)
    db.session.commit()


def delete_booking(user, booking_reference):
    booking = Booking.query.filter_by(
        booking_reference=booking_reference,
        user_id=user.id,
    ).first()
    if not booking:
        raise ValidationError("Ticket not found")

    route = booking.route
    if route:
        route.available_seats += 1

    db.session.delete(booking)
    db.session.commit()


DEFAULT_ROUTES = [
    ("Lagos", "Ibadan", 5000, 30),
    ("Lagos", "Abuja", 25500, 20),
    ("Abuja", "Kaduna", 65000, 25),
    ("Port Harcourt", "Enugu", 90000, 18),
    ("Enugu", "Owerri", 70000, 22),
    ("Kano", "Maiduguri", 12000, 15),
    ("Ibadan", "Oyo", 5000, 28),
    ("Lagos", "Abeokuta", 4000, 30),
    ("Abuja", "Jos", 20000, 20),
    ("Kaduna", "Zaria", 15000, 25),
    ("Port Harcourt", "Calabar", 80000, 18),
    ("Calabar", "Uyo", 60000, 22),
]


def seed_default_routes():
    """Insert any route from DEFAULT_ROUTES that isn't already in the database.

    Unlike the old version, this does not bail out just because the table
    already has rows - it checks each route individually, so adding new
    entries to DEFAULT_ROUTES later will actually create them, even after
    the app has already been run and seeded once.
    """
    created = 0
    for departure, destination, price, seats in DEFAULT_ROUTES:
        exists = BusRoute.query.filter_by(departure=departure, destination=destination).first()
        if exists:
            continue
        db.session.add(BusRoute(
            departure=departure,
            destination=destination,
            price=money(price),
            available_seats=seats,
        ))
        created += 1

    if created:
        db.session.commit()
    return created