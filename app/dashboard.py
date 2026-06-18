import os
import pandas as pd
import streamlit as st
import altair as alt

from datos import cargar_datos
from calculos import (
    calcular_duracion_minutos,
    filtrar_ocupacion_real,
    calcular_ocupacion_por_consultorio,
    calcular_ocupacion_mensual,
    calcular_heatmap,
    calcular_ranking,
    calcular_eficiencia_minutos,
    calcular_eficiencia_turnos,
)

# PALETA DE COLORES (extraída del logo de Hygge)
COLOR_GRIS = "#383639"
COLOR_AMARILLO = "#F0B400"
COLOR_VERDE = "#00B450"

RAIZ_PROYECTO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOGO_PATH = os.path.join(RAIZ_PROYECTO, "assets", "hygge_logo.png")

st.set_page_config(
    page_title="Ocupación — Hygge Psicoterapia",
    page_icon=LOGO_PATH,
    layout="wide",
)

# BARRA LATERAL: identidad del proyecto
st.sidebar.image(LOGO_PATH, width=120)
st.sidebar.markdown("### Dashboard de Ocupación")
st.sidebar.caption(
    "Datos simulados con fines demostrativos. " 
    "Dashboard creado por Tomás Bedini."
)

st.title("Dashboard de Ocupación — Hygge Psicoterapia")

with st.spinner("Cargando datos..."):
    df_raw = cargar_datos()

# FILTRO DE FECHAS
fecha_min_dataset = df_raw["fecha"].min()
fecha_max_dataset = df_raw["fecha"].max()

rango_fechas = st.date_input(
    "Rango de fechas",
    value=(fecha_min_dataset, fecha_max_dataset),
    min_value=fecha_min_dataset,
    max_value=fecha_max_dataset,
)

if len(rango_fechas) == 2:
    fecha_desde, fecha_hasta = rango_fechas
else:
    fecha_desde = fecha_hasta = rango_fechas[0]

fecha_desde = pd.Timestamp(fecha_desde)
fecha_hasta = pd.Timestamp(fecha_hasta)

df = df_raw[(df_raw["fecha"] >= fecha_desde) & (df_raw["fecha"] <= fecha_hasta)].copy()
df["duracion_minutos"] = calcular_duracion_minutos(df)
df_ocupado = filtrar_ocupacion_real(df)
df_presencial = df[df["modalidad"] == "presencial"]

tab_resumen, tab_tendencias, tab_eficiencia = st.tabs(
    ["Resumen", "Tendencias", "Eficiencia"]
)

# TAB 1 — RESUMEN
with tab_resumen:
    ocupacion_pct = calcular_ocupacion_por_consultorio(df_ocupado, fecha_desde, fecha_hasta)

    st.metric("Ocupación promedio general", f"{ocupacion_pct.mean():.1f}%")
    st.caption(
        "Porcentaje de horas de consultorio efectivamente usadas (presencial + realizada) "
        "sobre las horas disponibles según el horario real de atención."
    )

    st.subheader("Ocupación por consultorio")
    ocupacion_chart_df = ocupacion_pct.round(1).reset_index()
    ocupacion_chart_df.columns = ["consultorio", "pct_ocupacion"]
    chart_consultorio = (
        alt.Chart(ocupacion_chart_df)
        .mark_bar(color=COLOR_AMARILLO)
        .encode(
            x=alt.X("consultorio:N", title="Consultorio"),
            y=alt.Y("pct_ocupacion:Q", title="% de ocupación"),
            tooltip=["consultorio", "pct_ocupacion"],
        )
    )
    st.altair_chart(chart_consultorio, use_container_width=True)

    col_a, col_b = st.columns(2)

    with col_a:
        st.subheader("Por tipo de servicio")
        st.caption("Qué tipo de prestación consume más minutos de consultorio.")
        servicio_df = calcular_ranking(df_ocupado, "servicio").reset_index()
        servicio_df.columns = ["servicio", "duracion_minutos"]
        chart_servicio = (
            alt.Chart(servicio_df)
            .mark_bar(color=COLOR_AMARILLO)
            .encode(
                x=alt.X("duracion_minutos:Q", title="Minutos ocupados"),
                y=alt.Y("servicio:N", title="", sort="-x"),
                tooltip=["servicio", "duracion_minutos"],
            )
        )
        st.altair_chart(chart_servicio, use_container_width=True)

    with col_b:
        st.subheader("Por población atendida")
        st.caption("Distribución de la ocupación entre adultos, adolescentes y niños.")
        poblacion_df = calcular_ranking(df_ocupado, "poblacion_paciente").reset_index()
        poblacion_df.columns = ["poblacion", "duracion_minutos"]
        chart_poblacion = (
            alt.Chart(poblacion_df)
            .mark_bar(color=COLOR_VERDE)
            .encode(
                x=alt.X("duracion_minutos:Q", title="Minutos ocupados"),
                y=alt.Y("poblacion:N", title="", sort="-x"),
                tooltip=["poblacion", "duracion_minutos"],
            )
        )
        st.altair_chart(chart_poblacion, use_container_width=True)

    st.subheader("Ranking de profesionales por ocupación generada")
    st.caption("Quiénes usan más el espacio físico de consultorios (no incluye sesiones virtuales).")
    profesional_df = calcular_ranking(df_ocupado, "profesional").reset_index()
    profesional_df.columns = ["profesional", "duracion_minutos"]
    chart_profesional = (
        alt.Chart(profesional_df)
        .mark_bar(color=COLOR_GRIS)
        .encode(
            x=alt.X("duracion_minutos:Q", title="Minutos ocupados"),
            y=alt.Y("profesional:N", title="", sort="-x"),
            tooltip=["profesional", "duracion_minutos"],
        )
    )
    st.altair_chart(chart_profesional, use_container_width=True)

