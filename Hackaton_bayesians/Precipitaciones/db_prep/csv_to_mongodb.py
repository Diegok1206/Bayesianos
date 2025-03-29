import os
import pandas as pd
from pymongo import MongoClient

# MongoDB connection URI y nombre de la base de datos
MONGO_URI = "mongodb+srv://dmaldonado07:qroprep@dbprep.xw7rrus.mongodb.net/?retryWrites=true&w=majority&appName=dbprep"
DB_NAME = "weather_data"

# Directorio que contiene los archivos CSV
CSV_DIR = r"C:\Programacion\Hackaton\Datos_prep_csv"

def insert_csv_to_mongodb(file_path):
    # Leer datos del CSV:
    # - Se omiten las primeras 20 filas.
    # - Se leen solo las columnas de la A a la E (usecols=[0,1,2,3,4]).
    # - Se toma como encabezado la fila 21 (header=0) y luego se reasignan los nombres.
    data = pd.read_csv(
        file_path,
        encoding='latin1',
        skiprows=20,
        header=0,
        usecols=[0,1,2,3,4],
        parse_dates=[0],
        dayfirst=True,
        infer_datetime_format=True
    )
    # Asignar de forma explícita los nombres de las columnas
    data.columns = ["FECHA", "PRECIP", "EVAP", "TMAX", "TMIN"]
    
    # Conectar a MongoDB y obtener la base de datos
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    
    # Usar como nombre de colección el nombre del archivo sin extensión
    collection_name = os.path.splitext(os.path.basename(file_path))[0]
    collection = db[collection_name]
    
    # Convertir el DataFrame a diccionarios e insertar los registros
    records = data.to_dict("records")
    if records:
        collection.insert_many(records)
        print(f"Inserted {len(records)} records into collection '{collection_name}'.")
    else:
        print(f"No records found in {file_path}.")
    
    client.close()

def main():
    # Procesar todos los archivos CSV en el directorio
    for file_name in os.listdir(CSV_DIR):
        if file_name.endswith(".csv"):
            file_path = os.path.join(CSV_DIR, file_name)
            print(f"Processing CSV file: {file_name}")
            insert_csv_to_mongodb(file_path)

if __name__ == "__main__":
    main()