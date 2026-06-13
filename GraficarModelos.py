from matplotlib import pyplot as plt


def graficar_modelos_cuantitativos(serie_historica, promedio_movil, reg_hist, reg_futura, titulo, ylabel):
    fig, ax = plt.subplots(figsize=(10, 4))
    
    # datos Reales Históricos (Gris claro para que sirva de fondo)
    ax.plot(serie_historica.index, serie_historica.values, label='Histórico (Real)', color='gray', alpha=0.5, linewidth=1.5)
    
    # Promedio Móvil (Verde)
    ax.plot(promedio_movil.index, promedio_movil.values, label='Promedio Móvil', color='#2ca02c', linewidth=2.5)
    
    # Regresión Lineal Histórica (Azul)
    ax.plot(reg_hist.index, reg_hist.values, label='Tendencia (Regresión)', color="#51b1f6", linestyle='-.', alpha=0.8)
    
    # Proyección Futura por Regresión (Rojo)
    ax.plot(reg_futura.index, reg_futura.values, label='Pronóstico (Regresión Lineal)', color='#d62728', linestyle='--', linewidth=2.5)
    
    ax.set_title(titulo, fontsize=14)
    ax.set_xlabel('Fecha', fontsize=10)
    ax.set_ylabel(ylabel, fontsize=10)
    ax.legend(loc='best')
    ax.grid(True, linestyle=':', alpha=0.7)
    plt.tight_layout()
    return fig