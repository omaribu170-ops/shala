import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Supabase connection string format: postgresql://<user>:<password>@<host>:<port>/<dbname>
# For local development we can fallback to sqlite if needed, but we pivot to Supabase.
SUPABASE_URL = os.environ.get("SUPABASE_URL", "sqlite:///./app.db")

if SUPABASE_URL.startswith("postgres://"):
    SUPABASE_URL = SUPABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(
    SUPABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in SUPABASE_URL else {}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
