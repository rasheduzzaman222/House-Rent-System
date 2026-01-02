from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.property import Property
from app.models.user import User, UserRole
from app.routers.auth import get_current_user


router = APIRouter()


# -------------------- ADMIN GUARD --------------------

def require_admin(request: Request, db: Session):
    user = get_current_user(request, db)
    if not user or user.role != UserRole.ADMIN:
        return None
    return user


# -------------------- ADMIN DASHBOARD --------------------

@router.get("/dashboard")
async def admin_dashboard(
    request: Request,
    user_q: str | None = None,
    user_role: str | None = None,
    property_location: str | None = None,
    db: Session = Depends(get_db),
):
    from app.main import templates

    admin = require_admin(request, db)
    if not admin:
        return RedirectResponse("/login", status_code=303)

    # ---- USERS FILTER ----
    users_query = db.query(User)

    if user_q:
        pattern = f"%{user_q}%"
        users_query = users_query.filter(
            (User.full_name.ilike(pattern)) |
            (User.email.ilike(pattern))
        )

    if user_role:
        try:
            users_query = users_query.filter(User.role == UserRole(user_role))
        except ValueError:
            pass

    users = users_query.all()

    # ---- PROPERTIES FILTER ----
    properties_query = db.query(Property)

    if property_location:
        properties_query = properties_query.filter(
            Property.location.ilike(f"%{property_location}%")
        )

    properties = properties_query.all()

    return templates.TemplateResponse(
        "admin/dashboard.html",
        {
            "request": request,
            "admin": admin,
            "users": users,
            "properties": properties,
        },
    )


# -------------------- REMOVE PROPERTY --------------------

@router.post("/properties/{property_id}/remove")
async def remove_property(
    property_id: int,
    request: Request,
    db: Session = Depends(get_db),
):
    admin = require_admin(request, db)
    if not admin:
        return RedirectResponse("/login", status_code=303)

    prop = db.query(Property).filter(Property.id == property_id).first()
    if prop:
        db.delete(prop)
        db.commit()

    return RedirectResponse("/admin/dashboard", status_code=303)


# -------------------- REMOVE USER --------------------

@router.post("/users/{user_id}/remove")
async def remove_user(
    user_id: int,
    request: Request,
    db: Session = Depends(get_db),
):
    admin = require_admin(request, db)
    if not admin:
        return RedirectResponse("/login", status_code=303)

    user = db.query(User).filter(User.id == user_id).first()

    # ❗ SAFETY: do not allow deleting admin users
    if user and user.role != UserRole.ADMIN:
        db.delete(user)
        db.commit()

    return RedirectResponse("/admin/dashboard", status_code=303)
