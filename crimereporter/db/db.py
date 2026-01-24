from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

from crimereporter.utils.config import Config

config = Config()
# -------------------------------
# 1️⃣ Base class for all ORM models
# -------------------------------
class Base(DeclarativeBase):
    """All ORM models should inherit from this Base."""
    pass

# -------------------------------
# 2️⃣ Database engine
# -------------------------------
# For SQLite, future=True enables 2.0 style API

engine = create_engine(
    config.database_url,
    echo=False,           # True for SQL debug logs
    future=True,          # Use SQLAlchemy 2.0 style
    connect_args={"check_same_thread": False},  # allows multithreaded use
)

# -------------------------------
# 3️⃣ Session factory
# -------------------------------
# Use SessionLocal() as context manager for DB operations
SessionLocal = sessionmaker(
    bind=engine,
    autoflush=True,
    expire_on_commit=False,
    future=True
)

# -------------------------------
# 4️⃣ Helper: Base.metadata.create_all
# -------------------------------
def init_db():
    """Creates all tables defined on Base metadata."""
    Base.metadata.create_all(bind=engine)
