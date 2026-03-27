from sqlalchemy.orm import Session
from database import User, SessionLocal
from fastapi import APIRouter, Depends, Form, HTTPException
import bcrypt

router = APIRouter(prefix="/auth", tags=["auth"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_user(db: Session, email: str, password: str):
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    
    user = User(email=email, password=hashed)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def authenticate(db: Session, email: str, password: str):
    user = db.query(User).filter(User.email == email).first()
    
    if not user:
        return None
    
    if not bcrypt.checkpw(password.encode(), user.password.encode()):
        return None
    
    return user

@router.post("/signup")
def signup(email: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    user = create_user(db, email, password)
    return {"message": "User registered successfully", "user_id": user.id}

@router.post("/login")
def login(email: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    user = authenticate(db, email, password)
    
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    return {"message": "Login successful", "user_id": user.id}