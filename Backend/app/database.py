import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Load environment variables
load_dotenv()

# Database Configuration
DB_PASSWORD = os.getenv("DB_PASSWORD")
if DB_PASSWORD:
    DB_PASSWORD = DB_PASSWORD.strip().strip('"').strip("'")

DB_HOST = os.getenv("DB_HOST", "localhost")
DATABASE_URL = (
    f"postgresql+psycopg2://postgres:{DB_PASSWORD}@{DB_HOST}:5432/Scraped_Data"
)

# Create Engine
engine = create_engine(DATABASE_URL, pool_size=30, max_overflow=60, pool_timeout=60)

# Session Factory
SessionLocal = sessionmaker(
    autocommit=False, autoflush=False, expire_on_commit=False, bind=engine
)

# --- DEPENDENCIES ---


# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
