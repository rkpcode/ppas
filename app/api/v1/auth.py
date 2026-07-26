from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.staff import Staff
from app.services.auth_service import verify_password, create_access_token
from app.schemas.auth import Token, UserCreate, UserResponse
from app.services.auth_service import verify_password, create_access_token, get_password_hash

router = APIRouter(prefix="/auth", tags=["Auth"])

@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(Staff).filter(Staff.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(Staff).filter(Staff.username == user_data.username).first()
    if existing_user:
        existing_user.name = user_data.name
        existing_user.hashed_password = get_password_hash(user_data.password)
        if user_data.role:
            existing_user.role = user_data.role
        db.commit()
        db.refresh(existing_user)
        return existing_user
    
    new_staff = Staff(
        name=user_data.name,
        username=user_data.username,
        hashed_password=get_password_hash(user_data.password),
        role=user_data.role or "Pharmacist",
        is_active=True
    )
    db.add(new_staff)
    db.commit()
    db.refresh(new_staff)
    return new_staff


from app.services.auth_service import get_current_user

@router.get("/me", response_model=UserResponse)
def get_me(current_user: Staff = Depends(get_current_user)):
    return current_user


