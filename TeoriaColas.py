import streamlit as st
import pandas as pd
from api import obtener_datos_calidad

def calcular_M_M_1(lam, mu):
    """Calcula las métricas de un modelo de colas M/M/1"""
    if mu <= lam:
        return None # El sistema es inestable, la cola crecería al infinito
    
    rho = lam / mu                      # Factor de utilización del sistema
    lq = (lam ** 2) / (mu * (mu - lam)) # Número esperado en la cola (Quejas rezagadas)
    ls = lam / (mu - lam)               # Número esperado en el sistema
    wq = lam / (mu * (mu - lam))        # Tiempo esperado en la cola (Días)
    ws = 1 / (mu - lam)                 # Tiempo esperado en el sistema (Días)
    
    return rho, lq, ls, wq, ws

def render_teoria_colas():
    st.header("Análisis de Teoría de Colas (M/M/1)")
    st.markdown("Evaluación del sistema de atención de quejas para optimizar la tasa de servicio (**$\mu$**) y reducir la cantidad de quejas en espera (**$L_q$**).")
    
    col_izq, col_der = st.columns([1, 2])
    
    with col_izq:
        anio_evaluacion = st.selectbox("Seleccione el Año Histórico:", [2021, 2022, 2023, 2024], index=1, key="anio_colas")
        df_calidad = obtener_datos_calidad(anio_evaluacion)
        
        if df_calidad is not None:
            # Limpiar datos para sacar el total general de quejas (cqcp)
            df_calidad['cqcp'] = pd.to_numeric(df_calidad['cqcp'], errors='coerce').fillna(0)
            
            empresas = df_calidad['empresa'].unique().tolist()
            empresa_sel = st.selectbox("Seleccione la Empresa a Evaluar:", empresas, key="empresa_colas")
            
            # Calcular la tasa de llegada real basada en datos históricos
            df_empresa = df_calidad[df_calidad['empresa'] == empresa_sel]
            promedio_quejas_mes = df_empresa['cqcp'].mean()
            lam_calculado = promedio_quejas_mes / 30  # Promedio de quejas por DÍA
            
            st.info(f"**Tasa de Llegada Real ($\lambda$):**\n\nEl promedio histórico indica que **{empresa_sel}** recibe **{lam_calculado:.2f} quejas al día**.")
            
            st.markdown("---")
            st.markdown("**Propuesta de Mejora:**")
            mu_propuesto = st.slider("Capacidad de Resolución Diaria ($\mu$):", 
                                     min_value=float(lam_calculado + 0.1), 
                                     max_value=float(lam_calculado * 5), 
                                     value=float(lam_calculado * 1.5), 
                                     step=0.5,
                                     help="Mueva este control para simular qué pasaría si la empresa contrata más personal o mejora sus procesos.")
            
    with col_der:
        if df_calidad is not None:
            resultados = calcular_M_M_1(lam_calculado, mu_propuesto)
            
            if resultados:
                rho, lq, ls, wq, ws = resultados
                
                st.subheader("Métricas de Desempeño del Sistema")
                
                # Fila 1 de métricas
                c1, c2, c3 = st.columns(3)
                c1.metric(label="Factor de Utilización (ρ)", value=f"{rho*100:.1f} %", help="Porcentaje del tiempo que el equipo de atención está ocupado.")
                c2.metric(label="Quejas en Espera ($L_q$)", value=f"{lq:.1f} quejas", delta=f"Optimizado", delta_color="normal")
                c3.metric(label="Quejas en Sistema ($L_s$)", value=f"{ls:.1f} quejas")
                
                # Fila 2 de métricas
                c4, c5 = st.columns(2)
                c4.metric(label="Días en Cola ($W_q$)", value=f"{wq:.2f} días", help="Tiempo que pasa una queja sin ser leída.")
                c5.metric(label="Tiempo Total de Resolución ($W_s$)", value=f"{ws:.2f} días")
                
                st.markdown("---")
                # Conclusión 
                st.success(f"**Resultados:**\n\nAl establecer una tasa de servicio ($\mu$) de **{mu_propuesto:.1f} quejas resueltas por día**, la empresa {empresa_sel} mantendría su departamento ocupado el **{rho*100:.1f}%** del tiempo. Esto garantiza que la longitud de la cola se mantenga baja (aproximadamente **{lq:.1f} quejas rezagadas**), cumpliendo con los objetivos de mejora operativa establecidos.")
                
            else:
                st.error("El sistema es inestable. La capacidad de resolución ($\mu$) debe ser mayor a la tasa de llegada ($\lambda$).")