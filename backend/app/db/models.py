import datetime
from typing import Optional, Any
from sqlmodel import SQLModel, Field, Column
from sqlalchemy import text
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
