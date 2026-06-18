import os
from dotenv import load_dotenv
import psycopg2

load_dotenv()
conn = psycopg2.connect(os.getenv("DATABASE_URL"))
cursor = conn.cursor()

# tabla profesional
cursor.execute("""
CREATE TABLE IF NOT EXISTS profesional (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    tipo VARCHAR(20) NOT NULL,
    especialidad VARCHAR(100) NOT NULL
);
""")

# tabla consultorio
cursor.execute("""
CREATE TABLE IF NOT EXISTS consultorio (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(50) NOT NULL
);
""")

# tabla servicio
cursor.execute("""
CREATE TABLE IF NOT EXISTS servicio (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    precio NUMERIC(10, 2) NOT NULL,
    duracion_min INTEGER NOT NULL, 
    poblacion VARCHAR(20) NOT NULL
);
""")

# tabla paciente
cursor.execute("""
CREATE TABLE IF NOT EXISTS paciente (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    poblacion VARCHAR(20) NOT NULL,
    fecha_alta DATE NOT NULL
);
""")

# tabla sesion
cursor.execute("""
CREATE TABLE IF NOT EXISTS sesion (
    id SERIAL PRIMARY KEY,
    paciente_id INTEGER REFERENCES paciente(id),
    profesional_id INTEGER REFERENCES profesional(id),
    servicio_id INTEGER REFERENCES servicio(id),
    consultorio_id INTEGER REFERENCES consultorio(id),
    modalidad VARCHAR(20) NOT NULL,
    fecha DATE NOT NULL,
    hora_inicio TIME NOT NULL,
    hora_fin TIME NOT NULL,
    estado VARCHAR(20) NOT NULL,
    monto NUMERIC(10, 2) NOT NULL
);
""")

conn.commit()
print("Esquema creado correctamente.")
  
cursor.close()
conn.close()