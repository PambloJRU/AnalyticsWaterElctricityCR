import streamlit as st
import pandas as pd
import numpy as np
from scipy.optimize import linprog
from api import obtener_datos_tarifas


def _optimizar_energia(df, demanda_objetivo):
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


def render_optimizacion():
    st.header("Minimización de Costos de Abastecimiento")
    col_controles, col_resultados = st.columns([1, 2])

    with col_controles:
        anio_seleccionado = st.selectbox("Seleccione el Año Base:", [2020, 2021, 2022, 2023, 2024, 2025, 2026])
        df_tarifas = obtener_datos_tarifas(anio_seleccionado)

        if df_tarifas is not None:
            df_temporal = df_tarifas[df_tarifas['empresa'] != 'TOTAL NACIONAL']
            capacidad_total = int(df_temporal['ventas'].sum())
            st.markdown("---")
            demanda_objetivo = st.slider("Demanda Objetivo a Satisfacer:", min_value=int(capacidad_total * 0.1), max_value=capacidad_total, value=int(capacidad_total * 0.6), step=50000)
            st.info(f"Capacidad Máxima Nacional Instalada: **{capacidad_total:,.0f}**")

    with col_resultados:
        if df_tarifas is not None:
            resultado, empresas, costos, capacidades = _optimizar_energia(df_tarifas, demanda_objetivo)

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
