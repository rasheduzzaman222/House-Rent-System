import enum
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Numeric,
    Enum,
    ForeignKey,
    DateTime,
    Date,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.session import Base


# -------------------- ENUMS --------------------

class PropertyType(str, enum.Enum):
    APARTMENT = "apartment"
    HOUSE = "house"


class AvailabilityStatus(str, enum.Enum):
    AVAILABLE = "available"
    RENTED = "rented"
    INACTIVE = "inactive"


class PaymentStatus(str, enum.Enum):
    PAID = "paid"
    PENDING = "pending"


# -------------------- PROPERTY MODEL --------------------

class Property(Base):
    __tablename__ = "properties"

    id = Column(Integer, primary_key=True, index=True)

    owner_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    title = Column(String(150), nullable=False)
    description = Column(Text, nullable=False)
    location = Column(String(255), nullable=False)

    rent_amount = Column(Numeric(10, 2), nullable=False)

    property_type = Column(
        Enum(PropertyType, name="property_type_enum"),
        nullable=False,
    )

    availability_status = Column(
        Enum(AvailabilityStatus, name="availability_status_enum"),
        nullable=False,
        default=AvailabilityStatus.AVAILABLE,
    )

    main_image_path = Column(String(255), nullable=True)

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

    # Relationships
    owner = relationship("User", backref="properties")
    rent_payments = relationship(
        "RentPayment",
        back_populates="property",
        cascade="all, delete-orphan",
    )


# -------------------- RENT PAYMENT MODEL --------------------

class RentPayment(Base):
    __tablename__ = "rent_payments"

    id = Column(Integer, primary_key=True, index=True)

    tenant_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    property_id = Column(
        Integer,
        ForeignKey("properties.id", ondelete="CASCADE"),
        nullable=False,
    )

    month = Column(Date, nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)

    status = Column(
        Enum(PaymentStatus, name="payment_status_enum"),
        nullable=False,
        default=PaymentStatus.PENDING,
    )

    paid_at = Column(DateTime(timezone=True), nullable=True)

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

    # Relationships
    property = relationship("Property", back_populates="rent_payments")
    tenant = relationship("User")
