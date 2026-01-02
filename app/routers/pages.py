from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.property import Property, PropertyType
from app.models.user import User
from app.routers.auth import get_current_user


router = APIRouter()


@router.get("/")
async def home(
    request: Request,
    location: str | None = None,
    min_rent: float | None = None,
    max_rent: float | None = None,
    property_type: str | None = None,
    db: Session = Depends(get_db),
):
    from app.main import templates

    query = db.query(Property)

    if location:
        query = query.filter(Property.location.ilike(f"%{location}%"))
    if min_rent is not None:
        query = query.filter(Property.rent_amount >= min_rent)
    if max_rent is not None:
        query = query.filter(Property.rent_amount <= max_rent)
    if property_type:
        query = query.filter(Property.property_type == PropertyType(property_type))

    properties = query.order_by(Property.created_at.desc()).all()

    current_user = get_current_user(request, db)
    flash = request.session.pop("flash", None)

    return templates.TemplateResponse(
        "home.html",
        {
            "request": request,
            "properties": properties,
            "current_user": current_user,
            "flash": flash,
        },
    )


@router.get("/profile")
async def profile(request: Request, db: Session = Depends(get_db)):
    from app.main import templates

    user = get_current_user(request, db)
    if not user:
        return RedirectResponse("/login", status_code=303)

    flash = request.session.pop("flash", None)

    return templates.TemplateResponse(
        "profile.html", {"request": request, "user": user, "flash": flash}
    )


@router.post("/profile")
async def update_profile(
    request: Request,
    full_name: str = Form(...),
    phone: str = Form(...),
    db: Session = Depends(get_db),
):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse("/login", status_code=303)

    user.full_name = full_name
    user.phone = phone
    db.commit()
    db.refresh(user)

    request.session["flash"] = {
        "type": "success",
        "message": "Profile updated successfully.",
    }

    return RedirectResponse("/profile", status_code=303)
