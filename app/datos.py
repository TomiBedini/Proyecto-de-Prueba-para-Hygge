import os
import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from sqlalchemy import create_engine

load_dotenv()


def obtener_url_conexion():
    try:
        if "DATABASE_URL" in st.secrets:
            return st.secrets["DATABASE_URL"]
    except st.errors.StreamlitSecretNotFoundError:
        pass
    return os.getenv("DATABASE_URL")


@st.cache_data(ttl=3600)
def cargar_datos():
    engine = create_engine(obtener_url_conexion())

    query = """
    SELECT
        s.fecha,
        s.hora_inicio,
        s.hora_fin,
        s.modalidad,
        s.estado,
        c.nombre AS consultorio,
        p.nombre AS profesional,
        sv.nombre AS servicio,
        pac.poblacion AS poblacion_paciente
    FROM sesion s
    LEFT JOIN consultorio c ON s.consultorio_id = c.id
    JOIN profesional p ON s.profesional_id = p.id
    JOIN servicio sv ON s.servicio_id = sv.id
    JOIN paciente pac ON s.paciente_id = pac.id
    """
    datos = pd.read_sql(query, engine)
    datos["fecha"] = pd.to_datetime(datos["fecha"])
    return datos
