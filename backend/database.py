import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Default to the local docker compose values. This is a development-only password
# from docker-compose.yml; deployments should set DATABASE_URL explicitly.
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://civ_user:civ_password@localhost:5432/civ_timeline")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
