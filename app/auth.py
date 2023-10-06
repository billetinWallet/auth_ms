from datetime import timedelta, datetime
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from starlette import status
from app.database import SessionLocal
from app.models import Users
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from jose import jwt, JWTError


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

def get_db():
    db = SessionLocal()
    try: yield db
    finally: db.close()

db_dependency = Annotated[Session, Depends(get_db)]

@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_user(db: db_dependency, request: CreateUserRequest):
    user_model = Users(document_number=request.document_number,
                              hashed_password=bcrypt_context.hash(request.password))
    db.add(user_model)
    db.commit()

@router.post("/token", response_model=Token)
async def get_token(form_data: Annotated[OAuth2PasswordRequestForm, Depends()], db: db_dependency):
    user = authenticate_user(form_data.username, form_data.password, db)
    if not user: raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Validation failed")
    token = create_access_token(user.document_number, user.id, timedelta(minutes=20))
    return {"access_token":token, "token_type": "bearer"}

def authenticate_user(document_number: str, password: str, db):
    user = db.query(Users).filter(Users.document_number==document_number).first()
    if not user: return False
    if not bcrypt_context.verify(password, user.hashed_password): return False
    return user

def create_access_token(document_number: str, user_id: int, expires_delta: timedelta):
    encode = {"sub": document_number, "id": user_id}
    expires = datetime.utcnow() + expires_delta
    encode.update({"exp": expires})
    return jwt.encode(encode, sk, algorithm=algo)

def get_current_user(token: Annotated[str, Depends(oauth2_bearer)]):
    try:
        payload = jwt.decode(token, sk, algorithms=[algo])
        document_number: str = payload.get("sub")
        user_id: int = payload.get("id")
        if document_number is None or user_id is None: raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                                                           detail="Validation failed")
        return {"document_number": document_number, "id": user_id}
    except JWTError: raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Validation failed")