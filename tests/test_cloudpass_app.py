import unittest

from app import create_app, db
from app.models import Booking, BusRoute, User
from app.services import seed_default_routes


class CloudPassAppTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app("app.config.TestConfig")
        self.client = self.app.test_client()
        self.context = self.app.app_context()
        self.context.push()
        db.create_all()
        seed_default_routes()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.context.pop()

    def register_and_login(self):
        return self.client.post("/register", data={
            "username": "Oladunni",
            "email": "oladunni@example.com",
            "password": "secret123",
        }, follow_redirects=True)

    def test_homepage_and_health_check_load(self):
        home = self.client.get("/")
        health = self.client.get("/health")

        self.assertEqual(home.status_code, 200)
        self.assertIn(b"CloudPass", home.data)
        self.assertEqual(health.status_code, 200)
        self.assertEqual(health.get_json()["service"], "CloudPass")

    def test_user_can_register_and_view_routes(self):
        response = self.register_and_login()

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Choose a bus route", response.data)
        self.assertEqual(User.query.count(), 1)

    def test_routes_page_requires_login(self):
        response = self.client.get("/routes")

        self.assertEqual(response.status_code, 302)
        self.assertIn("/login", response.headers["Location"])

    def test_booking_uses_database_price_not_submitted_price(self):
        self.register_and_login()
        route = BusRoute.query.filter_by(departure="Lagos", destination="Ibadan").first()

        response = self.client.post(
            f"/book/{route.id}",
            data={"price": "1"},
            follow_redirects=True,
        )
        booking = Booking.query.first()

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Digital Ticket", response.data)
        self.assertEqual(float(booking.price_paid), 4500.0)
        self.assertEqual(route.available_seats, 29)

    def test_user_can_view_saved_ticket_later(self):
        self.register_and_login()
        route = BusRoute.query.first()
        self.client.post(f"/book/{route.id}", follow_redirects=True)
        booking = Booking.query.first()

        response = self.client.get(f"/ticket/{booking.booking_reference}")

        self.assertEqual(response.status_code, 200)
        self.assertIn(booking.booking_reference.encode("utf-8"), response.data)
        self.assertIn(b"TICKET-", response.data)

    def test_overbooking_is_rejected(self):
        self.register_and_login()
        route = BusRoute.query.first()
        route.available_seats = 0
        db.session.commit()

        response = self.client.post(f"/book/{route.id}", follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"No seats are available", response.data)
        self.assertEqual(Booking.query.count(), 0)


if __name__ == "__main__":
    unittest.main()
