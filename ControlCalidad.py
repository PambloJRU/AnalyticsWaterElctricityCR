import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from api import obtener_datos_calidad

def _graficar_carta_c_historica(df, empresa, sigma=3):
    # Filtrar por empresa
    df_empresa = df[df['empresa'] == empresa].copy()
    
    # Limpiar el texto del mes y capitalizar (ej. 'junio   ' -> 'Junio')
    df_empresa['mes_limpio'] = df_empresa['mes'].astype(str).str.strip().str.capitalize()
    
    # Mapeo para ordenar los semestres correctamente
    meses_orden = {'Junio': 1, 'Diciembre': 2}
    df_empresa['orden_semestre'] = df_empresa['mes_limpio'].map(meses_orden)
    
    # Ordenar cronológicamente por año y luego por semestre
    df_empresa = df_empresa.sort_values(['anho', 'orden_semestre'])
    
    # Crear una etiqueta clara para el eje X (Ej. "2021 - Junio")
    df_empresa['Periodo'] = df_empresa['anho'].astype(str) + " - " + df_empresa['mes_limpio']
    
    df_empresa['cqpcp'] = pd.to_numeric(df_empresa['cqpcp'], errors='coerce').fillna(0)
    
    # Matemática de Gráfica C
    c_mean = df_empresa['cqpcp'].mean()
    lsc = c_mean + sigma * np.sqrt(c_mean)
    lic = max(0, c_mean - sigma * np.sqrt(c_mean)) # LIC no puede ser negativo
    
    # Identificar puntos anómalos
    fuera_de_control = df_empresa[df_empresa['cqpcp'] > lsc]
    
    # Graficar
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(df_empresa['Periodo'], df_empresa['cqpcp'], marker='o', color='#1f77b4', linewidth=2, label='Quejas Semestrales (c)')
    
    ax.axhline(c_mean, color='green', linestyle='-', label=f'LC (Media: {c_mean:.1f})')
    ax.axhline(lsc, color='red', linestyle='--', alpha=0.7, label=f'LSC ({lsc:.1f})')
    ax.axhline(lic, color='red', linestyle='--', alpha=0.7, label=f'LIC ({lic:.1f})')
    
    if not fuera_de_control.empty:
        ax.scatter(fuera_de_control['Periodo'], fuera_de_control['cqpcp'], color='red', s=150, zorder=5, label='Fuera de Control (Anomalía)')
        
    ax.set_title(f"Gráfica C Histórica (Semestral): Calidad de Tensión - {empresa}", fontsize=14)
    ax.set_xlabel('Semestres Evaluados (2020 - 2023)', fontsize=10)
    ax.set_ylabel('Cantidad de Quejas', fontsize=10)
    plt.xticks(rotation=45)
    ax.legend(loc='best')
    ax.grid(True, linestyle=':', alpha=0.5)
    plt.tight_layout()
    
    return fig, fuera_de_control, c_mean, lsc

def render_control_calidad2():
    st.header("Control Estadístico de Calidad (Distribución de Poisson)")
    st.markdown("Monitoreo **semestral histórico** de Quejas por Problemas de Calidad de Tensión e Interrupciones.")
    
    col_izq, col_der = st.columns([1, 3])
    
    with col_izq:
        st.info("Descargando histórico (2018-2023)...")
        anios = [2018,2019,2020, 2021, 2022, 2023]
        dfs = []
        for anio in anios:
            df_temp = obtener_datos_calidad(anio)
            if df_temp is not None:
                dfs.append(df_temp)
                
                
        if dfs:

            df_completo = pd.concat(dfs, ignore_index=True)
            lista_empresas = df_completo['empresa'].unique().tolist()
            empresa_seleccionada = st.selectbox("Seleccione la Empresa:", lista_empresas)
            
            st.markdown("---")
            sigma = st.slider("Nivel de Control (Sigma - $\sigma$):", min_value=1.0, max_value=4.0, value=3.0, step=0.5)
            st.caption("Nota: El estándar industrial (y el enseñado en el curso) es $3\sigma$ para calcular LSC y LIC.")
            
    with col_der:
        if dfs:
            with st.spinner("Procesando límites de control..."):
                fig_control, df_anomalias, media_c, limite_sup = _graficar_carta_c_historica(df_completo, empresa_seleccionada, sigma)
                st.pyplot(fig_control)
                
                if df_anomalias.empty:
                    st.success(f"✅ **Proceso en Control:** En el periodo histórico, la empresa {empresa_seleccionada} mantuvo sus quejas dentro del límite estadístico esperado (Máx aceptable: {limite_sup:.0f} quejas/semestre).")
                else:
                    periodos_criticos = ", ".join(df_anomalias['Periodo'].tolist())
                    st.error(f"❌ **Proceso Fuera de Control:** Se detectó inestabilidad en la red. El Límite Superior de Control (LSC) fue superado en los periodos: **{periodos_criticos}**.")
                    
                    st.markdown("**Propuesta de Mejora (Recomendación para Reporte):**")
                    st.warning(f"Se requiere solicitar a ARESEP una auditoría técnica sobre la infraestructura de {empresa_seleccionada} durante los semestres de {periodos_criticos}, para identificar las causas que generaron un volumen atípico.")