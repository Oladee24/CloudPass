from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

from app import db
from app.models import Booking, BusRoute, SavedRoute
from app.services import (
    authenticate_user,
    book_route,
    delete_booking,
    generate_ticket_qr_code,
    get_saved_route_ids,
    register_user,
    request_password_reset,
    reset_password_with_token,
    seed_default_routes,
    toggle_saved_route,
)
from app.validators import ValidationError


main = Blueprint("main", __name__)

@main.before_request
def debug_request():
    print("REQUEST:", request.method, request.path)


@main.get("/health")
def health_check():
    return {
        "service": "CloudPass",
        "status": "ok",
    }

@main.get("/")
def home():
    route_count = BusRoute.query.count()
    return render_template("home.html", route_count=route_count)

@main.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("main.routes"))

    if request.method == "POST":
        try:
            user = register_user(
                request.form.get("username"),
                request.form.get("email"),
                request.form.get("password"),
            )
            login_user(user)
            flash("Account created. You can now book tickets.", "success")
            return redirect(url_for("main.routes"))
        except ValidationError as error:
            flash(str(error), "error")

    return render_template("register.html")


@main.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.routes"))

    if request.method == "POST":
        try:
            user = authenticate_user(request.form.get("email"), request.form.get("password"))
            login_user(user)
            flash("Welcome back.", "success")
            return redirect(url_for("main.routes"))
        except ValidationError as error:
            flash(str(error), "error")

    return render_template("login.html")


@main.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if current_user.is_authenticated:
        return redirect(url_for("main.routes"))

    if request.method == "POST":
        request_password_reset(request.form.get("email"))
        flash("If that email is registered, a reset link has been sent.", "success")
        return redirect(url_for("main.login"))

    return render_template("forgot_password.html")


@main.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for("main.routes"))

    if request.method == "POST":
        try:
            reset_password_with_token(
                token,
                request.form.get("password"),
                request.form.get("confirm_password"),
            )
            flash("Password updated. You can now log in.", "success")
            return redirect(url_for("main.login"))
        except ValidationError as error:
            flash(str(error), "error")

    return render_template("reset_password.html", token=token)


@main.post("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "success")
    return redirect(url_for("main.home"))


@main.get("/routes")
@login_required
def routes():
    seed_default_routes()

    query = (request.args.get("q") or "").strip()
    saved_only = request.args.get("saved") == "1"
    saved_ids = get_saved_route_ids(current_user)

    bus_routes_query = BusRoute.query
    if query:
        like = f"%{query}%"
        bus_routes_query = bus_routes_query.filter(
            db.or_(BusRoute.departure.ilike(like), BusRoute.destination.ilike(like))
        )
    if saved_only:
        bus_routes_query = bus_routes_query.filter(BusRoute.id.in_(saved_ids or {-1}))

    bus_routes = bus_routes_query.order_by(BusRoute.departure, BusRoute.destination).all()
    return render_template(
        "routes.html",
        routes=bus_routes,
        saved_ids=saved_ids,
        query=query,
        saved_only=saved_only,
    )


@main.post("/routes/<int:route_id>/save")
@login_required
def save_route(route_id):
    try:
        now_saved = toggle_saved_route(current_user, route_id)
        flash("Route added to your saved list." if now_saved else "Route removed from your saved list.", "success")
    except ValidationError as error:
        flash(str(error), "error")
    return redirect(request.referrer or url_for("main.routes"))


@main.route("/book/<int:route_id>", methods=["GET", "POST"])
@login_required
def book(route_id):
    route = BusRoute.query.get_or_404(route_id, description="Route not found")
    if request.method == "POST":
        try:
            booking = book_route(current_user, route.id)
            flash("Booking confirmed. Your digital ticket is saved.", "success")
            return redirect(url_for("main.ticket", booking_reference=booking.booking_reference))
        except ValidationError as error:
            flash(str(error), "error")

    return render_template("book.html", route=route)


@main.get("/my-bookings")
@login_required
def my_bookings():
    bookings = Booking.query.filter_by(user_id=current_user.id).order_by(Booking.booked_at.desc()).all()
    return render_template("my_bookings.html", bookings=bookings)


@main.get("/ticket/<booking_reference>")
@login_required
def ticket(booking_reference):
    booking = Booking.query.filter_by(
        booking_reference=booking_reference,
        user_id=current_user.id,
    ).first_or_404(description="Ticket not found")
    qr_code = generate_ticket_qr_code(booking)
    return render_template("ticket.html", booking=booking, qr_code=qr_code)


@main.post("/ticket/<booking_reference>/delete")
@login_required
def delete_ticket(booking_reference):
    try:
        delete_booking(current_user, booking_reference)
        flash("Ticket deleted.", "success")
    except ValidationError as error:
        flash(str(error), "error")
    return redirect(url_for("main.my_bookings"))


@main.get("/profile")
@login_required
def profile():
    booking_count = Booking.query.filter_by(user_id=current_user.id).count()
    saved_count = SavedRoute.query.filter_by(user_id=current_user.id).count()
    return render_template("profile.html", booking_count=booking_count, saved_count=saved_count)


@main.post("/profile/reset-password")
@login_required
def profile_reset_password():
    request_password_reset(current_user.email)
    flash("A password reset link has been sent to your email.", "success")
    return redirect(url_for("main.profile"))


@main.cli.command("seed-routes")
def seed_routes_command():
    created = seed_default_routes()
    print(f"Seeded {created} route(s).")