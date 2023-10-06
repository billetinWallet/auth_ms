from app.database import Base
from sqlalchemy import Column, Integer, String

class Users(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    document_number = Column(String, unique=True)
    hashed_password = Column(String)