import streamlit as st
import requests
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import linprog
import warnings
warnings.filterwarnings('ignore')


#  CONFIGURACIÓN DE LA PÁGINA

st.set_page_config(page_title="Dashboard ARESEP", layout="wide", page_icon="⚡")
st.title("📊 Dashboard Analítico ARESEP: Servicios Públicos")
st.markdown("Plataforma interactiva para el análisis cuantitativo de datos de agua y electricidad en Costa Rica.")

# 2. FUNCIONES DE CONEXIÓN A API (CON CACHÉ)

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


# FUNCIONES DE CÁLCULO Y GRÁFICOS

def graficar_modelos_cuantitativos(serie_historica, promedio_movil, reg_hist, reg_futura, titulo, ylabel):
    fig, ax = plt.subplots(figsize=(10, 4))
    
    # datos Reales Históricos (Gris claro para que sirva de fondo)
    ax.plot(serie_historica.index, serie_historica.values, label='Histórico (Real)', color='gray', alpha=0.5, linewidth=1.5)
    
    # Promedio Móvil (Verde)
    ax.plot(promedio_movil.index, promedio_movil.values, label='Promedio Móvil', color='#2ca02c', linewidth=2.5)
    
    # Regresión Lineal Histórica (Azul)
    ax.plot(reg_hist.index, reg_hist.values, label='Tendencia (Regresión)', color='#1f77b4', linestyle='-.', alpha=0.8)
    
    # Proyección Futura por Regresión (Rojo)
    ax.plot(reg_futura.index, reg_futura.values, label='Pronóstico (Regresión Lineal)', color='#d62728', linestyle='--', linewidth=2.5)
    
    ax.set_title(titulo, fontsize=14)
    ax.set_xlabel('Fecha', fontsize=10)
    ax.set_ylabel(ylabel, fontsize=10)
    ax.legend(loc='best')
    ax.grid(True, linestyle=':', alpha=0.7)
    plt.tight_layout()
    return fig

def optimizar_energia(df, demanda_objetivo):
    df_limpio = df[df['empresa'] != 'TOTAL NACIONAL'].copy()
    df_agrupado = df_limpio.groupby('empresa').agg({
        'precioMedioConCVG': 'mean', 
        'ventas': 'sum'
    }).reset_index().sort_values('precioMedioConCVG').reset_index(drop=True)
    
    empresas = df_agrupado['empresa'].tolist()
    costos = df_agrupado['precioMedioConCVG'].tolist()
    capacidades = df_agrupado['ventas'].tolist()
    
    c = np.array(costos)
    A_eq = np.ones((1, len(empresas)))
    b_eq = np.array([demanda_objetivo])
    limites = [(0, cap) for cap in capacidades]
    
    resultado = linprog(c, A_eq=A_eq, b_eq=b_eq, bounds=limites, method='highs')
    return resultado, empresas, costos, capacidades

# 4. ESTRUCTURA DE PESTAÑAS (TABS)

tab_pronosticos, tab_optimizacion = st.tabs(["📈 Pronósticos y Análisis de Tendencia", "⚙️ Optimización de Costos (Prog. Lineal)"])


# PESTAÑA 1: PRONÓSTICOS (REGRESIÓN Y PROMEDIOS MÓVILES)

