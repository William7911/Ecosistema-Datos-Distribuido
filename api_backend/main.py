from fastapi import FastAPI, Request, Depends
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session
from motor.motor_asyncio import AsyncIOMotorClient
import json
import datetime

# Importamos las conexiones e IP desde tu database.py
from database import engine, engine_sqlserver, engine_oracle, get_db, UBUNTU_IP

app = FastAPI()

# --- CONFIGURACIÓN MONGODB ---
MONGO_URL = f"mongodb://admin:admin123@{UBUNTU_IP}:27017"
mongo_client = AsyncIOMotorClient(MONGO_URL)
mongo_db = mongo_client["auditoria_db"]
logs_collection = mongo_db["logs_forenses"]

# --- MODELOS PYDANTIC (Para recibir los JSON de Streamlit) ---
class BitacoraRequest(BaseModel):
    nombre: str
    correo: str

class VentaRequest(BaseModel):
    monto: float
    cliente: str

class InventarioRequest(BaseModel):
    nombre: str
    cantidad: int

# --- EL INTERCEPTOR UNIFICADO (DOBLE ESCRITURA) ---
@app.middleware("http")
async def auditoria_forense(request: Request, call_next):
    # 1. Procesar la petición primero
    response = await call_next(request)

    # 2. Interceptar solo si es una acción de cambio
    if request.method in ["POST", "PUT", "DELETE"]:
        ahora = datetime.datetime.now()
        
        # Armamos el paquete de datos una sola vez
        datos_log = {
            "usuario": "usuario_demo",
            "accion": request.method,
            "endpoint": str(request.url.path),
            "fecha": ahora.isoformat(),
            "payload": {"status": "accion_detectada"}
        }

        # --- ESCRITURA 1: POSTGRESQL (Estructurado) ---
        try:
            with engine.connect() as conn:
                query = text("""
                    INSERT INTO bitacora (usuario, accion, endpoint, payload) 
                    VALUES (:u, :a, :e, :p)
                """)
                conn.execute(query, {
                    "u": datos_log["usuario"], 
                    "a": datos_log["accion"], 
                    "e": datos_log["endpoint"], 
                    "p": json.dumps(datos_log["payload"])
                })
                conn.commit()
        except Exception as e:
            print(f"Error en Postgres: {e}")

        # --- ESCRITURA 2: MONGODB (Desestructurado) ---
        try:
            await logs_collection.insert_one(datos_log)
            print(f"🔥 LOG DUPLICADO: SQL y NoSQL sincronizados ({request.method} en {request.url.path})")
        except Exception as e:
            print(f"Error en Mongo: {e}")

    return response

# --- NUEVA RUTA: GET BITACORA (Para el Dashboard del Integrante 3) ---
@app.get("/bitacora")
def obtener_bitacora(db: Session = Depends(get_db)):
    query = text("SELECT id, fecha, usuario, accion, endpoint, payload FROM bitacora ORDER BY id DESC LIMIT 10")
    result = db.execute(query)
    return [dict(row._mapping) for row in result]

# --- RUTA DE PRUEBA ---
@app.post("/probar-bitacora")
async def test_post(datos: BitacoraRequest):
    return {"msg": "¡Acción realizada con éxito! Revisa Postgres y Mongo."}

# --- RUTA SQL SERVER (VENTAS PARTICIONADAS) ---
@app.post("/ventas")
async def registrar_venta(venta: VentaRequest):
    with engine_sqlserver.connect() as conn:
        query = text("""
            INSERT INTO Ventas (FechaVenta, Monto, Cliente) 
            VALUES (GETDATE(), :m, :c)
        """)
        conn.execute(query, {"m": venta.monto, "c": venta.cliente})
        conn.commit()
        
    return {"status": "Venta insertada en SQL Server", "cliente": venta.cliente}

# --- RUTA ORACLE (INVENTARIO MAESTRO) ---
@app.post("/inventario")
async def registrar_producto(item: InventarioRequest):
    with engine_oracle.connect() as conn:
        query = text("""
            INSERT INTO Inventario_Global (Nombre, Cantidad) 
            VALUES (:n, :c)
        """)
        conn.execute(query, {"n": item.nombre, "c": item.cantidad})
        conn.commit()
        
    return {"status": "Inventario actualizado en Oracle", "producto": item.nombre}