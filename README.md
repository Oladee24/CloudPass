# CloudPass

CloudPass is a cloud-ready bus ticket and pass management system built with Python and Flask.

The system lets a passenger register, log in, view available bus routes, book a ticket, and later return to view the saved digital ticket. The backend protects the ticket price by reading the official price from the database during booking instead of trusting any price sent from the browser.

## Internship Task

Task 3: Cloud-Based Bus Pass System

- Develop an online ticket booking system hosted on the cloud.
- Ensure prevention of ticket loss, theft, and incorrect pricing.
- Design the system to handle high traffic by dynamically provisioning servers.
- Focus on scalability and reliability improvements over traditional booking sites.
- Test and deploy the system to provide a seamless booking experience for users.

## What CloudPass Does In Simple Terms

CloudPass is like the backend and first web interface for a transport company's online ticket system.

Instead of giving passengers only a paper ticket, the system stores every booking in a database. If the user logs in later, they can still see their ticket. This helps prevent ticket loss.

Instead of allowing the browser to decide the fare, the system stores official route prices in the database. When a passenger books, the backend checks the selected route and copies the official price into the booking. This prevents incorrect pricing.

Instead of depending on one server forever, the project includes Docker and Kubernetes files. In a cloud environment, more application copies can be started when traffic is high.

## Tools And What They Do

| Tool | Purpose |
| --- | --- |
| Python | Main programming language |
| Flask | Web framework used to build pages and routes |
| Flask-SQLAlchemy | Connects Python classes to database tables |
| Flask-Login | Handles login sessions and protected pages |
| Werkzeug password hashing | Stores passwords securely as hashes |
| SQLite | Simple local database for development |
| PostgreSQL | Production-style cloud database |
| python-dotenv | Loads environment variables from `.env` |
| Gunicorn | Production server used inside Docker/cloud hosting |
| Docker | Packages the application so it runs consistently |
| Docker Compose | Runs the app and database together locally |
| Kubernetes | A manifest (cloud/kubernetes/cloudpass-api.yaml) is included, describing how CloudPass could run as multiple replicas on a cluster |
| Horizontal Pod Autoscaler | Dynamically increases app pods during high traffic |
| unittest | Tests the important booking behavior |

## Folder And File Explanation

```text
CloudPass/
├── app/
│   ├── static/css/styles.css
│   ├── templates/
│   ├── __init__.py
│   ├── config.py
│   ├── models.py
│   ├── routes.py
│   ├── services.py
│   └── validators.py
├── cloud/kubernetes/cloudpass-api.yaml
├── tests/test_cloudpass_app.py
├── .dockerignore
├── .env.example
├── .gitignore
├── Dockerfile
├── docker-compose.yml
├── README.md
├── requirements.txt
└── run.py
```

### `run.py`

Starts the application. It creates the database tables and seeds sample routes so the app has routes to show immediately.

### `app/__init__.py`

Creates the Flask application, connects the database, sets up login management, registers the routes, and handles basic errors.

### `app/config.py`

Stores settings such as `SECRET_KEY` and `DATABASE_URL`. Locally, the app can fall back to SQLite. In the cloud, it should use PostgreSQL.

### `app/models.py`

Defines the database tables:

- `User`: a registered passenger.
- `BusRoute`: a travel route with departure, destination, price, and available seats.
- `Booking`: a saved digital ticket connected to a user and route.

### `app/routes.py`

Defines the web pages:

- `/`: homepage
- `/register`: create account
- `/login`: log in
- `/logout`: log out
- `/routes`: view available routes
- `/book/<route_id>`: book a route
- `/my-bookings`: view saved tickets
- `/ticket/<booking_reference>`: view one digital ticket
- `/health`: health check for deployment monitoring

### `app/services.py`

Contains the main business logic:

- register users
- authenticate login
- create bus routes
- seed sample routes
- create bookings
- reduce available seats
- copy the official database price into the booking

### `app/validators.py`

Checks user input, such as valid email addresses, non-empty text, positive seat numbers, and positive prices.

### `app/templates/`

Contains the HTML pages shown in the browser.

### `app/static/css/styles.css`

Contains the visual styling for the pages.

### `tests/test_cloudpass_app.py`

Tests the most important behavior:

- homepage loads
- user registration works
- routes require login
- booking uses database price, not browser-submitted price
- saved tickets can be viewed later
- overbooking is rejected

### `Dockerfile`

Packages the Flask app into a container for deployment.

### `docker-compose.yml`

Runs CloudPass and PostgreSQL together locally.

### `cloud/kubernetes/cloudpass-api.yaml`

Shows how CloudPass can run in Kubernetes with multiple replicas and autoscaling.

## Running code Locally

Open PowerShell and go into the project folder:

```powershell
cd C:\Users\oladu\Downloads\CloudPass
```

Create and activate a virtual environment:

```powershell
py -m venv venv
.\venv\Scripts\Activate.ps1
```

Install the required packages:

```powershell
pip install -r requirements.txt
```

Start the app:

```powershell
python run.py
```

Open this in your browser:

```text
http://127.0.0.1:5000
```

Health check:

```text
http://127.0.0.1:5000/health
```

## Application steps

1. Open `http://127.0.0.1:5000`.
2. Click `Register`.
3. Create a user account.
4. After registering, you will be sent to the routes page.
5. Pick a route and click `Book`.
6. Confirm the booking.
7. The app shows your digital ticket, you also get a QR code
8. Click `My Bookings` any time after login to recover/view saved tickets.
9. Tickets can also be saved and deleted

## How To Run Tests

```powershell
python -m unittest discover
```

## Docker Run

```powershell
docker compose up --build
```

Then open:

```text
http://127.0.0.1:8000
```

## Explanation

CloudPass is a cloud-based bus ticket booking system. It allows passengers to register, log in, view available routes, book tickets, and retrieve their digital tickets later. The project prevents ticket loss by storing bookings in a database. It prevents incorrect pricing by calculating the fare from the official route price stored in the database, not from user-submitted browser data. It improves reliability and scalability by supporting Docker containerization and Kubernetes autoscaling, meaning multiple application instances can run behind a load balancer when traffic increases.

## Development Roadmap Used For Project

- Phase 1: Planning and system design
- Phase 2: Local Flask application foundation
- Phase 3: Database models and seeded routes
- Phase 4: Authentication
- Phase 5: Booking and digital ticket system
- Phase 6: Testing and hardening
- Phase 7: Docker
- Phase 8: Cloud deployment
- Phase 9: Kubernetes and autoscaling
- Phase 10: Load and reliability testing
- Phase 11: Final documentation