with tab_pronosticos:
    st.header("Análisis de Tendencias y Pronósticos")
    st.markdown("Implementación de métodos cuantitativos: **Promedios Móviles** y **Regresión Lineal Simple** para la proyección de demanda.")
    
    # Control interactivo para el Promedio Móvil
    n_ventana = st.slider("Seleccione los periodos (meses) para el cálculo del Promedio Móvil (n):", min_value=2, max_value=12, value=6, step=1)
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    periodos_a_proyectar = 12 # Proyectar 1 año hacia el futuro
    
    #  Electricidad 
    with col1:
        st.subheader("Demanda Eléctrica")
        URL_ELEC = "https://datos.aresep.go.cr/ws.datosabiertos/Services/IE/Electricidad.svc/ObtenerGeneracionDemandaMaximaElectricidad"
        with st.spinner('Procesando Regresión Lineal...'):
            df_elec = obtener_datos_api(URL_ELEC)
            if df_elec is not None:
                # Limpieza de fechas
                df_elec['Fecha'] = pd.to_datetime(df_elec['anho'].astype(str) + '-' + df_elec['id_Mes'].astype(str) + '-01')
                ts_elec = df_elec.sort_values('Fecha').set_index('Fecha')['demandaMaxima']
                ts_elec.index = ts_elec.index.to_period('M').to_timestamp()
                
                # Cálculo de Promedio Móvil
                pm_elec = ts_elec.rolling(window=n_ventana).mean()
                
                # Cálculo de Regresión Lineal (y = mx + b)
                x_num = np.arange(len(ts_elec))
                coeficientes = np.polyfit(x_num, ts_elec.values, 1) # 1 indica grado lineal
                ecuacion_recta = np.poly1d(coeficientes)
                reg_hist_elec = pd.Series(ecuacion_recta(x_num), index=ts_elec.index)
                
                # Proyección Futura
                x_futuro = np.arange(len(ts_elec), len(ts_elec) + periodos_a_proyectar)
                fechas_futuras = pd.date_range(start=ts_elec.index[-1] + pd.DateOffset(months=1), periods=periodos_a_proyectar, freq='MS')
                reg_fut_elec = pd.Series(ecuacion_recta(x_futuro), index=fechas_futuras)
                
                # Graficar
                fig_elec = graficar_modelos_cuantitativos(ts_elec, pm_elec, reg_hist_elec, reg_fut_elec, "Análisis de Demanda Máxima (MW)", "MW")
                st.pyplot(fig_elec)
                
                # Mostrar ecuación al usuario
                st.info(f"**Ecuación de Regresión:** y = {coeficientes[0]:.2f}x + {coeficientes[1]:.2f}")
    
    #  Agua 
    with col2:
        st.subheader("Producción de Agua")
        URL_AGUA = "https://datos.aresep.go.cr/ws.datosabiertos/Services/IA/AguaPotable.svc/ObtenerHistoricoTarifarioProduccionAguaPotable"
        with st.spinner('Procesando Regresión Lineal...'):
            df_agua = obtener_datos_api(URL_AGUA)
            if df_agua is not None:
                # Limpieza de fechas
                df_agua['Fecha'] = pd.to_datetime(df_agua['fecha'])
                ts_agua = df_agua.groupby('Fecha')['produccion'].sum()
                ts_agua.index = ts_agua.index.to_period('M').to_timestamp()
                
                # Cálculo de Promedio Móvil
                pm_agua = ts_agua.rolling(window=n_ventana).mean()
                
                # Cálculo de Regresión Lineal
                x_num = np.arange(len(ts_agua))
                coeficientes = np.polyfit(x_num, ts_agua.values, 1)
                ecuacion_recta = np.poly1d(coeficientes)
                reg_hist_agua = pd.Series(ecuacion_recta(x_num), index=ts_agua.index)
                
                # Proyección Futura
                x_futuro = np.arange(len(ts_agua), len(ts_agua) + periodos_a_proyectar)
                fechas_futuras = pd.date_range(start=ts_agua.index[-1] + pd.DateOffset(months=1), periods=periodos_a_proyectar, freq='MS')
                reg_fut_agua = pd.Series(ecuacion_recta(x_futuro), index=fechas_futuras)
                
                # Graficar
                fig_agua = graficar_modelos_cuantitativos(ts_agua, pm_agua, reg_hist_agua, reg_fut_agua, "Análisis de Prod. Neta Agua", "Metros Cúbicos")
                st.pyplot(fig_agua)
                
                # Mostrar ecuación 
                st.info(f"**Ecuación de Regresión:** y = {coeficientes[0]:.2f}x + {coeficientes[1]:.2f}")

# PESTAÑA 2: OPTIMIZACIÓN DE COSTOS 

with tab_optimizacion:
    st.header("Minimización de Costos de Abastecimiento")
    col_controles, col_resultados = st.columns([1, 2])
    
    with col_controles:
        anio_seleccionado = st.selectbox("Seleccione el Año Base:", [2024, 2025, 2026])
        df_tarifas = obtener_datos_tarifas(anio_seleccionado)
        
        if df_tarifas is not None:
            df_temporal = df_tarifas[df_tarifas['empresa'] != 'TOTAL NACIONAL']
            capacidad_total = int(df_temporal['ventas'].sum())
            st.markdown("---")
            demanda_objetivo = st.slider("Demanda Objetivo a Satisfacer:", min_value=int(capacidad_total * 0.1), max_value=capacidad_total, value=int(capacidad_total * 0.6), step=50000)
            st.info(f"Capacidad Máxima Nacional Instalada: **{capacidad_total:,.0f}**")
            
    with col_resultados:
        if df_tarifas is not None:
            resultado, empresas, costos, capacidades = optimizar_energia(df_tarifas, demanda_objetivo)

            if resultado.success:
                c1, c2 = st.columns(2)
                c1.metric("Demanda Satisfecha", f"{demanda_objetivo:,.0f} und")
                c2.metric("Costo Total Minimizado", f"₡ {resultado.fun:,.2f}")
                
                resultados_lista = []
                for i in range(len(empresas)):
                    asignacion = resultado.x[i]
                    resultados_lista.append({
                        "Empresa": empresas[i],
                        "Costo Unitario (₡)": round(costos[i], 2),
                        "Asignación Óptima": asignacion,
                        "Capacidad Libre": capacidades[i] - asignacion
                    })
                    
                df_res = pd.DataFrame(resultados_lista)
                st.bar_chart(df_res.set_index("Empresa")[["Asignación Óptima", "Capacidad Libre"]])
                with st.expander("Ver Desglose Operativo Completo"):
                    st.dataframe(df_res[["Empresa", "Costo Unitario (₡)", "Asignación Óptima"]], hide_index=True)
            else:
                st.error("❌ El modelo no encontró solución. Revise la demanda vs capacidad instalada.")