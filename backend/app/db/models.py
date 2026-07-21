import datetime
from typing import Optional, Any
from sqlmodel import SQLModel, Field, Column
from sqlalchemy import text
from sqlalchemy.dialects.postgresql import JSONB
from geoalchemy2 import Geometry

# Definición de esquemas en PostgreSQL
# Ambos modelos se guardan en el esquema "metadata" por compatibilidad con el sistema actual.

class PageVisit(SQLModel, table=True):
    __tablename__ = "page_visits"
    __table_args__ = {"schema": "metadata"}

    id: Optional[int] = Field(default=None, primary_key=True)
    visit_date: datetime.datetime = Field(
        default_factory=datetime.datetime.now,
        sa_column_kwargs={"server_default": text("CURRENT_TIMESTAMP")}
    )
    page: str = Field(default="/", max_length=255)
    user_agent: Optional[str] = Field(default=None)
    ip_hash: Optional[str] = Field(default=None, max_length=64)


class ApiUsageLog(SQLModel, table=True):
    __tablename__ = "api_usage_logs"
    __table_args__ = {"schema": "metadata"}

    id: Optional[int] = Field(default=None, primary_key=True)
    timestamp: datetime.datetime = Field(
        default_factory=datetime.datetime.now,
        sa_column_kwargs={"server_default": text("CURRENT_TIMESTAMP")}
    )
    endpoint: str = Field(max_length=100)
    location_name: Optional[str] = Field(default=None, max_length=255)
    
    # Campo geométrico espacial compatible con PostGIS.
    # Usamos Column de SQLAlchemy pasándole el tipo Geometry de GeoAlchemy2.
    coordinates: Any = Field(
        sa_column=Column(
            Geometry(geometry_type="POINT", srid=4326, spatial_index=True),
            nullable=True
        )
    )
    
    approach: str = Field(max_length=100)
    status: str = Field(default="success", max_length=50)


class User(SQLModel, table=True):
    __tablename__ = "users"
    __table_args__ = {"schema": "metadata"}

    id: Optional[int] = Field(default=None, primary_key=True)
    google_sub: str = Field(max_length=255, unique=True, index=True)
    email: str = Field(max_length=320, index=True)
    name: Optional[str] = Field(default=None, max_length=255)
    picture_url: Optional[str] = Field(default=None, max_length=1024)
    created_at: datetime.datetime = Field(
        default_factory=datetime.datetime.now,
        sa_column_kwargs={"server_default": text("CURRENT_TIMESTAMP")}
    )
    last_login_at: datetime.datetime = Field(
        default_factory=datetime.datetime.now,
        sa_column_kwargs={"server_default": text("CURRENT_TIMESTAMP")}
    )


class UserAnalysis(SQLModel, table=True):
    __tablename__ = "user_analyses"
    __table_args__ = {"schema": "metadata"}

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="metadata.users.id", index=True)
    task_id: str = Field(max_length=64, index=True)
    created_at: datetime.datetime = Field(
        default_factory=datetime.datetime.now,
        sa_column_kwargs={"server_default": text("CURRENT_TIMESTAMP")}
    )

    location_name: str = Field(max_length=255)
    lat: float
    lng: float
    radius: int
    approach: str = Field(max_length=100)

    # Campo geométrico espacial compatible con PostGIS (igual que ApiUsageLog.coordinates).
    coordinates: Any = Field(
        sa_column=Column(
            Geometry(geometry_type="POINT", srid=4326, spatial_index=True),
            nullable=True
        )
    )

    # Snapshot completo del análisis en el momento en que se generó, para poder
    # re-mostrar el historial del usuario sin volver a golpear Google Earth Engine.
    indices: Optional[dict] = Field(default=None, sa_column=Column(JSONB, nullable=True))
    chart_data: Optional[list] = Field(default=None, sa_column=Column(JSONB, nullable=True))
    map_layer_url: Optional[str] = Field(default=None, max_length=2048)
    image_date: Optional[str] = Field(default=None, max_length=30)
    interpretation: Optional[str] = Field(default=None)


class UserAlert(SQLModel, table=True):
    __tablename__ = "user_alerts"
    __table_args__ = {"schema": "metadata"}

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="metadata.users.id", index=True)
    location_name: str = Field(max_length=255)
    lat: float
    lng: float
    radius: int
    approach: str = Field(max_length=100)
    
    # Campo geométrico compatible con PostGIS
    coordinates: Any = Field(
        sa_column=Column(
            Geometry(geometry_type="POINT", srid=4326, spatial_index=True),
            nullable=True
        )
    )

    created_at: datetime.datetime = Field(
        default_factory=datetime.datetime.now,
        sa_column_kwargs={"server_default": text("CURRENT_TIMESTAMP")}
    )
    is_active: bool = Field(default=True)
    frequency: str = Field(max_length=20, default="daily")
    
    # Alertas personalizables:
    # ndvi_below, ndwi_above, ndmi_below, ndvi_drop_pct
    trigger_type: str = Field(max_length=50, default="ndvi_below")
    trigger_value: float = Field(default=0.3)
    
    last_checked_at: Optional[datetime.datetime] = Field(default=None)
    last_index_value: Optional[float] = Field(default=None)
