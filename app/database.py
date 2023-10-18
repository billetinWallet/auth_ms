from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

db_url = 'postgresql://ms:gRIgBmN8KFuqmhcL2EV0vHmLDLojxinY@dpg-cko5idujmi5c73essu00-a/auth_db_7z9w'
engine = create_engine(db_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()