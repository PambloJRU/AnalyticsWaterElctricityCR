import streamlit as st
from Pronosticos import render_pronosticos
from Optimizacion import render_optimizacion
from ControlDeCalidad import render_control_calidad
from TeoriaColas import render_teoria_colas

st.set_page_config(page_title="Dashboard ARESEP", layout="wide", page_icon="⚡")
st.title("Dashboard Analítico ARESEP: Servicios Públicos")
st.markdown("Plataforma interactiva para el análisis cuantitativo de datos de agua y electricidad en Costa Rica.")

tab_pronosticos, tab_optimizacion, tab_control, tab_colas = st.tabs([
    "Pronósticos y Análisis de Tendencia",
    "Optimización de Costos (Prog. Lineal)",
    "Control de Calidad (Gráfica C)",
    "Análisis de Líneas de Espera (Colas)"
])

with tab_pronosticos:
    render_pronosticos()

with tab_optimizacion:
    render_optimizacion()

with tab_control:
    render_control_calidad()

with tab_colas:
    render_teoria_colas()
