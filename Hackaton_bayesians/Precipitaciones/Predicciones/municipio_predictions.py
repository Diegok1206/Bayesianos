import pandas as pd
import numpy as np
from pymongo import MongoClient
from sklearn.linear_model import LinearRegression
import matplotlib.pyplot as plt
import seaborn as sns
import re
from datetime import datetime as dt

# Configuración MongoDB
MONGO_URI = "mongodb+srv://dmaldonado07:qroprep@dbprep.xw7rrus.mongodb.net/?retryWrites=true&w=majority&appName=dbprep"
DB_NAME = "weather_data"

# Configuración estética
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("husl")

# Configuración de municipios
MUNICIPIOS = {
    "Querétaro": ["22027_QUERÉTARO", "22041_QUERÉTARO", "22045_QUERÉTARO"],
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

def procesar_datos(raw_data):
    """Limpieza y procesamiento de datos"""
    if not raw_data:
        return pd.DataFrame()
    
    df = pd.DataFrame(raw_data)
    
    try:
        # Conversión de fechas
        df['FECHA'] = pd.to_datetime(df['FECHA'], errors='coerce', dayfirst=True)
        df = df[df['FECHA'].dt.year.between(2018, 2023)].dropna(subset=['FECHA'])
        
        if df.empty:
            return pd.DataFrame()
        
        # Limpieza numérica
        df['PRECIP'] = (
            df['PRECIP']
            .replace(['NULO', ''], np.nan)
            .astype(float)
            .clip(0, 1000)
        )  # Added missing closing parenthesis
        
        # Agregación anual
        df['Año'] = df['FECHA'].dt.year
        annual = df.groupby('Año').agg(
            Precip_Media=('PRECIP', 'mean'),
            Precip_Std=('PRECIP', 'std'),
            Muestras=('PRECIP', 'count')
        ).query('Muestras >= 30').reset_index()
        
        return annual
    
    except Exception as e:
        print(f"Error en procesamiento: {str(e)}")
        return pd.DataFrame()

def generar_grafica_municipio(municipio, data):
    """Genera gráfico individual para un municipio"""
    plt.figure(figsize=(10, 6))
    
    try:
        # Modelado predictivo
        X = data['Año'].values.reshape(-1, 1)
        y = data['Precip_Media'].values
        
        model = LinearRegression()
        model.fit(X, y)
        
        # Generar predicción para 4 años
        ultimo_año = data['Año'].max()
        años_prediccion = np.arange(ultimo_año + 1, ultimo_año + 5)
        predicciones = model.predict(años_prediccion.reshape(-1, 1))
        
        # Configurar gráfico
        plt.errorbar(data['Año'], y, 
                    yerr=data['Precip_Std'], 
                    fmt='o', capsize=5, label='Datos históricos')
        plt.plot(años_prediccion, predicciones, 
                'r--', marker='s', label='Predicción')
        
        # Personalización
        plt.title(f'Precipitación en {municipio}\nTendencia: {model.coef_[0]:.1f} mm/año')
        plt.xlabel('Año', fontsize=12)
        plt.ylabel('Precipitación (mm)', fontsize=12)
        plt.xticks(np.arange(2018, 2028, 1), rotation=45)
        plt.grid(alpha=0.3)
        plt.legend()
        
        # Guardar
        nombre_archivo = f"precipitacion_{municipio.lower().replace(' ', '_')}.png"
        plt.tight_layout()
        plt.savefig(nombre_archivo, dpi=150)
        plt.close()
        print(f"✅ Gráfico generado: {nombre_archivo}")
        
    except Exception as e:
        print(f"⚠️ Error en {municipio}: {str(e)}")

def main():
    """Función principal"""
    client = None
    try:
        # Conexión a MongoDB con timeout
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        # Verify connection
        client.server_info()
        db = client[DB_NAME]
        print("✅ Conexión exitosa a MongoDB")
        
        # Procesar datos por municipio
        for municipio, estaciones in MUNICIPIOS.items():
            print(f"\n🔍 Procesando: {municipio}")
            datos = []
            
            for estacion in estaciones:
                try:
                    cursor = db[estacion].find(
                        {"FECHA": {"$regex": r"^\d{2}/\d{2}/(201[8-9]|202[0-3])"}},
                        {"FECHA": 1, "PRECIP": 1, "_id": 0}
                    )
                    raw_data = list(cursor)
                    
                    if not raw_data:
                        print(f"⚠️ {estacion} sin datos")
                        continue
                        
                    processed = procesar_datos(raw_data)
                    if not processed.empty:
                        datos.append(processed)
                except Exception as e:
                    print(f"🚨 Error en {estacion}: {str(e)}")
                    continue
            
            if datos:
                combined = pd.concat(datos).groupby('Año').mean().reset_index()
                generar_grafica_municipio(municipio, combined)
            else:
                print(f"❌ {municipio} sin datos válidos")
                
    except Exception as e:
        print(f"⛔ Error general: {str(e)}")
        return  # Exit if connection fails
    finally:
        if client:
            client.close()
            print("\n🔌 Conexión cerrada")

if __name__ == "__main__":
    main()