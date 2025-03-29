import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

# Configuración inicial
st.set_page_config(layout="wide", page_title="Sistema Acuíferos")
st.title("SISTEMA DE GESTIÓN HÍDRICA DE ACUÍFEROS")

# Datos de los mantos acuíferos
datos_mantos = {
    "TOLIMAN": {
        "AÑO": [2003, 2009, 2013, 2015, 2018, 2020, 2023],
        "RERGA_TOTAL": [8.40]*7,
        "EXTRACCION": [0, 0, 0, 0, 9.03, 9.96, 10.44],
        "DISP_NEGATIVA": [0, -0.08, -0.62, -0.70, -3.53, -3.96, -4.94]
    },
    "TEQUISQUIAPAN": {
        "AÑO": [2003, 2009, 2013, 2015, 2018, 2020, 2023],
        "RERGA_TOTAL": [108.10]*7,
        "EXTRACCION": [0, 0, 0, 0, 104.30, 108.07, 110.65],
        "DISP_NEGATIVA": [0, 0, 0, 0, 0, -2.57, -5.15]
    },
    "SAN JUAN DEL RIO": {
        "AÑO": [2003, 2009, 2013, 2015, 2018, 2020, 2023],
        "RERGA_TOTAL": [309.0, 191.5, 191.5, 191.5, 191.5, 191.5, 277.9],
        "EXTRACCION": [0, 0, 0, 0, 326.9, 327.76, 334.79],
        "DISP_NEGATIVA": [-12.93, -118.68, -129.64, -133.35, -135.4, -136.26, -56.89]
    },
    "HUIMILPAN": {
        "AÑO": [2003, 2009, 2013, 2015, 2018, 2020, 2023],
        "RERGA_TOTAL": [20.0]*7,
        "EXTRACCION": [0, 0, 0, 0, 21.94, 21.91, 22.54],
        "DISP_NEGATIVA": [-1.07, 0, -0.51, -0.53, -1.94, -3.91, -4.54]
    },
    "CADEREYTA": {
        "AÑO": [2009, 2013, 2015, 2018, 2020, 2023],
        "RERGA_TOTAL": [4.10]*6,
        "EXTRACCION": [0, 0, 0, 3.62, 4.14, 3.66],
        "DISP_NEGATIVA": [0, 0, 0, 0, -0.04, 0]
    },
    "QUERETARO": {
        "AÑO": [2003, 2009, 2013, 2015, 2018, 2020, 2023],
        "RERGA_TOTAL": [70.0]*7,
        "EXTRACCION": [0, 0, 0, 0, 131.93, 129.72, 131.56],
        "DISP_NEGATIVA": [-76.32, -74.36, -68.02, -67.01, -65.93, -63.72, -65.56]
    },
    "AMAZCALA": {
        "AÑO": [2003, 2009, 2013, 2015, 2018, 2020, 2023],
        "RERGA_TOTAL": [34.0]*7,
        "EXTRACCION": [0, 0, 0, 0, 54.33, 54.45, 53.36],
        "DISP_NEGATIVA": [-44.69, -40.75, -25.21, -24.68, -23.13, -23.25, -22.16]
    },
    "BUENAVISTA": {
        "AÑO": [2011, 2013, 2015, 2018, 2020, 2023],
        "RERGA_TOTAL": [11.0, 11.0, 11.0, 11.0, 11.0, 9.5],
        "EXTRACCION": [0, 0, 0, 22.41, 23.34, 23.28],
        "DISP_NEGATIVA": [-9.06, -11.05, -11.05, -11.51, -12.44, -13.88]
    }
}

# Convertir a DataFrames
mantos_df = {nombre: pd.DataFrame(datos) for nombre, datos in datos_mantos.items()}

# ============ SECCIÓN 1: DATOS COMPLETOS ============
st.header("1. Datos Completos por Manto Acuífero")
tabs = st.tabs(list(mantos_df.keys()))
for tab, (nombre, df) in zip(tabs, mantos_df.items()):
    with tab:
        st.subheader(f"Datos: {nombre}")
        st.dataframe(df.round(2))
        st.write(f"Último registro: {df['AÑO'].max()} - Déficit: {df['DISP_NEGATIVA'].iloc[-1]:.2f} hm³/año")

# ============ SECCIÓN 2: COMPARATIVA 2023 ============
st.header("2. Comparativa General 2023")

# Preparar datos 2023
df_2023 = pd.DataFrame([{
    'Manto': nombre,
    'Recarga': df[df['AÑO'] == 2023]['RERGA_TOTAL'].values[0] if 2023 in df['AÑO'].values else np.nan,
    'Extracción': df[df['AÑO'] == 2023]['EXTRACCION'].values[0] if 2023 in df['AÑO'].values else np.nan,
    'Déficit': df[df['AÑO'] == 2023]['DISP_NEGATIVA'].values[0] if 2023 in df['AÑO'].values else np.nan
} for nombre, df in mantos_df.items()])

