import os
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# Configuración de conexión
DATABASE_URL = os.getenv('DATABASE_URL')

try:
    if DATABASE_URL:
        print(f"Usando DATABASE_URL...")
        conn = psycopg2.connect(DATABASE_URL)
    else:
        # Variables individuales (OBLIGATORIAS — no usar defaults inseguros)
        DB_HOST = os.getenv('DB_HOST')
        DB_PORT = os.getenv('DB_PORT')
        DB_USER = os.getenv('DB_USER')
        DB_PASSWORD = os.getenv('DB_PASSWORD')
        DB_NAME = os.getenv('DB_NAME', 'railway')

        if not all([DB_HOST, DB_PORT, DB_USER, DB_PASSWORD]):
            raise ValueError(
                "Variables de entorno requeridas: DB_HOST, DB_PORT, DB_USER, DB_PASSWORD. "
                "Configúralas antes de ejecutar este script."
            )

        print(f"Conectando a {DB_HOST}:{DB_PORT} como {DB_USER}...")
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            dbname=DB_NAME
        )

    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cur = conn.cursor()
    
    print("Conexión exitosa.")

    # 1. Leer y ejecutar Schema (01_setup_postgis_schema.sql)
    print("Ejecutando 01_setup_postgis_schema.sql...")
    with open('scripts/sql/01_setup_postgis_schema.sql', 'r', encoding='utf-8') as f:
        sql_schema = f.read()
        # Eliminar comandos \c y \echo que son de psql, no de psycopg2
        sql_clean = "\n".join([line for line in sql_schema.splitlines() if not line.startswith('\\')])
        cur.execute(sql_clean)
    print("Schema creado.")

    # 2. Leer y ejecutar Funciones (04_create_functions.sql)
    print("Ejecutando 04_create_functions.sql...")
    with open('scripts/sql/04_create_functions.sql', 'r', encoding='utf-8') as f:
        sql_funcs = f.read()
        sql_clean = "\n".join([line for line in sql_funcs.splitlines() if not line.startswith('\\')])
        cur.execute(sql_clean)
    print("Funciones creadas.")

    cur.close()
    conn.close()
    print("\n✅ Inicialización de Base de Datos COMPLETADA.")

except Exception as e:
    print(f"\n❌ Error: {e}")
