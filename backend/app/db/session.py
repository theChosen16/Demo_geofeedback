import logging
from sqlmodel import SQLModel, create_engine, Session
from app.core.config import settings

logger = logging.getLogger(__name__)

# Configuración del engine de SQLModel
# SQLModel es una delgada capa sobre SQLAlchemy que se integra nativamente con Pydantic.
connection_uri = settings.db_connection_uri
engine = create_engine(
    connection_uri, 
    echo=settings.DEBUG,
    pool_pre_ping=True,  # Chequea que la conexión siga viva antes de usarla
    pool_size=5,         # Ajustado al Railway free tier
    max_overflow=10
)

def get_session():
    """Generador de sesiones de base de datos para inyección de dependencias de FastAPI."""
    with Session(engine) as session:
        yield session

def init_db():
    """Crea las tablas definidas en SQLModel si no existen."""
    try:
        # Nota: En producción, Alembic debería manejar esto,
        # pero mantenemos el bootstrap nativo por compatibilidad y facilidad de despliegue.
        SQLModel.metadata.create_all(engine)
        logger.info("Base de datos inicializada (Tablas creadas/verificadas).")
        return True
    except Exception as e:
        logger.error(f"Error inicializando base de datos: {e}")
        return False