df_2023['Sobreexplotación (%)'] = np.where(
    df_2023['Recarga'] > 0,
    ((df_2023['Extracción'] / df_2023['Recarga']) - 1) * 100,
    np.nan
)
df_2023 = df_2023.dropna()

# Gráficos comparativos
col1, col2 = st.columns(2)

with col1:
    st.subheader("Déficit Hídrico (2023)")
    fig1 = px.bar(df_2023.sort_values('Déficit'), 
                 x='Manto', y='Déficit',
                 color='Déficit',
                 color_continuous_scale='RdYlGn',  # Cambio clave
                 range_color=[df_2023['Déficit'].min(), df_2023['Déficit'].max()])
    st.plotly_chart(fig1, use_container_width=True)

with col2:

# ============ SECCIÓN 3: EVOLUCIÓN TEMPORAL ============
st.header("3. Evolución Histórica")
fig3 = go.Figure()
for nombre, df in mantos_df.items():
    fig3.add_trace(go.Scatter(x=df['AÑO'], y=df['DISP_NEGATIVA'],
                            name=nombre, mode='lines+markers'))
fig3.update_layout(height=500, yaxis_title="Déficit (hm³/año)")
st.plotly_chart(fig3, use_container_width=True)

# ============ SECCIÓN 4: ANÁLISIS INDIVIDUAL ============
st.header("4. Análisis por Manto")
manto_seleccionado = st.selectbox("Seleccione un manto:", list(mantos_df.keys()))
df = mantos_df[manto_seleccionado]

fig4 = px.line(df, x='AÑO', y=['RERGA_TOTAL', 'EXTRACCION', 'DISP_NEGATIVA'],
              labels={'value': 'hm³/año'},
              color_discrete_map={
                  'RERGA_TOTAL': '#2CA02C',
                  'EXTRACCION': '#FF7F0E',
                  'DISP_NEGATIVA': '#D62728'
              })
st.plotly_chart(fig4, use_container_width=True)

# ============ SECCIÓN 5: SEMÁFORO DE PRIORIDADES ============
st.header("5. Semáforo de Prioridades Hídricas")

# Configuración de prioridades simplificada
prioridades = {
    0: {"color": "#90EE90", "nombre": "Baja", 
        "acciones": [
            "Monitoreo anual",
            "Mantenimiento preventivo",
            "Promoción de cultura del agua"
        ]},
    
    1: {"color": "#FFFF00", "nombre": "Media", 
        "acciones": [
            "Control de extracciones",
            "Optimización de redes",
            "Auditorías técnicas"
        ]},
    
    2: {"color": "#FF0000", "nombre": "Alta", 
        "acciones": [
            "Reducción obligatoria de consumo",
            "Restricciones severas",
            "Emergencia hídrica declarada"
        ]}
}

# Nueva clasificación con 3 niveles
bins = [-np.inf, -20, -10, np.inf]
labels = [2, 1, 0]  # 2: Rojo, 1: Amarillo, 0: Verde
df_2023['Prioridad'] = pd.cut(
    df_2023['Déficit'],
    bins=bins,
    labels=labels,
    right=False
).astype(int)

# Función para tabla con estilo (modificada)
def dataframe_with_style(df):
    html = "<table style='width:100%; border-collapse: collapse;'><tr>"
    for col in df.columns:
        html += f"<th style='border: 1px solid #ddd; padding: 8px;'>{col}</th>"
    html += "</tr>"
    
    for _, row in df.iterrows():
        html += "<tr>"
        for col in df.columns:
            style = "border: 1px solid #ddd; padding: 8px;"
            if col == 'Prioridad':
                try:
                    priority = int(row[col])
                    color = prioridades[priority]['color']
                except (ValueError, KeyError):
                    color = "#FFFFFF"
                style += f"background-color: {color};"
            html += f"<td style='{style}'>{row[col]}</td>"
        html += "</tr>"
    html += "</table>"
    return html

# Mostrar tabla con formato
st.subheader("Clasificación por Prioridad")
styled_df = df_2023[['Manto', 'Déficit', 'Prioridad']].copy()
styled_df = styled_df.sort_values('Prioridad', ascending=False).round(2)
st.markdown(dataframe_with_style(styled_df), unsafe_allow_html=True)

# Semáforo visual simplificado
st.subheader("Niveles de Prioridad")
cols = st.columns(3)
for i in range(3):
    with cols[i]:
        nivel = prioridades[i]
        st.markdown(f"""
        <div style='background-color: {nivel['color']};
                    padding: 15px;
                    border-radius: 10px;
                    text-align: center;
                    margin: 5px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);'>
            <strong>{nivel['nombre']}</strong>
        </div>
        """, unsafe_allow_html=True)
        
        st.caption("Acciones clave:")
        for accion in nivel['acciones']:
            st.caption(f"• {accion}")

# Resto del código se mantiene igual...
