from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from pathlib import Path

from app.core.config import settings
from app.routers import auth, pages, owners, tenants, admin


# -------------------- APP INIT --------------------

app = FastAPI(title="House Rent Service System")


# -------------------- BASE DIR --------------------

BASE_DIR = Path(__file__).resolve().parent.parent


# -------------------- SESSION MIDDLEWARE --------------------

app.add_middleware(
    SessionMiddleware,
    secret_key=settings.SECRET_KEY,
    session_cookie=settings.SESSION_COOKIE_NAME,
    same_site="lax",
    https_only=False,   # ✅ True only when using HTTPS
)


# -------------------- STATIC & TEMPLATES --------------------

static_dir = BASE_DIR / "static"
templates_dir = BASE_DIR / "templates"

app.mount("/static", StaticFiles(directory=static_dir), name="static")
templates = Jinja2Templates(directory=templates_dir)


# -------------------- ROUTERS --------------------

app.include_router(auth.router)
app.include_router(pages.router)
app.include_router(owners.router, prefix="/owner", tags=["owner"])
app.include_router(tenants.router, prefix="/tenant", tags=["tenant"])
app.include_router(admin.router, prefix="/admin", tags=["admin"])


# -------------------- HEALTH CHECK --------------------

@app.get("/health", tags=["health"])
async def health_check():
    return {"status": "ok"}
