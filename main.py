from fastapi import FastAPI, status, Depends, HTTPException

from app import auth, models
from app.database import engine, SessionLocal
from typing import Annotated
from sqlalchemy.orm import Session

auth_ms = FastAPI()
auth_ms.include_router(auth.router)

models.Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try: yield db
    finally: db.close()

db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(auth.get_current_user)]

@auth_ms.get("/", status_code=status.HTTP_200_OK)
async def user(user: user_dependency, db: db_dependency):
    if user is None: raise HTTPException(status_code=401, detail="Auth failed")
    return {"User":user}