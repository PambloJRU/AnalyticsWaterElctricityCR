import streamlit as st
import requests
import pandas as pd


@st.cache_data
def obtener_datos_api(url):
    respuesta = requests.get(url)
    if respuesta.status_code == 200:
        return pd.DataFrame(respuesta.json()['value'])
    return None


@st.cache_data
def obtener_datos_tarifas(anio):
    url = f"https://datos.aresep.go.cr/ws.datosabiertos/Services/IE/TarifasElectricidad.svc/ObtenerTarifasPreciosMedios/{anio}"
    respuesta = requests.get(url)
    if respuesta.status_code == 200:
        return pd.DataFrame(respuesta.json()['value'])
    return None


@st.cache_data
def obtener_datos_calidad(anio):
    url = f"https://datos.aresep.go.cr/ws.datosabiertos/Services/IE/Electricidad.svc/ObtenerIndicadoresComercialesYQuejas/{anio}"
    respuesta = requests.get(url)
    if respuesta.status_code == 200:
        return pd.DataFrame(respuesta.json()['value'])
    return None
