from datetime import date

from fastapi import APIRouter, Depends, File, Form, Request, UploadFile
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
import os

from app.db.session import get_db
from app.models.property import AvailabilityStatus, Property, PropertyType, PaymentStatus, RentPayment
from app.models.user import UserRole
from app.routers.auth import get_current_user


router = APIRouter()


UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "static", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)


def require_owner(request: Request, db: Session):
    user = get_current_user(request, db)
    if not user or user.role != UserRole.OWNER:
        return None
    return user


@router.get("/dashboard")
async def owner_dashboard(request: Request, db: Session = Depends(get_db)):
    from app.main import templates

    owner = require_owner(request, db)
    if not owner:
        return RedirectResponse("/login", status_code=303)

    properties = db.query(Property).filter(Property.owner_id == owner.id).all()

    return templates.TemplateResponse(
        "owner/dashboard.html",
        {"request": request, "owner": owner, "properties": properties},
    )


@router.get("/properties/new")
async def new_property_form(request: Request, db: Session = Depends(get_db)):
    from app.main import templates

    owner = require_owner(request, db)
    if not owner:
        return RedirectResponse("/login", status_code=303)

    return templates.TemplateResponse(
        "owner/property_form.html",
        {"request": request, "property": None},
    )


@router.post("/properties/new")
async def create_property(
    request: Request,
    title: str = Form(...),
    description: str = Form(...),
    location: str = Form(...),
    rent_amount: float = Form(...),
    property_type: str = Form(...),
    image: UploadFile | None = File(None),
    db: Session = Depends(get_db),
):
    owner = require_owner(request, db)
    if not owner:
        return RedirectResponse("/login", status_code=303)

    image_path = None
    if image and image.filename:
        filename = f"{owner.id}_{image.filename}"
        save_path = os.path.join(UPLOAD_DIR, filename)
        with open(save_path, "wb") as f:
            f.write(await image.read())
        image_path = f"/static/uploads/{filename}"

    prop = Property(
        owner_id=owner.id,
        title=title,
        description=description,
        location=location,
        rent_amount=rent_amount,
        property_type=PropertyType(property_type),
        main_image_path=image_path,
    )
    db.add(prop)
    db.commit()

    return RedirectResponse("/owner/dashboard", status_code=303)


@router.get("/properties/{property_id}/edit")
async def edit_property_form(
    property_id: int, request: Request, db: Session = Depends(get_db)
):
    from app.main import templates

    owner = require_owner(request, db)
    if not owner:
        return RedirectResponse("/login", status_code=303)

    prop = (
        db.query(Property)
        .filter(Property.id == property_id, Property.owner_id == owner.id)
        .first()
    )
    if not prop:
        return RedirectResponse("/owner/dashboard", status_code=303)

    return templates.TemplateResponse(
        "owner/property_form.html",
        {"request": request, "property": prop},
    )


@router.post("/properties/{property_id}/edit")
async def update_property(
    property_id: int,
    request: Request,
    title: str = Form(...),
    description: str = Form(...),
    location: str = Form(...),
    rent_amount: float = Form(...),
    property_type: str = Form(...),
    availability_status: str = Form("available"),
    image: UploadFile | None = File(None),
    db: Session = Depends(get_db),
):
    owner = require_owner(request, db)
    if not owner:
        return RedirectResponse("/login", status_code=303)

    prop = (
        db.query(Property)
        .filter(Property.id == property_id, Property.owner_id == owner.id)
        .first()
    )
    if not prop:
        return RedirectResponse("/owner/dashboard", status_code=303)

    prop.title = title
    prop.description = description
    prop.location = location
    prop.rent_amount = rent_amount
    prop.property_type = PropertyType(property_type)
    prop.availability_status = AvailabilityStatus(availability_status)

    if image and image.filename:
        filename = f"{owner.id}_{image.filename}"
        save_path = os.path.join(UPLOAD_DIR, filename)
        with open(save_path, "wb") as f:
            f.write(await image.read())
        prop.main_image_path = f"/static/uploads/{filename}"

    db.commit()

    return RedirectResponse("/owner/dashboard", status_code=303)


@router.post("/properties/{property_id}/delete")
async def delete_property(
    property_id: int, request: Request, db: Session = Depends(get_db)
):
    owner = require_owner(request, db)
    if not owner:
        return RedirectResponse("/login", status_code=303)

    prop = (
        db.query(Property)
        .filter(Property.id == property_id, Property.owner_id == owner.id)
        .first()
    )
    if prop:
        db.delete(prop)
        db.commit()

    return RedirectResponse("/owner/dashboard", status_code=303)


@router.get("/properties/{property_id}/payments")
async def view_payments(property_id: int, request: Request, db: Session = Depends(get_db)):
    from app.main import templates

    owner = require_owner(request, db)
    if not owner:
        return RedirectResponse("/login", status_code=303)

    prop = (
        db.query(Property)
        .filter(Property.id == property_id, Property.owner_id == owner.id)
        .first()
    )
    if not prop:
        return RedirectResponse("/owner/dashboard", status_code=303)

    payments = (
        db.query(RentPayment)
        .filter(RentPayment.property_id == property_id)
        .order_by(RentPayment.month.desc())
        .all()
    )

    return templates.TemplateResponse(
        "owner/payments.html",
        {"request": request, "owner": owner, "property": prop, "payments": payments},
    )


@router.post("/properties/{property_id}/payments")
async def add_or_update_payment(
    property_id: int,
    request: Request,
    tenant_id: int = Form(...),
    month: str = Form(...),  # Expect YYYY-MM-01
    amount: float = Form(...),
    status: str = Form("pending"),
    db: Session = Depends(get_db),
):
    owner = require_owner(request, db)
    if not owner:
        return RedirectResponse("/login", status_code=303)

    pay_month = date.fromisoformat(month)

    payment = (
        db.query(RentPayment)
        .filter(
            RentPayment.property_id == property_id,
            RentPayment.tenant_id == tenant_id,
            RentPayment.month == pay_month,
        )
        .first()
    )

    if payment:
        payment.amount = amount
        payment.status = PaymentStatus(status)
    else:
        payment = RentPayment(
            tenant_id=tenant_id,
            property_id=property_id,
            month=pay_month,
            amount=amount,
            status=PaymentStatus(status),
        )
        db.add(payment)

    db.commit()

    return RedirectResponse("/owner/dashboard", status_code=303)
