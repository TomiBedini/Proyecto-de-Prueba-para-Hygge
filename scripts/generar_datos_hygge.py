import os
import random
from datetime import date, timedelta, time

from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import execute_values

load_dotenv()
conn = psycopg2.connect(os.getenv("DATABASE_URL"))
cursor = conn.cursor()

random.seed(7)

# ============================================================
# 1. PROFESIONALES
# ============================================================
PROFESIONALES = [
    ("Agustina Ferreyra", "psicólogo", "Clínica adultos"),
    ("Bruno Castelli", "psicólogo", "Clínica adultos"),
    ("Camila Suárez", "psicólogo", "Clínica adultos"),
    ("Diego Manrique", "psicólogo", "Clínica adultos"),
    ("Florencia Aguirre", "psicólogo", "DBT"),
    ("Gonzalo Pereyra", "psicólogo", "DBT"),
    ("Helena Roldán", "psicólogo", "Infanto-juvenil"),
    ("Ignacio Vidal", "psicólogo", "Infanto-juvenil"),
    ("Julieta Campos", "psicólogo", "Infanto-juvenil"),
    ("Lautaro Funes", "psicólogo", "Adolescentes"),
    ("Martina Quiroga", "psicólogo", "Adolescentes"),
    ("Nicolás Toledo", "psicólogo", "Orientación vocacional"),
    ("Ornella Bazán", "psicólogo", "Orientación vocacional"),
    ("Pablo Sosa", "psiquiatra", "Psiquiatría adultos"),
    ("Renata Acosta", "psiquiatra", "Psiquiatría adultos"),
    ("Santiago Lema", "psiquiatra", "Psiquiatría infanto-juvenil"),
]

profesional_ids = {}
for nombre, tipo, especialidad in PROFESIONALES:
    cursor.execute(
        "INSERT INTO profesional (nombre, tipo, especialidad) VALUES (%s, %s, %s) RETURNING id",
        (nombre, tipo, especialidad),
    )
    profesional_ids[nombre] = cursor.fetchone()[0]

# ============================================================
# 2. CONSULTORIOS
# ============================================================
CONSULTORIOS = ["Consultorio 1", "Consultorio 2", "Consultorio 3", "Consultorio 4"]

consultorio_ids = {}
for nombre in CONSULTORIOS:
    cursor.execute(
        "INSERT INTO consultorio (nombre) VALUES (%s) RETURNING id", (nombre,)
    )
    consultorio_ids[nombre] = cursor.fetchone()[0]

# ============================================================
# 3. SERVICIOS
# (nombre, precio, duracion_min, poblacion, especialidad_requerida)
# ============================================================
SERVICIOS = [
    ("Admisión adultos", 65000, 60, "adultos", "Clínica adultos"),
    ("Admisión niños", 50000, 60, "niños", "Infanto-juvenil"),
    ("Admisión psiquiatría", 60000, 45, "adultos", "Psiquiatría adultos"),
    ("Tratamiento adultos", 40000, 50, "adultos", "Clínica adultos"),
    ("Tratamiento adolescentes", 40000, 50, "adolescentes", "Adolescentes"),
    ("Tratamiento niños", 40000, 45, "niños", "Infanto-juvenil"),
    ("DBT", 40000, 90, "adultos", "DBT"),
    ("Orientación vocacional", 6000, 60, "adolescentes", "Orientación vocacional"),
    ("Acompañamiento a padres", 35000, 60, "niños", "Infanto-juvenil"),
    ("Consulta psiquiátrica", 60000, 30, "adultos", "Psiquiatría adultos"),
]

servicio_ids = {}
servicio_info = {}  # nombre -> (precio, duracion_min, poblacion, especialidad_requerida)
for nombre, precio, duracion_min, poblacion, especialidad in SERVICIOS:
    cursor.execute(
        """INSERT INTO servicio (nombre, precio, duracion_min, poblacion)
           VALUES (%s, %s, %s, %s) RETURNING id""",
        (nombre, precio, duracion_min, poblacion),
    )
    servicio_ids[nombre] = cursor.fetchone()[0]
    servicio_info[nombre] = (precio, duracion_min, poblacion, especialidad)

conn.commit()
print("Profesionales, consultorios y servicios cargados.")

# ============================================================
# 4. PACIENTES
# ============================================================
NOMBRES_PACIENTES = [f"Paciente {i}" for i in range(1, 161)]
POBLACIONES_PESOS = ["adultos"] * 6 + ["adolescentes"] * 2 + ["niños"] * 2  # 60/20/20

FECHA_INICIO_ALTAS = date(2025, 12, 1)
FECHA_FIN_ALTAS = date(2026, 6, 17)
rango_dias_altas = (FECHA_FIN_ALTAS - FECHA_INICIO_ALTAS).days

