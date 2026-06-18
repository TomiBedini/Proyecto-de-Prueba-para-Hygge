# Dashboard de Ocupación — Hygge Psicoterapia

Este es un proyecto que armé para prepararme para la entrevista laboral. La idea era practicar el stack que pedían (Python, Pandas, SQL, Streamlit) pero con algo más cercano a un caso real que con un dataset genérico.

Los datos que ves acá son simulados, pero están armados a partir de datos públicos del negocio: sus servicios, precios, horarios de atención y cantidad de profesionales.

## Demo

[Link a la app desplegada] _(pendiente)_

## Qué muestra

El dashboard está dividido en tres pestañas:

- Resumen: cuánto se está ocupando cada consultorio, qué tipo de servicios y de pacientes generan más ocupación, y qué profesionales usan más el espacio físico.
- Tendencias: cómo varió la ocupación mes a mes, y un mapa de calor para ver qué días y horarios están más saturados.
- Eficiencia: cuánto tiempo (y cuántos turnos) se pierden por cancelaciones o ausencias.

## Stack

- Python + Pandas para procesar los datos
- PostgreSQL (alojado en [Neon](https://neon.tech)) como base
- SQLAlchemy para conectar
- Streamlit para la interfaz
- Altair para los gráficos

## Estructura

```
├── app/
│   ├── dashboard.py     # la interfaz: filtros, pestañas, gráficos
│   ├── datos.py         # conexión y carga de datos
│   └── calculos.py      # los cálculos de cada indicador
├── scripts/
│   ├── crear_esquema.py         # crea las tablas en Postgres
│   ├── generar_datos_hygge.py   # genera y carga los datos simulados
│   └── conexion.py              # prueba de conexión a la base
├── assets/
│   └── hygge_logo.png
└── requirements.txt
```

## Modelo de datos

Son 5 tablas: `profesional`, `consultorio`, `servicio`, `paciente` y `sesion` (esta última es la que conecta a todas las demás, ahí vive cada turno).

## Si querés correrlo

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Necesitás un archivo `.env` en la raíz con tu propia conexión a Postgres:
```
DATABASE_URL=postgresql://usuario:password@host/db?sslmode=require
```

Y después:
```bash
streamlit run app/dashboard.py
```
