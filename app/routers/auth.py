from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User, UserRole
from app.core.security import hash_password, verify_password


router = APIRouter(tags=["auth"])


# -------------------- HELPERS --------------------

def get_current_user(request: Request, db: Session) -> User | None:
    user_id = request.session.get("user_id")
    if not user_id:
        return None
    return db.query(User).filter(User.id == user_id).first()


# -------------------- REGISTER --------------------

@router.get("/register")
async def register_form(request: Request, db: Session = Depends(get_db)):
    # import here to avoid circular import
    from app.main import templates

    flash = request.session.pop("flash", None)
    current_user = get_current_user(request, db)

    return templates.TemplateResponse(
        "auth/register.html",
        {
            "request": request,
            "flash": flash,
            "current_user": current_user,
        },
    )


@router.post("/register")
async def register(
    request: Request,
    full_name: str = Form(...),
    email: str = Form(...),
    phone: str = Form(...),
    password: str = Form(...),
    role: str = Form("tenant"),
    db: Session = Depends(get_db),
):
    # -------------------- BASIC VALIDATION --------------------
    full_name = full_name.strip()
    email = email.lower().strip()
    phone = phone.strip()

    if len(password) < 6 or len(password) > 64:
        request.session["flash"] = {
            "type": "danger",
            "message": "Password must be between 6 and 64 characters.",
        }
        return RedirectResponse("/register", status_code=303)

    # -------------------- EXISTING USER CHECK --------------------
    if db.query(User).filter(User.email == email).first():
        request.session["flash"] = {
            "type": "danger",
            "message": "Email already registered. Please log in.",
        }
        return RedirectResponse("/register", status_code=303)

    # -------------------- SAFE ENUM CONVERSION --------------------
    try:
        user_role = UserRole(role)
    except ValueError:
        user_role = UserRole.TENANT

    # -------------------- CREATE USER --------------------
    try:
        user = User(
            full_name=full_name,
            email=email,
            phone=phone,
            hashed_password=hash_password(password),
            role=user_role,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    except Exception:
        db.rollback()
        request.session["flash"] = {
            "type": "danger",
            "message": "Registration failed. Please try again.",
        }
        return RedirectResponse("/register", status_code=303)

    # -------------------- SESSION --------------------
    request.session["user_id"] = user.id
    request.session["role"] = user.role.value
    request.session["flash"] = {
        "type": "success",
        "message": "Registration successful. You are now logged in.",
    }

    return RedirectResponse("/", status_code=303)


# -------------------- LOGIN --------------------

@router.get("/login")
async def login_form(request: Request, db: Session = Depends(get_db)):
    from app.main import templates

    flash = request.session.pop("flash", None)
    current_user = get_current_user(request, db)

    return templates.TemplateResponse(
        "auth/login.html",
        {
            "request": request,
            "flash": flash,
            "current_user": current_user,
        },
    )


@router.post("/login")
async def login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    email = email.lower().strip()

    user = db.query(User).filter(User.email == email).first()

    if not user or not verify_password(password, user.hashed_password):
        request.session["flash"] = {
            "type": "danger",
            "message": "Invalid email or password.",
        }
        return RedirectResponse("/login", status_code=303)

    request.session["user_id"] = user.id
    request.session["role"] = user.role.value
    request.session["flash"] = {
        "type": "success",
        "message": "Logged in successfully.",
    }

    return RedirectResponse("/", status_code=303)


# -------------------- LOGOUT --------------------

@router.get("/logout")
async def logout(request: Request):
    request.session.clear()
    request.session["flash"] = {
        "type": "info",
        "message": "You have been logged out.",
    }
    return RedirectResponse("/", status_code=303)
