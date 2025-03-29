from google.colab import drive  # Importación añadida
import pandas as pd
import numpy as np
import folium
import geopandas as gpd
import ipywidgets as widgets
from IPython.display import display
from datetime import datetime
import json
import unicodedata
import os
import cv2
from pathlib import Path

# === Montar Google Drive ===
drive.mount('/content/drive')  # Nueva sección añadida

# === Configuración ===
COORDENADAS_QUERETARO = [20.5888, -100.3899]
NIVELES_SEQUIA = {
    0: "Sin Sequía",
    1: "Leve",
    2: "Moderada",
    3: "Severa",
    4: "Crítica",
    5: "Extrema"
}

def normalizar_texto(texto):
    texto = str(texto).lower().strip()
    sustituciones = {
        'amealco de bonfil': 'amealco',
        'amealco_de_bonfil': 'amealco',
        'amealco bonfil': 'amealco',
        'amealco_bonfil': 'amealco',
        'amealco de bonfin': 'amealco',
        'amealco_de_bonfin': 'amealco',
        'san joaquín': 'san_joaquin',
        'cadereyta de montes': 'cadereyta'
    }
    texto = sustituciones.get(texto, texto)
    texto = unicodedata.normalize('NFKD', texto)\
           .encode('ASCII', 'ignore')\
           .decode('ASCII')\
           .replace(' ', '_').replace('-', '_').replace("'", "")
    return texto

# === Carga de datos desde Google Drive ===
df_raw = pd.read_excel('/content/drive/MyDrive/Base_de_Datos_Querétaro.xlsx', header=None)

municipios = df_raw.iloc[4, 2:20].tolist()
datos = df_raw.iloc[10:802, 2:20]
fechas = pd.to_datetime(df_raw.iloc[10:802, 1].values, errors='coerce')

df_limpio = pd.DataFrame(datos.values, columns=municipios)
df_limpio['Fecha'] = fechas

df_long = pd.melt(df_limpio, id_vars=['Fecha'],
                 var_name='Municipio', value_name='Magnitud')
df_long['Magnitud'] = pd.to_numeric(df_long['Magnitud'], errors='coerce').fillna(0).astype(int)
df_long['Fecha_str'] = df_long['Fecha'].dt.strftime('%Y-%m')
df_long['Municipio_Norm'] = df_long['Municipio'].apply(normalizar_texto)

# Cargar y preparar GeoJSON desde Google Drive
gdf = gpd.read_file('/content/drive/MyDrive/22_Queretaro.json')
gdf['NAME_2_Norm'] = gdf['NAME_2'].apply(normalizar_texto)

# === Función principal mejorada ===
def generar_mapa_sequia(fecha_str):
    try:
        fecha_dt = datetime.strptime(fecha_str, '%Y-%m')
        año, mes = fecha_dt.year, fecha_dt.month

        df_filtrado = df_long[
            (df_long['Fecha'].dt.year == año) &
            (df_long['Fecha'].dt.month == mes)
        ].copy()

        # Verificación especial para Amealco
        amealco_data = df_filtrado[df_filtrado['Municipio_Norm'] == 'amealco']
        if not amealco_data.empty:
            print(f"Datos actuales de Amealco - Magnitud: {amealco_data['Magnitud'].values[0]}")

        # Merge con verificación explícita
        df_merge = df_filtrado.groupby('Municipio_Norm', as_index=False)['Magnitud'].first()

        # Debugging: Verificar nombres
        print("\nNombres en datos:", df_merge['Municipio_Norm'].unique())
        print("Nombres en GeoJSON:", gdf['NAME_2_Norm'].unique())

        gdf_mapa = gdf.merge(
            df_merge,
            left_on='NAME_2_Norm',
            right_on='Municipio_Norm',
            how='left'
        )

        # Debugging: Verificar merge
        amealco_merged = gdf_mapa[gdf_mapa['NAME_2_Norm'] == 'amealco']
        print("\nDatos mergeados de Amealco:", amealco_merged[['NAME_2', 'Magnitud']].values)

        # Manejo de valores faltantes
        gdf_mapa['Magnitud'] = gdf_mapa['Magnitud'].fillna(0).astype(int)

        # Crear mapa
        m = folium.Map(location=COORDENADAS_QUERETARO, zoom_start=8, tiles='cartodb positron')

        colormap = folium.LinearColormap(
            colors=["#4dc4f0", "#00FF00", "#FFFF00", "#FFA500", "#FF0000", "#8B0000"],
            index=[0, 1, 2, 3, 4, 5],
            vmin=0,
            vmax=5
        )

        # Capa GeoJSON con estilos dinámicos
        folium.GeoJson(
            json.loads(gdf_mapa.to_json()),
            style_function=lambda feature: {
                'fillColor': colormap(feature['properties']['Magnitud']),
                'color': 'black',
                'weight': 1.5,
                'fillOpacity': 0.9
            },
            tooltip=folium.GeoJsonTooltip(
                fields=['NAME_2', 'Magnitud'],
                aliases=['Municipio:', 'Nivel:'],
                style=("background: white; padding: 5px; border: 1px solid gray;")
            )
        ).add_to(m)

        colormap.add_to(m)
        _agregar_leyenda(m)
        _agregar_titulo(m, fecha_dt)

        return m

    except Exception as e:
        print(f"Error: {str(e)}")
        return folium.Map(location=COORDENADAS_QUERETARO, zoom_start=8)

