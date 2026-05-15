from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Configuración de red (deja localhost por ahora si están probando en tu máquina)
UBUNTU_IP = "127.0.0.1"

# --- CONFIGURACIÓN POSTGRES (Ojo al cambio a bd_principal) ---
URL_DATABASE = f"postgresql://admin:admin123@{UBUNTU_IP}:5432/bd_principal"

# El motor que gestiona la conexión
engine = create_engine(URL_DATABASE)

# La fábrica de sesiones para hacer consultas
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- CONFIGURACIÓN SQL SERVER ---
URL_SQLSERVER = f"mssql+pymssql://sa:PasswordFuerte2026!@{UBUNTU_IP}:1433/CorporativoDB"
engine_sqlserver = create_engine(URL_SQLSERVER)

# --- CONFIGURACIÓN ORACLE ---
URL_ORACLE = f"oracle+oracledb://SYSTEM:PasswordFuerte2026!@{UBUNTU_IP}:1521/?service_name=FREEPDB1"
engine_oracle = create_engine(URL_ORACLE)
