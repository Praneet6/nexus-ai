"""
Auth routes — JWT login / register, plus shared auth dependencies.
"""
import logging
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.config import get_settings
from app.models.models import Customer, UserRole
from app.db.postgres import get_db

router = APIRouter(prefix="/auth", tags=["auth"])
logger = logging.getLogger(__name__)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


class RegisterRequest(BaseModel):
    email: str
    password: str
    name: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    customer_id: str
    name: str
    role: str  # "user" | "admin" — lets the frontend gate the Admin link


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_token(customer_id: str, email: str, role: str = "user") -> str:
    settings = get_settings()
    expire = datetime.utcnow() + timedelta(minutes=settings.jwt_expire_minutes)
    payload = {"sub": customer_id, "email": email, "role": role, "exp": expire}
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


# ── Shared auth dependencies ──────────────────────────────────────────────────

async def get_current_customer(token: str = Depends(oauth2_scheme)) -> dict:
    """Decode JWT and return basic customer info. Raises 401 on bad token."""
    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        return {
            "id": payload["sub"],
            "email": payload["email"],
            "role": payload.get("role", "user"),
        }
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")


async def require_admin(current: dict = Depends(get_current_customer)) -> dict:
    """
    FastAPI dependency — allows only customers with role == 'admin'.
    Raises 403 Forbidden for any other authenticated user.
    Usage:
        @router.get("/admin/something")
        async def admin_endpoint(admin=Depends(require_admin)):
            ...
    """
    if current.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required. Your account does not have this permission.",
        )
    return current


# ── DB helper ─────────────────────────────────────────────────────────────────

async def _get_db_dep():
    settings = get_settings()
    async for session in get_db(settings.database_url):
        yield session


# ── Routes ────────────────────────────────────────────────────────────────────

@router.post("/register", response_model=LoginResponse)
async def register(req: RegisterRequest, db: AsyncSession = Depends(_get_db_dep)):
    existing = await db.execute(select(Customer).where(Customer.email == req.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")

    customer = Customer(
        email=req.email,
        name=req.name,
        hashed_password=hash_password(req.password),
        role=UserRole.user,
    )
    db.add(customer)
    await db.commit()
    await db.refresh(customer)

    token = create_token(customer.id, customer.email, customer.role.value)
    return LoginResponse(
        access_token=token,
        customer_id=customer.id,
        name=customer.name,
        role=customer.role.value,
    )


@router.post("/login", response_model=LoginResponse)
async def login(form: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(_get_db_dep)):
    result = await db.execute(select(Customer).where(Customer.email == form.username))
    customer = result.scalar_one_or_none()

    if not customer or not verify_password(form.password, customer.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = create_token(customer.id, customer.email, customer.role.value)
    return LoginResponse(
        access_token=token,
        customer_id=customer.id,
        name=customer.name,
        role=customer.role.value,
    )