# Funciones auxiliares
def _agregar_leyenda(mapa):
    leyenda_html = '''
    <div style="position: fixed;
                bottom: 50px;
                left: 50px;
                width: 180px;
                padding: 10px;
                background: white;
                border: 2px solid #4dc4f0;
                border-radius: 5px;
                z-index: 1000;">
        <h4 style="margin:0 0 8px 0;">Niveles de Sequía</h4>
        <div style="display: grid; grid-template-columns: 25px auto; gap: 5px;">
            <div style="background:#4dc4f0; border:1px solid #000;"></div><span>0: Sin</span>
            <div style="background:#00FF00; border:1px solid #000;"></div><span>1: Leve</span>
            <div style="background:#FFFF00; border:1px solid #000;"></div><span>2: Moderada</span>
            <div style="background:#FFA500; border:1px solid #000;"></div><span>3: Severa</span>
            <div style="background:#FF0000; border:1px solid #000;"></div><span>4: Crítica</span>
            <div style="background:#8B0000; border:1px solid #000;"></div><span>5: Extrema</span>
        </div>
    </div>
    '''
    mapa.get_root().html.add_child(folium.Element(leyenda_html))

def _agregar_titulo(mapa, fecha):
    titulo_html = f'''
    <div style="position: fixed;
                top: 20px;
                left: 50px;
                padding: 10px;
                background: rgba(255,255,255,0.9);
                border: 2px solid #4dc4f0;
                border-radius: 5px;
                z-index: 1000;">
        <h3 style="margin:0;">Sequía en Querétaro<br>{fecha.strftime('%B %Y')}</h3>
    </div>
    '''
    mapa.get_root().html.add_child(folium.Element(titulo_html))

# === Función para generar el video ===
def generar_video_mapa(nombre_video='/Users/enrique/Desktop/UAQ/UNI/mapa_sequia.mp4', carpeta_frames='frames', fps=2):
    # Crear carpeta para almacenar los frames
    Path(carpeta_frames).mkdir(parents=True, exist_ok=True)

    # Generar un mapa para cada mes y guardar como imagen
    for fecha_str in fechas_unicas:
        mapa = generar_mapa_sequia(fecha_str)
        filepath_html = os.path.join(carpeta_frames, f'{fecha_str}.html')
        filepath_png = os.path.join(carpeta_frames, f'{fecha_str}.png')

        # Guardar el mapa como archivo HTML temporalmente
        mapa.save(filepath_html)

        # Capturar una imagen del mapa usando Firefox en modo sin cabeza (headless)
        os.system(f'firefox --headless --screenshot --window-size=1024x768 --output {filepath_png} {filepath_html}')

        # Remover archivo HTML después de guardar la imagen
        os.remove(filepath_html)

    # Crear video a partir de los frames guardados
    frame_files = sorted(Path(carpeta_frames).glob("*.png"))
    if len(frame_files) == 0:
        print("No se generaron frames para crear el video.")
        return

    # Obtener dimensiones del primer frame
    frame = cv2.imread(str(frame_files[0]))
    height, width, layers = frame.shape
    video = cv2.VideoWriter(nombre_video, cv2.VideoWriter_fourcc(*'mp4v'), fps, (width, height))

    # Agregar cada frame al video
    for frame_file in frame_files:
        frame = cv2.imread(str(frame_file))
        video.write(frame)

    video.release()
    print(f"Video generado exitosamente: {nombre_video}")

# === Interfaz interactiva existente ===
fechas_unicas = sorted(df_long['Fecha_str'].unique())
slider_tiempo = widgets.SelectionSlider(
    options=fechas_unicas,
    value=fechas_unicas[0],
    description='Fecha:',
    layout={'width': '80%'},
    style={'description_width': 'initial'}
)

output = widgets.Output()

def actualizar_mapa(change):
    output.clear_output(wait=True)
    with output:
        display(generar_mapa_sequia(change.new))

slider_tiempo.observe(actualizar_mapa, names='value')

display(widgets.VBox([
    widgets.Label("Selecciona el mes y año:"),
    slider_tiempo,
    output
]))

with output:
    display(generar_mapa_sequia(fechas_unicas[0]))

# === Uso adicional ===
# La función para generar el video puede ser llamada de forma independiente:
# generar_video_mapa()