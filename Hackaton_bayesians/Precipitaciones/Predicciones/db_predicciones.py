import os
import pandas as pd
import numpy as np
from pymongo import MongoClient
from sklearn.linear_model import LinearRegression
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime as dt
import re
from warnings import filterwarnings
filterwarnings('ignore')

# Configuración MongoDB
MONGO_URI = "mongodb+srv://dmaldonado07:qroprep@dbprep.xw7rrus.mongodb.net/?retryWrites=true&w=majority&appName=dbprep"
DB_NAME = "weather_data"

# Configuración visual
plt.style.use('seaborn-v0_8-darkgrid')
COLORS = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728']

# Estructura de estaciones por municipio
MUNICIPIOS_ESTACIONES = {
    "Querétaro": [
        "22027_QUERÉTARO",
        "22041_QUERÉTARO",
        "22045_QUERÉTARO"
    ],
    "San Juan del Rio": ["22028_SAN_JUAN_DEL_RÍO"],
    "Cadereyta": [
        "22005_CADEREYTA_DE_MONTES",
        "22021_CADEREYTA_DE_MONTES",
        "22035_CADEREYTA_DE_MONTES",
        "22054_CADEREYTA_DE_MONTES",
        "22056_CADEREYTA_DE_MONTES"
    ],
    "Arroyo Seco": ["22036_ARROYO_SECO"]
}

def clean_precip(value):
    """Limpieza especializada para precipitación"""
    if isinstance(value, str):
        value = re.sub(r'[^0-9.-]', '', value)
        if value.strip() in ('', 'NULO'):
            return np.nan
    try:
        val = float(value)
        return val if val >= 0 else np.nan
    except:
        return np.nan

def get_annual_data(df):
    """Procesamiento anual robusto con validación"""
    df['FECHA'] = pd.to_datetime(df['FECHA'], errors='coerce', dayfirst=True)
    df = df[df['FECHA'].notna()].copy()
    
    if df.empty:
        return pd.DataFrame()
    
    # Filtrado temporal (últimos 5 años)
    cutoff_date = dt.now().year - 5
    df = df[df['FECHA'].dt.year >= cutoff_date]
    
    # Limpieza y agrupación anual
    df['PRECIP'] = df['PRECIP'].apply(clean_precip).clip(0, 1000)
    df['Año'] = df['FECHA'].dt.year
    
    annual = df.groupby('Año')['PRECIP'].agg(['mean', 'std', 'count']).reset_index()
    annual.columns = ['Año', 'Media', 'Desviacion', 'Muestras']
    
    # Filtrado de calidad: mínimo 300 días de datos por año
    return annual[annual['Muestras'] >= 300]

def plot_municipio(data, municipio, color):
    """Generación de gráfica para un municipio"""
    if data.empty:
        return None
    
    model = LinearRegression()
    X = data[['Año']]
    y = data['Media']
    model.fit(X, y)
    
    # Predicción 2020-2028
    future_years = np.arange(data['Año'].min(), 2029).reshape(-1, 1)
    predicciones = model.predict(future_years)
    
    # Configuración de la curva
    plt.plot(future_years, predicciones, '--', 
            color=color, alpha=0.7, 
            label=f'{municipio}')
    
    # Datos reales con intervalos
    plt.errorbar(data['Año'], data['Media'], 
                yerr=data['Desviacion'], fmt='o',
                color=color, markersize=6, capsize=4,
                linewidth=2)
    
    return model

def main():
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    
    plt.figure(figsize=(14, 8))
    
    for idx, (municipio, estaciones) in enumerate(MUNICIPIOS_ESTACIONES.items()):
        print(f"\nProcesando: {municipio}")
        
        all_data = []
        for estacion in estaciones:
            try:
                docs = db[estacion].find(
                    {}, 
                    {'_id': 0, 'FECHA': 1, 'PRECIP': 1}
                )
                df = pd.DataFrame(list(docs))
                annual = get_annual_data(df)
                if not annual.empty:
                    all_data.append(annual)
            except Exception as e:
                print(f"Error en {estacion}: {str(e)}")
                continue
        
        if not all_data:
            continue
        
        # Combinar datos de todas las estaciones del municipio
        combined = pd.concat(all_data).groupby('Año').mean().reset_index()
        
        # Generar gráfica
        model = plot_municipio(combined, municipio, COLORS[idx % len(COLORS)])
        
        # Anotación estadística
        last_year = combined['Año'].max()
        text = (f"{municipio}\n"
                f"Tendencia: {model.coef_[0]:.1f} mm/año\n"
                f"R²: {model.score(combined[['Año']], combined['Media']):.2f}")
        
        # Posición dinámica de anotaciones
        offset_x = idx * 0.25
        offset_y = -idx * 5  # Offset vertical inverso
        
        plt.annotate(text, 
                    xy=(last_year + 0.5, model.predict([[last_year + 0.5]])[0]),
                    xytext=(last_year + 2.0 + offset_x, model.predict([[last_year]])[0] + offset_y),
                    arrowprops=dict(arrowstyle="->", color=COLORS[idx % len(COLORS)], alpha=0.7),
                    fontsize=9,
                    bbox=dict(boxstyle="round,pad=0.3", fc="white", ec=COLORS[idx % len(COLORS)], lw=1, alpha=0.8))

    # Personalización final
    plt.title('Precipitación Anual y Proyecciones 2020-2028\nRegión de Querétaro', 
             fontsize=16, pad=20, fontweight='bold')
    plt.xlabel('Año', fontsize=12)
    plt.ylabel('Precipitación Media (mm)', fontsize=12)
    plt.xticks(np.arange(2020, 2029, 1), rotation=45)
    plt.grid(alpha=0.4, linestyle='--')
    
    # Leyenda horizontal arriba
    plt.legend(
        loc='lower center',
        bbox_to_anchor=(0.5, 1.15),  # 1.15 posiciona arriba del gráfico
        ncol=len(MUNICIPIOS_ESTACIONES),
        frameon=True,
        shadow=True,
        fontsize=10,
        title='Municipios',
        title_fontsize=12
    )
    
    plt.tight_layout()
    plt.subplots_adjust(top=0.85)  # Espacio para la leyenda
    
    # Guardar y mostrar
    plt.savefig('precipitacion_municipios.png', dpi=300, bbox_inches='tight')
    plt.show()
    
    client.close()

if __name__ == "__main__":
    main()