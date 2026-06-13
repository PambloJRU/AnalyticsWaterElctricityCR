import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from api import obtener_datos_calidad


def _graficar_carta_c(df, empresa, sigma=3):
    meses_orden = {'Enero':1, 'Febrero':2, 'Marzo':3, 'Abril':4, 'Mayo':5, 'Junio':6,
                   'Julio':7, 'Agosto':8, 'Setiembre':9, 'Septiembre':9, 'Octubre':10, 'Noviembre':11, 'Diciembre':12}

    df_empresa = df[df['empresa'] == empresa].copy()
    df_empresa['mes_limpio'] = df_empresa['mes'].astype(str).str.strip()
    df_empresa['mes_num'] = df_empresa['mes_limpio'].map(meses_orden)
    df_empresa = df_empresa.sort_values('mes_num')
    df_empresa['cqpcp'] = pd.to_numeric(df_empresa['cqpcp'], errors='coerce').fillna(0)

    c_mean = df_empresa['cqpcp'].mean()
    lsc = c_mean + sigma * np.sqrt(c_mean)
    lic = max(0, c_mean - sigma * np.sqrt(c_mean))

    fuera_de_control = df_empresa[df_empresa['cqpcp'] > lsc]

    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(df_empresa['mes_limpio'], df_empresa['cqpcp'], marker='o', color='#1f77b4', linewidth=2, label='Quejas x Calidad (c)')

    ax.axhline(c_mean, color='green', linestyle='-', label=f'LC (Media: {c_mean:.1f})')
    ax.axhline(lsc, color='red', linestyle='--', alpha=0.7, label=f'LSC ({lsc:.1f})')
    ax.axhline(lic, color='red', linestyle='--', alpha=0.7, label=f'LIC ({lic:.1f})')

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


def render_control_calidad():
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
                fig_control, df_anomalias, media_c, limite_sup = _graficar_carta_c(df_calidad, empresa_seleccionada, sigma)
                st.pyplot(fig_control)

                if df_anomalias.empty:
                    st.success(f"✅ **Proceso en Control:** Durante el {anio_calidad}, la empresa {empresa_seleccionada} mantuvo sus quejas dentro del límite estadístico esperado (Máx aceptable: {limite_sup:.0f} quejas/mes).")
                else:
                    meses_criticos = ", ".join(df_anomalias['mes_limpio'].tolist())
                    st.error(f"❌ **Proceso Fuera de Control:** Se detectó inestabilidad en la red. El Límite Superior de Control (LSC) fue superado en los meses de: **{meses_criticos}**.")

                    st.markdown("**Propuesta de Mejora (Recomendación para Reporte):**")
                    st.warning(f"Se requiere solicitar a ARESEP una auditoría técnica sobre la infraestructura de {empresa_seleccionada} durante los meses de {meses_criticos}, para identificar las causas raíz (fenómenos climáticos, fallas de transformadores, etc.) que generaron un volumen de quejas atípico, superior al límite de {limite_sup:.0f}.")
