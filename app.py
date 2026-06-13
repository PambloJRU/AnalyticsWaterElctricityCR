import streamlit as st
import requests
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import linprog
import warnings
from GraficarModelos import graficar_modelos_cuantitativos
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

@st.cache_data
def obtener_datos_calidad(anio):
    url = f"https://datos.aresep.go.cr/ws.datosabiertos/Services/IE/Electricidad.svc/ObtenerIndicadoresComercialesYQuejas/{anio}"
    respuesta = requests.get(url)
    if respuesta.status_code == 200:
        return pd.DataFrame(respuesta.json()['value'])
    return None


# FUNCIONES DE CÁLCULO Y GRÁFICOS



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

def graficar_carta_c(df, empresa, sigma=3):
    # Diccionario para ordenar cronológicamente (ARESEP trae espacios en los strings)
    meses_orden = {'Enero':1, 'Febrero':2, 'Marzo':3, 'Abril':4, 'Mayo':5, 'Junio':6, 
                   'Julio':7, 'Agosto':8, 'Setiembre':9, 'Septiembre':9, 'Octubre':10, 'Noviembre':11, 'Diciembre':12}
    
    # Limpieza de datos
    df_empresa = df[df['empresa'] == empresa].copy()
    df_empresa['mes_limpio'] = df_empresa['mes'].astype(str).str.strip()
    df_empresa['mes_num'] = df_empresa['mes_limpio'].map(meses_orden)
    df_empresa = df_empresa.sort_values('mes_num')
    df_empresa['cqpcp'] = pd.to_numeric(df_empresa['cqpcp'], errors='coerce').fillna(0)
    
    # Matemática de Gráfica C (Poisson)
    c_mean = df_empresa['cqpcp'].mean()
    lsc = c_mean + sigma * np.sqrt(c_mean)
    lic = max(0, c_mean - sigma * np.sqrt(c_mean)) # No puede haber quejas negativas
    
    # Identificar puntos fuera de control
    fuera_de_control = df_empresa[df_empresa['cqpcp'] > lsc]
    
    # Graficar
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(df_empresa['mes_limpio'], df_empresa['cqpcp'], marker='o', color='#1f77b4', linewidth=2, label='Quejas x Calidad (c)')
    
    # Líneas de control
    ax.axhline(c_mean, color='green', linestyle='-', label=f'LC (Media: {c_mean:.1f})')
    ax.axhline(lsc, color='red', linestyle='--', alpha=0.7, label=f'LSC ({lsc:.1f})')
    ax.axhline(lic, color='red', linestyle='--', alpha=0.7, label=f'LIC ({lic:.1f})')
    
    # Resaltar anomalías
    if not fuera_de_control.empty:
        ax.scatter(fuera_de_control['mes_limpio'], fuera_de_control['cqpcp'], color='red', s=150, zorder=5, label='Fuera de Control (Anomalía)')
        
    ax.set_title(f"Gráfica C: Control de Calidad de Tensión - {empresa}", fontsize=14)
    ax.set_xlabel('Meses del Año', fontsize=10)
    ax.set_ylabel('Cantidad de Quejas', fontsize=10)
    plt.xticks(rotation=45)
    ax.legend(loc='best')
    ax.grid(True, linestyle=':', alpha=0.5)
    plt.tight_layout()
    
    return fig, fuera_de_control, c_mean, lsc

# 4. ESTRUCTURA DE PESTAÑAS (TABS)

tab_pronosticos, tab_optimizacion, tab_control = st.tabs(["📈 Pronósticos y Análisis de Tendencia", 
                                             "⚙️ Optimización de Costos (Prog. Lineal)" ,
                                             "📉 Control de Calidad (Gráfica C)"])


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
                st.info(f"Registros desde el año 2000 hasta 2024 - Se proyecta hacia 2026")
    
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
                st.info(f"Registros desde el año 2010 hasta 2020 - Se proyecta hacia 2021-2022")

# PESTAÑA 2: OPTIMIZACIÓN DE COSTOS 

with tab_optimizacion:
    st.header("Minimización de Costos de Abastecimiento")
    col_controles, col_resultados = st.columns([1, 2])
    
    with col_controles:
        anio_seleccionado = st.selectbox("Seleccione el Año Base:", [2020,2021,2022,2023,2024, 2025, 2026])
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

#PESTAÑA 3: CONTROL ESTADÍSTICO DE CALIDAD

with tab_control:
    st.header("Control Estadístico de Calidad (Distribución de Poisson)")
    st.markdown("Monitoreo de **Quejas por Problemas de Calidad de Tensión e Interrupciones (cqpcp)** mediante **Gráficas C**.")
    
    col_izq, col_der = st.columns([1, 3])
    
    with col_izq:
        anio_calidad = st.selectbox("Seleccione el Año a Evaluar:", [2021, 2022, 2023, 2024], index=1)
        df_calidad = obtener_datos_calidad(anio_calidad)
        
        if df_calidad is not None:
            lista_empresas = df_calidad['empresa'].unique().tolist()
            empresa_seleccionada = st.selectbox("Seleccione la Empresa:", lista_empresas)
            
            st.markdown("---")
            sigma = st.slider("Nivel de Control (Sigma - $\sigma$):", min_value=1.0, max_value=4.0, value=3.0, step=0.5)
            st.caption("Nota: El estándar industrial (y el enseñado en el curso) es $3\sigma$ para calcular LSC y LIC.")
            
    with col_der:
        if df_calidad is not None:
            with st.spinner("Procesando límites de control..."):
                fig_control, df_anomalias, media_c, limite_sup = graficar_carta_c(df_calidad, empresa_seleccionada, sigma)
                st.pyplot(fig_control)
                
                # Evaluación automática y Toma de Decisiones
                if df_anomalias.empty:
                    st.success(f"✅ **Proceso en Control:** Durante el {anio_calidad}, la empresa {empresa_seleccionada} mantuvo sus quejas dentro del límite estadístico esperado (Máx aceptable: {limite_sup:.0f} quejas/mes).")
                else:
                    meses_criticos = ", ".join(df_anomalias['mes_limpio'].tolist())
                    st.error(f"❌ **Proceso Fuera de Control:** Se detectó inestabilidad en la red. El Límite Superior de Control (LSC) fue superado en los meses de: **{meses_criticos}**.")
                    
                    st.markdown("**Propuesta de Mejora (Recomendación para Reporte):**")
                    st.warning(f"Se requiere solicitar a ARESEP una auditoría técnica sobre la infraestructura de {empresa_seleccionada} durante los meses de {meses_criticos}, para identificar las causas raíz (fenómenos climáticos, fallas de transformadores, etc.) que generaron un volumen de quejas atípico, superior al límite de {limite_sup:.0f}.")