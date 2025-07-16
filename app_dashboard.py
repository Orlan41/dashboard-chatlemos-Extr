import streamlit as st
import pandas as pd
import plotly.express as px
import gspread
from gspread_dataframe import get_as_dataframe
from oauth2client.service_account import ServiceAccountCredentials

# --- Autenticación Google Sheets ---
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets, scope)
client = gspread.authorize(creds)

# --- Cargar datos desde Google Sheets ---
sheet = client.open_by_url("https://docs.google.com/spreadsheets/d/1InpmV--7WJuKEdMML4F05xWapcyzOqOd5uVOv0HKK-Y/edit")
worksheet = sheet.worksheet("2025 Registro Listas de asistencia")
df = get_as_dataframe(worksheet, evaluate_formulas=True)
df = df.dropna(how='all')

# --- Limpiar y renombrar columnas relevantes ---
df.columns = df.columns.str.strip()
df = df.rename(columns={
    "Fecha del caso": "fecha",
    "Edad": "edad",
    "Género": "genero",
    "Barrio": "barrio",
    "Clasificación del riesgo": "riesgo",
    "EPS actual según ADRES": "eps",
    "Canal de recepción": "canal",
    "Motivo de consulta": "motivo",
    "Conducta": "conducta",
    "Localidad": "localidad",
    "Observaciones": "observaciones"
})

# --- Streamlit config ---
st.set_page_config(page_title="Dashboard Chatlemos", layout="wide")
st.title("📊 Dashboard de Intervenciones Extramurales - Chatlemos 2025")

# --- KPIs ---
col1, col2, col3 = st.columns(3)
col1.metric("👥 Total de registros", len(df))
col2.metric("🏥 EPS distintas", df['eps'].nunique())
col3.metric("📍 Barrios atendidos", df['barrio'].nunique())

st.markdown("---")

# --- Preparar datos ---
df['fecha'] = pd.to_datetime(df['fecha'], errors='coerce')
df['mes'] = df['fecha'].dt.month
df['año'] = df['fecha'].dt.year

# Normalizar motivos similares
df['motivo'] = df['motivo'].str.strip().str.lower()
df['motivo'] = df['motivo'].replace({
    'intervenciones extramurales': 'Intervenciones Extramurales',
    'intervenciones ied': 'Intervenciones IED'
})

# Normalizar conducta similares
df['conducta'] = df['conducta'].str.strip().str.lower()
df['conducta'] = df['conducta'].replace({
    'promoción y prevención.': 'Promoción y prevención',
    'promoción y prevención ': 'Promoción y prevención',
    'promoción y prevención': 'Promoción y prevención'
})
df['conducta'] = df['conducta'].str.title()
df['motivo'] = df['motivo'].str.title()

# Etiquetas de mes
meses_dict = {
    1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril",
    5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto",
    9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"
}
df['mes_nombre'] = df['mes'].map(meses_dict)

# --- Visualizaciones ---

# Casos por mes y motivo
df_2025 = df[df['año'] == 2025]
graf_motivo = px.histogram(
    df_2025,
    x="mes_nombre",
    color="motivo",
    title="Casos por mes y motivo de consulta",
    category_orders={"mes_nombre": list(meses_dict.values())}
)
st.plotly_chart(graf_motivo, use_container_width=True)

# Distribución por Género
graf_genero = px.pie(df_2025, names="genero", title="Distribución por Género", color_discrete_sequence=px.colors.sequential.RdBu)
st.plotly_chart(graf_genero, use_container_width=True)

# Distribución por Conducta
graf_conducta = px.pie(df_2025, names="conducta", title="Distribución por Conducta", color_discrete_sequence=px.colors.sequential.Blues)
st.plotly_chart(graf_conducta, use_container_width=True)

# Distribución por Canal de Recepción
graf_canal = px.pie(df_2025, names="canal", title="Canales de Recepción", color_discrete_sequence=px.colors.sequential.Teal)
st.plotly_chart(graf_canal, use_container_width=True)

# Casos por Localidad
top_localidades = df_2025['localidad'].value_counts().nlargest(10).reset_index()
top_localidades.columns = ['localidad', 'casos']
graf_localidad = px.bar(top_localidades, x='localidad', y='casos', title="Top 10 Localidades con más casos", color='casos', color_continuous_scale='Mint')
st.plotly_chart(graf_localidad, use_container_width=True)

# Observaciones por mes (2025, gráfico de torta)
obs_por_mes_2025 = df_2025['mes_nombre'].value_counts().sort_index()
obs_por_mes_2025 = obs_por_mes_2025.reset_index()
obs_por_mes_2025.columns = ['mes_nombre', 'cantidad']

graf_pie_obs = px.pie(
    obs_por_mes_2025,
    names='mes_nombre',
    values='cantidad',
    title="📆 Distribución de observaciones registradas por mes (2025)",
    color_discrete_sequence=px.colors.sequential.Tealgrn
)
st.plotly_chart(graf_pie_obs, use_container_width=True)

# --- Exportar datos ---
st.download_button("📥 Descargar registros completos (CSV)", df_2025.to_csv(index=False).encode('utf-8'), file_name="registros_2025.csv", mime='text/csv')

# --- Reporte por EPS/Barrio ---
with st.expander("📄 Reportes resumidos por EPS/Barrio"):
    if st.button("Generar reporte por EPS"):
        st.dataframe(df_2025.groupby('eps').size().reset_index(name='casos'))
    if st.button("Generar reporte por Barrio"):
        st.dataframe(df_2025.groupby('barrio').size().reset_index(name='casos'))

st.markdown("---")
st.markdown("📌 **Notas:** Esta herramienta es de carácter exploratorio y no sustituye evaluación clínica.")
