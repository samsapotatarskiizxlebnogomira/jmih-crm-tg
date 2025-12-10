# backend/app/db.py
import os
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Путь до корня проекта (папка backend/..)
BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "crm.db"

# SQLite база в файле crm.db рядом с backend/
DATABASE_URL = f"sqlite:///{DB_PATH}"

# Для SQLite нужен этот флаг
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=True,
    future=True,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()