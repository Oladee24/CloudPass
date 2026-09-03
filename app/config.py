import os


def _normalize_database_url(url):
    # Some hosts (Heroku, Render, etc.) hand out DATABASE_URL starting with
    # "postgres://", but modern SQLAlchemy only accepts "postgresql://".
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://"):]
    return url


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-before-deployment")
    SQLALCHEMY_DATABASE_URI = _normalize_database_url(
        os.getenv("DATABASE_URL", "sqlite:///cloudpass.db")
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JSON_SORT_KEYS = False

    # SMTP settings for password reset emails. If MAIL_SERVER / MAIL_USERNAME
    # are left blank (the default), CloudPass will not attempt to send real
    # email - it will just log the reset link to the console instead, which
    # is fine for local development.
    MAIL_SERVER = os.getenv("MAIL_SERVER", "")
    MAIL_PORT = int(os.getenv("MAIL_PORT", "587"))
    MAIL_USE_TLS = os.getenv("MAIL_USE_TLS", "true").lower() == "true"
    MAIL_USERNAME = os.getenv("MAIL_USERNAME", "")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD", "")
    MAIL_DEFAULT_SENDER = os.getenv("MAIL_DEFAULT_SENDER", "no-reply@cloudpass.local")


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    
    