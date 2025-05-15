import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.database.models import Base
from dotenv import load_dotenv

load_dotenv()

SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./test.db")

#Base = declarative_base()
pool_size=int(os.getenv("POOL_SIZE",10))
max_overflow=int(os.getenv("MAX_OVERFLOW",20))
pool_timeout=int(os.getenv("POOL_TIMEOUT",120))

engine = create_engine(SQLALCHEMY_DATABASE_URL, echo=False, pool_size=pool_size, max_overflow=max_overflow, pool_timeout=pool_timeout, pool_recycle=1800)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Função para criar as tabelas no banco
def init_db():
    session = SessionLocal()
    return session
