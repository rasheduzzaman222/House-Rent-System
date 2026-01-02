from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.property import Property, RentPayment
from app.models.user import UserRole
from app.routers.auth import get_current_user


router = APIRouter()


def require_tenant(request: Request, db: Session):
    user = get_current_user(request, db)
    if not user or user.role != UserRole.TENANT:
        return None
    return user


@router.get("/properties/{property_id}")
async def property_detail(
    property_id: int, request: Request, db: Session = Depends(get_db)
):
    from app.main import templates

    prop = db.query(Property).filter(Property.id == property_id).first()
    if not prop:
        return RedirectResponse("/", status_code=303)

    current_user = get_current_user(request, db)

    return templates.TemplateResponse(
        "tenant/property_detail.html",
        {"request": request, "property": prop, "current_user": current_user},
    )


@router.get("/rent-history")
async def rent_history(request: Request, db: Session = Depends(get_db)):
    from app.main import templates

    tenant = require_tenant(request, db)
    if not tenant:
        return RedirectResponse("/login", status_code=303)

    payments = (
        db.query(RentPayment)
        .filter(RentPayment.tenant_id == tenant.id)
        .order_by(RentPayment.month.desc())
        .all()
    )

    return templates.TemplateResponse(
        "tenant/rent_history.html",
        {"request": request, "tenant": tenant, "payments": payments},
    )
