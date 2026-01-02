from app.db.session import engine, Base

# 👇 Import ALL models
from app.models.user import User
from app.models.property import Property, RentPayment


def init_db():
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully.")


if __name__ == "__main__":
    init_db()