paciente_ids = []  # lista de tuplas (id, poblacion)
for nombre in NOMBRES_PACIENTES:
    poblacion = random.choice(POBLACIONES_PESOS)
    fecha_alta = FECHA_INICIO_ALTAS + timedelta(days=random.randint(0, rango_dias_altas))
    cursor.execute(
        """INSERT INTO paciente (nombre, poblacion, fecha_alta)
           VALUES (%s, %s, %s) RETURNING id""",
        (nombre, poblacion, fecha_alta),
    )
    paciente_ids.append((cursor.fetchone()[0], poblacion))

conn.commit()
print(f"{len(paciente_ids)} pacientes cargados.")

# ============================================================
# 5. SESIONES
# ============================================================
especialidad_a_profesionales = {}
for nombre, tipo, especialidad in PROFESIONALES:
    especialidad_a_profesionales.setdefault(especialidad, []).append(profesional_ids[nombre])

pacientes_por_poblacion = {"adultos": [], "adolescentes": [], "niños": []}
for pid, poblacion in paciente_ids:
    pacientes_por_poblacion[poblacion].append(pid)

# Horarios reales de Hygge Psicoterapia (lunes=0 ... domingo=6)
HORARIOS_POR_DIA = {
    0: (8, 21),  # lunes
    1: (7, 21),  # martes
    2: (7, 21),  # miércoles
    3: (8, 22),  # jueves
    4: (8, 21),  # viernes
}  # sábado/domingo: cerrado (no están en el diccionario)

FECHA_INICIO = date(2026, 2, 16)
FECHA_FIN = date(2026, 6, 17)

ESTADOS_PESOS = ["realizada"] * 7 + ["cancelada"] * 2 + ["ausente"] * 1  # ~70/20/10


def generar_dias_habiles():
    dias = []
    actual = FECHA_INICIO
    while actual <= FECHA_FIN:
        if actual.weekday() in HORARIOS_POR_DIA:
            dias.append(actual)
        actual += timedelta(days=1)
    return dias


def elegir_servicio_profesional_paciente():
    nombre_servicio = random.choice(list(servicio_info.keys()))
    precio, duracion_min, poblacion, especialidad = servicio_info[nombre_servicio]
    profesional_id = random.choice(especialidad_a_profesionales[especialidad])
    paciente_id = random.choice(pacientes_por_poblacion[poblacion])
    return nombre_servicio, precio, duracion_min, profesional_id, paciente_id


filas_sesiones = []

for dia in generar_dias_habiles():
    hora_apertura, hora_cierre = HORARIOS_POR_DIA[dia.weekday()]

    # --- Sesiones presenciales: una agenda independiente por consultorio ---
    for nombre_consultorio, consultorio_id in consultorio_ids.items():
        if random.random() < 0.1:
            continue  # ese consultorio no se usó ese día

        minuto_actual = hora_apertura * 60
        minuto_cierre = hora_cierre * 60

        while minuto_actual < minuto_cierre:
            if random.random() < 0.2:
                minuto_actual += 30  # hueco libre, no se ocupa esa franja
                continue

            nombre_servicio, precio, duracion_min, profesional_id, paciente_id = (
                elegir_servicio_profesional_paciente()
            )

            if minuto_actual + duracion_min > minuto_cierre:
                break

            hora_inicio = time(minuto_actual // 60, minuto_actual % 60)
            minuto_fin = minuto_actual + duracion_min
            hora_fin = time(minuto_fin // 60, minuto_fin % 60)

            estado = random.choice(ESTADOS_PESOS)
            monto = precio if estado == "realizada" else 0

            filas_sesiones.append((
                paciente_id, profesional_id, servicio_ids[nombre_servicio],
                consultorio_id, "presencial", dia, hora_inicio, hora_fin,
                estado, monto,
            ))

            minuto_actual = minuto_fin

    # --- Sesiones virtuales: no ocupan ningún consultorio físico ---
    cantidad_virtuales = random.randint(0, 6)
    for _ in range(cantidad_virtuales):
        nombre_servicio, precio, duracion_min, profesional_id, paciente_id = (
            elegir_servicio_profesional_paciente()
        )

        minuto_inicio = random.randint(
            hora_apertura * 60, hora_cierre * 60 - duracion_min
        )
        hora_inicio = time(minuto_inicio // 60, minuto_inicio % 60)
        minuto_fin = minuto_inicio + duracion_min
        hora_fin = time(minuto_fin // 60, minuto_fin % 60)

        estado = random.choice(ESTADOS_PESOS)
        monto = precio if estado == "realizada" else 0

        filas_sesiones.append((
            paciente_id, profesional_id, servicio_ids[nombre_servicio],
            None, "virtual", dia, hora_inicio, hora_fin, estado, monto,
        ))

execute_values(
    cursor,
    """INSERT INTO sesion
       (paciente_id, profesional_id, servicio_id, consultorio_id,
        modalidad, fecha, hora_inicio, hora_fin, estado, monto)
       VALUES %s""",
    filas_sesiones,
)

conn.commit()
print(f"{len(filas_sesiones)} sesiones cargadas.")

cursor.close()
conn.close()
