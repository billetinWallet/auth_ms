from datetime import timedelta, datetime
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from fastapi import status
from app.database import SessionLocal
from app.models import Users
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from jose import jwt, JWTError
from app import database


router = APIRouter(
    prefix="/auth",
    tags=["auth"]
)

sk = "3f2d6a6bc52e789ce88dac6f183291837bd0ea53099d34b81a4bf90c47e897919630cdfb935c2abe016ee4753b5764300c4294dc5b655fe67cff7fe2fc659dff"
algo = "HS256"

bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_bearer = OAuth2PasswordBearer(tokenUrl="auth/token")

class CreateUserRequest(BaseModel):
    document_number: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str


get_db = database.get_db

@router.get("/users", status_code=status.HTTP_200_OK)
async def get_users(db: Session = Depends(get_db)):
    users = db.query(Users).all()
    return users

@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_user(request: CreateUserRequest, db: Session = Depends(get_db)):
    user_model = Users(document_number=request.document_number,
                              hashed_password=bcrypt_context.hash(request.password))
    db.add(user_model)
    db.commit()
    return user_model.document_number

@router.post("/token", response_model=Token)
async def get_token(form_data: Annotated[OAuth2PasswordRequestForm, Depends()], db: Session = Depends(get_db)):
    user = authenticate_user(form_data.username, form_data.password, db)
    if not user: raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Validation failed")
    token = create_access_token(user.id, timedelta(minutes=10))
    return {"access_token":token, "token_type": "bearer"}

def authenticate_user(document_number: str, password: str, db):
    user = db.query(Users).filter(Users.document_number==document_number).first()
    if not user: return False
    if not bcrypt_context.verify(password, user.hashed_password): return False
    return user

def create_access_token(user_id: int, expires_delta: timedelta):
    encode = {"id": user_id}
    expires = datetime.utcnow() + expires_delta
    encode.update({"exp": expires})
    return jwt.encode(encode, sk, algorithm=algo)

def get_current_user(token: Annotated[str, Depends(oauth2_bearer)]):
    try:
        payload = jwt.decode(token, sk, algorithms=[algo])
        user_id: int = payload.get("id")
        if user_id is None: raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Validation failed")
        return {"id": user_id}
    except JWTError: raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Validation failed")