# TAB 2 — TENDENCIAS
with tab_tendencias:
    ocupacion_mensual = calcular_ocupacion_mensual(df_ocupado, fecha_desde, fecha_hasta)

    st.subheader("Evolución mensual de ocupación")
    consultorio_sel = st.selectbox(
        "Elegí un consultorio para ver su evolución",
        sorted(ocupacion_mensual["consultorio"].unique()),
    )
    st.caption("Permite ver si la ocupación de un consultorio sube, baja o se mantiene estable mes a mes.")

    filtrado = ocupacion_mensual[ocupacion_mensual["consultorio"] == consultorio_sel]
    chart_mensual = (
        alt.Chart(filtrado)
        .mark_line(point=True, color=COLOR_AMARILLO)
        .encode(
            x=alt.X("mes:O", title="Mes"),
            y=alt.Y("pct_ocupacion:Q", title="% de ocupación"),
            tooltip=["mes", "pct_ocupacion"],
        )
    )
    st.altair_chart(chart_mensual, use_container_width=True)

    st.subheader("Mapa de calor — Ocupación por día y franja horaria")
    st.caption("Identifica picos de demanda (días/horas saturados) y huecos libres que podrían reasignarse.")

    heatmap_datos = calcular_heatmap(df_ocupado)
    orden_dias = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes"]

    heatmap_chart = (
        alt.Chart(heatmap_datos)
        .mark_rect()
        .encode(
            x=alt.X("hora:O", title="Hora del día"),
            y=alt.Y("dia_semana:N", title="Día", sort=orden_dias),
            color=alt.Color(
                "duracion_minutos:Q",
                title="Minutos ocupados",
                scale=alt.Scale(range=["#FBE9B8", COLOR_AMARILLO]),
            ),
            tooltip=["dia_semana", "hora", "duracion_minutos"],
        )
    )
    st.altair_chart(heatmap_chart, use_container_width=True)

# TAB 3 — EFICIENCIA
with tab_eficiencia:
    escala_estado = alt.Scale(
        domain=["realizada", "cancelada", "ausente"],
        range=[COLOR_VERDE, COLOR_AMARILLO, COLOR_GRIS],
    )

    minutos_por_estado, minutos_reservados, minutos_perdidos, pct_perdido = calcular_eficiencia_minutos(
        df_presencial
    )

    st.subheader("Tiempo reservado vs. tiempo perdido")
    st.caption(
        "Mide eficiencia del espacio físico: cuánto del tiempo reservado en consultorios "
        "se perdió por cancelaciones o ausencias."
    )

    col1, col2 = st.columns(2)
    col1.metric("Minutos reservados (presencial)", f"{minutos_reservados:,.0f}")
    col2.metric("Minutos perdidos (cancelado/ausente)", f"{minutos_perdidos:,.0f}", f"{pct_perdido:.1f}% del total")

    minutos_df = minutos_por_estado.reset_index()
    minutos_df.columns = ["estado", "duracion_minutos"]
    chart_minutos = (
        alt.Chart(minutos_df)
        .mark_bar()
        .encode(
            x=alt.X("estado:N", title="Estado"),
            y=alt.Y("duracion_minutos:Q", title="Minutos"),
            color=alt.Color("estado:N", scale=escala_estado, legend=None),
            tooltip=["estado", "duracion_minutos"],
        )
    )
    st.altair_chart(chart_minutos, use_container_width=True)

    sesiones_por_estado, turnos_reservados, turnos_perdidos, pct_turnos_perdidos = calcular_eficiencia_turnos(
        df_presencial
    )

    st.subheader("Tasa de ausentismo/cancelación — en cantidad de turnos")
    st.caption(
        "Mide comportamiento de pacientes: cuántos turnos (no minutos) se perdieron, "
        "útil para evaluar recordatorios automáticos."
    )

    col3, col4 = st.columns(2)
    col3.metric("Turnos reservados (presencial)", f"{turnos_reservados:,.0f}")
    col4.metric("Turnos perdidos (cancelado/ausente)", f"{turnos_perdidos:,.0f}", f"{pct_turnos_perdidos:.1f}% del total")

    turnos_df = sesiones_por_estado.reset_index()
    turnos_df.columns = ["estado", "cantidad"]
    chart_turnos = (
        alt.Chart(turnos_df)
        .mark_bar()
        .encode(
            x=alt.X("estado:N", title="Estado"),
            y=alt.Y("cantidad:Q", title="Cantidad de turnos"),
            color=alt.Color("estado:N", scale=escala_estado, legend=None),
            tooltip=["estado", "cantidad"],
        )
    )
    st.altair_chart(chart_turnos, use_container_width=True)
