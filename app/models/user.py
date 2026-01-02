import enum
from sqlalchemy import Column, Integer, String, Enum, DateTime
from sqlalchemy.sql import func

from app.db.session import Base


# -------------------- ENUM --------------------

class UserRole(str, enum.Enum):
    TENANT = "tenant"
    OWNER = "owner"
    ADMIN = "admin"


# -------------------- USER MODEL --------------------

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)

    full_name = Column(String(100), nullable=False)

    email = Column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
    )

    phone = Column(String(20), nullable=False)

    # store ONLY hashed password (never plain text)
    hashed_password = Column(String(255), nullable=False)

    role = Column(
        Enum(UserRole, name="user_role_enum"),
        nullable=False,
        server_default=UserRole.TENANT.value,
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # -------------------- SAFE SERIALIZATION --------------------
    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email} role={self.role}>"
