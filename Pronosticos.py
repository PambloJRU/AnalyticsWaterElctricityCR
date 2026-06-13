import streamlit as st
import pandas as pd
import numpy as np
from api import obtener_datos_api
from GraficarModelos import graficar_modelos_cuantitativos


def _calcular_pronosticos(ts, n_ventana, periodos_a_proyectar):
    pm = ts.rolling(window=n_ventana).mean()

    x_num = np.arange(len(ts))
    coeficientes = np.polyfit(x_num, ts.values, 1)
    ecuacion_recta = np.poly1d(coeficientes)
    reg_hist = pd.Series(ecuacion_recta(x_num), index=ts.index)

    x_futuro = np.arange(len(ts), len(ts) + periodos_a_proyectar)
    fechas_futuras = pd.date_range(start=ts.index[-1] + pd.DateOffset(months=1), periods=periodos_a_proyectar, freq='MS')
    reg_fut = pd.Series(ecuacion_recta(x_futuro), index=fechas_futuras)

    return pm, reg_hist, reg_fut, coeficientes


def render_pronosticos():
    st.header("Análisis de Tendencias y Pronósticos")
    st.markdown("Implementación de métodos cuantitativos: **Promedios Móviles** y **Regresión Lineal Simple** para la proyección de demanda.")

    n_ventana = st.slider("Seleccione los periodos (meses) para el cálculo del Promedio Móvil (n):", min_value=2, max_value=12, value=6, step=1)
    st.markdown("---")

    col1, col2 = st.columns(2)
    periodos_a_proyectar = 12

    with col1:
        st.subheader("Demanda Eléctrica")
        URL_ELEC = "https://datos.aresep.go.cr/ws.datosabiertos/Services/IE/Electricidad.svc/ObtenerGeneracionDemandaMaximaElectricidad"
        with st.spinner('Procesando Regresión Lineal...'):
            df_elec = obtener_datos_api(URL_ELEC)
            if df_elec is not None:
                df_elec['Fecha'] = pd.to_datetime(df_elec['anho'].astype(str) + '-' + df_elec['id_Mes'].astype(str) + '-01')
                ts_elec = df_elec.sort_values('Fecha').set_index('Fecha')['demandaMaxima']
                ts_elec.index = ts_elec.index.to_period('M').to_timestamp()

                pm_elec, reg_hist_elec, reg_fut_elec, coef_elec = _calcular_pronosticos(ts_elec, n_ventana, periodos_a_proyectar)

                fig_elec = graficar_modelos_cuantitativos(ts_elec, pm_elec, reg_hist_elec, reg_fut_elec, "Análisis de Demanda Máxima (MW)", "MW")
                st.pyplot(fig_elec)

                st.info(f"**Ecuación de Regresión:** y = {coef_elec[0]:.2f}x + {coef_elec[1]:.2f}")
                st.info(f"Registros desde el año 2000 hasta 2024 - Se proyecta hacia 2026")

    with col2:
        st.subheader("Producción de Agua")
        URL_AGUA = "https://datos.aresep.go.cr/ws.datosabiertos/Services/IA/AguaPotable.svc/ObtenerHistoricoTarifarioProduccionAguaPotable"
        with st.spinner('Procesando Regresión Lineal...'):
            df_agua = obtener_datos_api(URL_AGUA)
            if df_agua is not None:
                df_agua['Fecha'] = pd.to_datetime(df_agua['fecha'])
                ts_agua = df_agua.groupby('Fecha')['produccion'].sum()
                ts_agua.index = ts_agua.index.to_period('M').to_timestamp()

                pm_agua, reg_hist_agua, reg_fut_agua, coef_agua = _calcular_pronosticos(ts_agua, n_ventana, periodos_a_proyectar)

                fig_agua = graficar_modelos_cuantitativos(ts_agua, pm_agua, reg_hist_agua, reg_fut_agua, "Análisis de Prod. Neta Agua", "Metros Cúbicos")
                st.pyplot(fig_agua)

                st.info(f"**Ecuación de Regresión:** y = {coef_agua[0]:.2f}x + {coef_agua[1]:.2f}")
                st.info(f"Registros desde el año 2010 hasta 2020 - Se proyecta hacia 2021-2022")
