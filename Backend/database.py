import os
from datetime import datetime, timezone
from dotenv import load_dotenv
from sqlalchemy import create_engine, Column, Integer, String, Text, Numeric, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker

# ------------------------------------------------------------------------------
# 1. CHARGEMENT DES VARIABLES D'ENVIRONNEMENT
# ------------------------------------------------------------------------------
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("La variable d'environnement DATABASE_URL n'est pas définie dans le fichier .env")

# ------------------------------------------------------------------------------
# 2. CONFIGURATION SQLALCHEMY (Engine & SessionMaker)
# ------------------------------------------------------------------------------
engine = create_engine(DATABASE_URL, echo=False)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# ------------------------------------------------------------------------------
# 3. DÉFINITION DU MODÈLE ORM (Table 'analyses')
# ------------------------------------------------------------------------------
class Analysis(Base):
    __tablename__ = "analyses"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    created_at = Column(
        DateTime(timezone=True), 
        default=lambda: datetime.now(timezone.utc), 
        nullable=False
    )
    job_title = Column(String(255), nullable=True)
    job_description = Column(Text, nullable=False)  # Obligatoire selon le schéma initial
    score = Column(Numeric(5, 2), nullable=False)   # Précision exacte à 2 décimales
    recommendations = Column(Text, nullable=False)

# ------------------------------------------------------------------------------
# 4. INJECTION DE DÉPENDANCE (Session FastAPI)
# ------------------------------------------------------------------------------
def get_db():
    """Générateur de session de base de données (pour FastAPI Depends)."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()