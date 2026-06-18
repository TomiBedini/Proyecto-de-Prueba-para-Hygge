import pandas as pd

# Horarios reales de Hygge Psicoterapia (lunes=0 ... viernes=4)
HORARIOS_POR_DIA = {
    0: (8, 21),  # lunes
    1: (7, 21),  # martes
    2: (7, 21),  # miércoles
    3: (8, 22),  # jueves
    4: (8, 21),  # viernes
}  # sábado y domingo: cerrado

DIAS_ES = {0: "Lunes", 1: "Martes", 2: "Miércoles", 3: "Jueves", 4: "Viernes"}


def calcular_horas_disponibles(fecha_inicio, fecha_fin):
    horas_totales = 0
    dia = fecha_inicio
    while dia <= fecha_fin:
        if dia.weekday() in HORARIOS_POR_DIA:
            apertura, cierre = HORARIOS_POR_DIA[dia.weekday()]
            horas_totales += cierre - apertura
        dia += pd.Timedelta(days=1)
    return horas_totales


def calcular_duracion_minutos(df):
    return (
        pd.to_timedelta(df["hora_fin"].astype(str)) - pd.to_timedelta(df["hora_inicio"].astype(str))
    ).dt.total_seconds() / 60


def filtrar_ocupacion_real(df):
    return df[(df["modalidad"] == "presencial") & (df["estado"] == "realizada")].copy()


def calcular_ocupacion_por_consultorio(df_ocupado, fecha_desde, fecha_hasta):
    minutos_disponibles = calcular_horas_disponibles(fecha_desde, fecha_hasta) * 60
    ocupacion = df_ocupado.groupby("consultorio")["duracion_minutos"].sum()
    return (ocupacion / minutos_disponibles) * 100


def calcular_ocupacion_mensual(df_ocupado, fecha_desde, fecha_hasta):
    df_ocupado = df_ocupado.copy()
    df_ocupado["mes"] = df_ocupado["fecha"].dt.to_period("M").astype(str)

    disponibilidad_por_mes = {}
    for mes in sorted(df_ocupado["mes"].unique()):
        periodo = pd.Period(mes, freq="M")
        inicio_mes = max(periodo.start_time, fecha_desde)
        fin_mes = min(periodo.end_time, fecha_hasta)
        disponibilidad_por_mes[mes] = calcular_horas_disponibles(inicio_mes, fin_mes) * 60

    ocupacion_mensual = (
        df_ocupado.groupby(["mes", "consultorio"])["duracion_minutos"].sum().reset_index()
    )
    ocupacion_mensual["minutos_disponibles"] = ocupacion_mensual["mes"].map(disponibilidad_por_mes)
    ocupacion_mensual["pct_ocupacion"] = (
        ocupacion_mensual["duracion_minutos"] / ocupacion_mensual["minutos_disponibles"] * 100
    )
    return ocupacion_mensual


def calcular_heatmap(df_ocupado):
    df_ocupado = df_ocupado.copy()
    df_ocupado["dia_semana"] = df_ocupado["fecha"].dt.weekday.map(DIAS_ES)
    df_ocupado["hora"] = df_ocupado["hora_inicio"].apply(lambda t: t.hour)
    return df_ocupado.groupby(["dia_semana", "hora"])["duracion_minutos"].sum().reset_index()


def calcular_ranking(df_ocupado, columna):
    return df_ocupado.groupby(columna)["duracion_minutos"].sum().sort_values(ascending=False)


def calcular_eficiencia_minutos(df_presencial):
    minutos_por_estado = df_presencial.groupby("estado")["duracion_minutos"].sum()
    minutos_reservados = minutos_por_estado.sum()
    minutos_perdidos = minutos_por_estado.get("cancelada", 0) + minutos_por_estado.get("ausente", 0)
    pct_perdido = (minutos_perdidos / minutos_reservados * 100) if minutos_reservados else 0
    return minutos_por_estado, minutos_reservados, minutos_perdidos, pct_perdido


def calcular_eficiencia_turnos(df_presencial):
    sesiones_por_estado = df_presencial.groupby("estado").size()
    turnos_reservados = sesiones_por_estado.sum()
    turnos_perdidos = sesiones_por_estado.get("cancelada", 0) + sesiones_por_estado.get("ausente", 0)
    pct_turnos_perdidos = (turnos_perdidos / turnos_reservados * 100) if turnos_reservados else 0
    return sesiones_por_estado, turnos_reservados, turnos_perdidos, pct_turnos_perdidos
