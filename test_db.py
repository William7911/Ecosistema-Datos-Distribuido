from database import engine
from sqlalchemy import text

try:
    # Intentamos conectarnos y ejecutar una consulta simple
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))
        print("✅ ¡CONEXIÓN EXITOSA! Python ya puede hablar con Postgres.")
except Exception as e:
    print(f"❌ ERROR DE CONEXIÓN: {e}")