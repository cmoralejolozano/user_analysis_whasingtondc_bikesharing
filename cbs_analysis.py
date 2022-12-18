#----------------------------------------------LIBRERIAS----------------------------------------------------------------------
import numpy as np
import pandas as pd
import os
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import plotly_express as px
from plotly.subplots import make_subplots
import plotly.graph_objects as go
from streamlit_folium import st_folium
import folium
import geopandas as gpd
import requests
import streamlit as st
import zipfile
from PIL import Image

#----------------------------------------------CONFIGURACIÓN DE PÁGINA ----------------------------------------------------------------------

st.set_page_config(page_title="Capital Bike Share análisis de usuarios", layout="wide", page_icon="🚲​") # después establecer el título de página, su layout e icono 

#---------------------------------------------- COSAS QUE PODEMOS USAR EN TODA NUESTRA APP----------------------------------------------------------------------
# Leemos todos los archivos en una línea
df_hourly = pd.read_csv('cbs_hourly.csv')

@st.cache
def read_files():
	read1 = pd.read_csv('cbs_individual_records_1_seventh.zip',compression='zip')
	read2 = pd.read_csv('cbs_individual_records_2_seventh.zip',compression='zip')
    	read3 = pd.read_csv('cbs_individual_records_3_seventh.zip',compression='zip')
    	read4 = pd.read_csv('cbs_individual_records_4_seventh.zip',compression='zip')
    	read5 = pd.read_csv('cbs_individual_records_5_seventh.zip',compression='zip')
    	read6 = pd.read_csv('cbs_individual_records_6_seventh.zip',compression='zip')
    	read7 = pd.read_csv('cbs_individual_records_7_seventh.zip',compression='zip')
    	whole = pd.concat([read1, read2, read3, read4, read5, read6, read7])
    	return whole

cbs = read_files()

#cbs_1 = pd.read_csv('cbs_individual_records_1_seventh.zip',compression='zip')
#cbs_2 = pd.read_csv('cbs_individual_records_2_seventh.zip',compression='zip')
#cbs_3 = pd.read_csv('cbs_individual_records_3_seventh.zip',compression='zip')
#cbs_4 = pd.read_csv('cbs_individual_records_4_seventh.zip',compression='zip')
#cbs_5 = pd.read_csv('cbs_individual_records_5_seventh.zip',compression='zip')
#cbs_6 = pd.read_csv('cbs_individual_records_6_seventh.zip',compression='zip')
#cbs_7 = pd.read_csv('cbs_individual_records_7_seventh.zip',compression='zip')
#cbs = pd.concat([cbs_1, cbs_2, cbs_3, cbs_4, cbs_5, cbs_6, cbs_7])
#cbs= pd.read_csv('cbs_from_2016_to_10-2022.csv')

# Agrupo por estación y año, lo que me da la cuenta de usuarios por año
anual_users_station = pd.DataFrame(cbs.groupby(['Start station', 'year']).size().unstack(fill_value=0).reset_index().values,
                        columns=["Start station", "2016", "2017", "2018", "2019", "2020", "2021", "2022"])
# Creo columna de los años del dataframe
anual_users_station['Anual iniciated Trips average (5 last Yrs)'] = anual_users_station[anual_users_station.columns.difference(["Start station",
                    "2022", "2016"])].mean(axis=1).astype(int)
# Vamos a obtener de la API proporcionada por Capital Bike Share datos sobre las ubicaciones de las estaciones de bicis
url = 'https://maps2.dcgis.dc.gov/dcgis/rest/services/DCGIS_DATA/Transportation_WebMercator/MapServer/5/query?where=1%3D1&outFields=*&outSR=4326&f=json'
respuesta = requests.get(url)
# Obtenemos los datos y los convertimos a diccionaro formato JSON.
respuesta = respuesta.json()
# Asigno a variable la selección del diccionario: key 'features' y de la lista que hay dentro, todos sus elementos
respuesta = respuesta['features'][:]
# Selección de cada diccionario dentro de la lista y conversión a dataframe
respuesta = pd.json_normalize(respuesta) # https://stackoverflow.com/questions/54321290/how-to-convert-list-of-nested-dictionary-to-pandas-dataframe
# Renombro las columnas eliminando attributed. de cada columna
respuesta = respuesta.rename(columns=lambda x: x.split('.')[-1]) # https://stackoverflow.com/questions/64998101/how-to-remove-part-of-the-column-name
# Conviero el df en GeoDataframe asignando el argumento geometry, necesario para dibujar el mapa con Folium
respuesta = gpd.GeoDataFrame(respuesta, crs= 'epsg:4326',geometry= gpd.points_from_xy(respuesta['LONGITUDE'], respuesta['LATITUDE'])) # https://geopandas.org/en/stable/gallery/create_geopandas_from_pandas.html
# Combino el dataset
respuesta = pd.merge(respuesta, anual_users_station, left_on='NAME', right_on = 'Start station', how='inner')
# Cambio el nombre a la columna 'address' para que en el mapa aparezca 'Station'
respuesta.rename(columns= {'NAME': 'station'}, inplace= True)
# Elimino columnas que no se van a utilizar
respuesta.drop(columns= ['STATION_ID', 'OBJECTID', 'STATION_STATUS', 'LAST_REPORTED', 'NUM_DOCKS_AVAILABLE', 'NUM_EBIKES_AVAILABLE',
                        'NUM_BIKES_DISABLED', 'IS_INSTALLED', 'IS_RETURNING', 'IS_RENTING', 'HAS_KIOSK', 'IOS', 'ANDROID', 'ELECTRIC_BIKE_SURCHARGE_WAIVER',
                        'EIGHTD_HAS_KEY_DISPENSER', 'CAPACITY', 'REGION_ID', 'GIS_LAST_MOD_DTTM', 'GIS_ID', 'NUM_DOCKS_DISABLED',
                        'NUM_BIKES_AVAILABLE'], inplace= True)
# Cambio los nombres de las columnas para que todas estén en minúsculas
respuesta.columns = respuesta.columns.str.lower()

# Vamos a obtener de la API proporcionada por Capital Bike Share datos sobre las ubicaciones de las estaciones de bicis
url = 'https://maps2.dcgis.dc.gov/dcgis/rest/services/DCGIS_DATA/Administrative_Other_Boundaries_WebMercator/MapServer/17/query?outFields=*&where=1%3D1&f=geojson'
barrios2 = requests.get(url)
# Obtenemos los datos y los convertimos a diccionaro formato JSON.
barrios2 = barrios2.json()
# Asigno a variable la selección del diccionario: key 'features' y de la lista que hay dentro, todos sus elementos
barrios2 = barrios2['features'][:]
# Selección de cada diccionario dentro de la lista y conversión a dataframe
barrios2 = pd.json_normalize(barrios2) # https://stackoverflow.com/questions/54321290/how-to-convert-list-of-nested-dictionary-to-pandas-dataframe

# Leo archivo GeoJSON con geopandas
barrios = gpd.read_file("Neighborhood_Clusters.geojson")
# web oficial descarga dataset barrios Washington D.C.: https://opendata.dc.gov/datasets/neighborhood-clusters/explore?location=38.893761%2C-77.014470%2C12.24

# Elimino las columnas que no se van a utilizar
barrios.drop(columns= ['WEB_URL', 'TYPE', 'CREATOR', 'CREATED', 'EDITOR', 'EDITED',
                        'SHAPEAREA', 'SHAPELEN'], inplace= True)
# Cambio los nombres de las columnas para que todas estén en minúsculas
barrios.columns = barrios.columns.str.lower()
# Cambio el nombre a la columna 'nbh_names' para que en el mapa aparezca 'neighborhood'
barrios.rename(columns= {'nbh_names': 'neighborhood'}, inplace= True)
# Uno los datasets asignando a cada estación su barrio: https://geopandas.org/en/stable/gallery/spatial_joins.html
cbs_map_data =  respuesta.sjoin(barrios, how="left", predicate="within")
# Agrupo por barrio para conocer el número de estaciones por barrio y luego poder combinarlo
stations_per_neighborhood = cbs_map_data.groupby('neighborhood').count().reset_index()
stations_per_neighborhood.drop(columns= ['longitude', 'station', 'station_type', 'rental_methods', 'region_name', 'x', 'y', 'geometry',
                                    'start station', '2016', '2017', '2018', '2019', '2020', '2021', '2022', 
                                    'anual iniciated trips average (5 last yrs)', 'index_right', 'objectid','name', 'globalid'], inplace = True)
stations_per_neighborhood.rename(columns= {'latitude': 'number of stations'}, inplace= True)

# Uno los datasets asignando a cada estación su barrio: https://geopandas.org/en/stable/gallery/spatial_joins.html
cbs_map_data2 =  barrios.sjoin(respuesta, how="left", predicate="within")
# Elimino columnas que no tienen sentido en este caso
cbs_map_data2.drop(columns= ['index_right', 'latitude', 'longitude', 'station', 'station_type', 'rental_methods',
                        'region_name', 'x', 'y', 'start station', '2016', '2017', '2018', '2019', '2020', '2021', '2022',
                        'anual iniciated trips average (5 last yrs)'], inplace= True)

# Combino el dataset con las estaciones por barrio
cbs_map_data2 = pd.merge(cbs_map_data2, stations_per_neighborhood, on = 'neighborhood', how= 'left')
# relleno los valores nulos con 0s
cbs_map_data2.fillna(0, inplace =True)
# el barrio pasa a ser el índice, es necesario para dibujar el choropleth map con plotly
cbs_map_data2.set_index('neighborhood', inplace= True)

#---------------------------------------------- EMPIEZA LA APP ----------------------------------------------------------------------

st.title("Análisis de Usuarios - Capital Bikeshare")
st.markdown('Los sistemas de bicicletas compartidas son una nueva generación de alquileres de bicicletas tradicionales donde todo \
    el proceso, desde la membresía, el alquiler y la devolución se ha automatizado. A través de estos sistemas, el usuario puede \
    alquilar fácilmente una bicicleta en una estación y devolverla en otra estación diferente. Actualmente, hay alrededor \
    de 500 programas de bicicletas compartidas en todo el mundo, que se componen de más de 500 mil bicicletas. Hoy en día existe un \
    gran interés por estos sistemas debido a su importante papel en el tráfico, cuestiones ambientales y de salud.')

col1, col2 = st.columns([2.75,1.25])
with col1:
    st.markdown("Capital Bikeshare es el nombre por el que se conoce al servicio de alquiler de bicicletas compartidas que opera en\
    Washington, D.C. y otras ciudades pequeñas cercanas a esta.")
    st.markdown('Recientemente la gerencia ha notado una disminución de las membresías, y por ello, les gustaría contar con un análisis \
    de los datos que recopilan gracias a estos sistemas automatizados, para así, ver las diferencias que existen entre los usuarios \
    miembros y los casual, además de cualquier otro factor que tenga relación con la cantidad de usuarios.')
    st.markdown('Los datos utilizados de Capitalbikeshare van desde el 2016 a octubre del 2022. Se pueden descargar en esta URL de su web \
    oficial: https://ride.capitalbikeshare.com/system-data')
    st.markdown('Los datos del clima han sido obtenidos de la web freemeteo: \
    https://freemeteo.es/eltiempo/Washington-D.C./historial/historial-diario/?gid=9036777&station=19056&date=2022-11-23&language=spanish&country=us-united-states')

with col2:
    imagen = Image.open('bicycle-bike-rack-urban-preview.jpg')
    st.image(imagen)

m1, m2, m3, m4 = st.columns((1,1,1,1))
fig = go.Figure(go.Indicator(
    mode = "number+delta",
    value = len(cbs[cbs['year']==2022]['Start station'].unique()),
    title = {'text': "Total Estaciones<br><span style='font-size:0.8em;color:gray'>2022</span>"},
    delta = {'reference': len(cbs[cbs['year']==2021]['Start station'].unique())},
    domain = {'x': [0, 1], 'y': [0, 1]}))
fig.update_layout(width=300, height=300)
m2.plotly_chart(fig, use_container_width=True)

# Creación gráfico de donut
values_pie = cbs[cbs['year']>= 2017].groupby(['Member type'])['Duration (min)'].count().reset_index()
values_pie.rename(columns= {'Duration (min)': 'Number of users'}, inplace= True)
colors = {"casual": "#f5deb3", "member": "#ff6347"} #https://stackoverflow.com/questions/66518387/python-plotly-graph-objects-discrete-color-map-like-in-plotly-express
values_pie["Color"] = values_pie['Member type'].apply(lambda x: colors.get(x)) #to connect Column value to Color in Dict

fig = px.pie(values_pie, values='Number of users', names='Member type', hole=.5, labels= 'Member type', 
                color_discrete_sequence=px.colors.sequential.RdBu)
fig.update_traces(hoverinfo='label+percent', insidetextorientation= 'horizontal',
                textinfo='label+percent', textfont_size=20, marker=dict(colors=values_pie["Color"], line=dict(color='#000000', width=0)))
fig.add_annotation(x= 0.5, y = 0.5,
                    text = 'Total usuarios<br>{:,}'.format(values_pie['Number of users'].sum()),
                    font = dict(size=10,family='Verdana', 
                                color='black'),
                    showarrow = False)
fig.update_layout(title_text='Últimos 5 años', title_x=0.50, showlegend=False, width=300, height=300)
m3.plotly_chart(fig, use_container_width=True) # https://towardsdatascience.com/pie-donut-charts-with-plotly-d5524a60295b
del values_pie

st.write("---")
st.header("¿Donde se encuentran las estaciones?")
col1,col2 = st.columns(2)
with col1:
    st.markdown('A principios de los 2000 se establecieron las agrupaciones de barrios por la Oficina de Planificación cómo unidades \
        razonablemente descriptivas de la ciudad para fines de planificación. Estos se han mantenido para facilitar las comparaciones \
        y análisis de agencias y analistas externos, aunque no son límites oficiales de los vecindarios.')
    st.markdown('* La agrupación 8 (cluster 8), en la que se encuentra el centro de la ciudad, es la que tiene un mayor número de estaciones.')
    st.markdown('* Según nos vamos alejando del centro, va disminuyendo el número de estaciones.')

fig = px.choropleth_mapbox(cbs_map_data2,
                   geojson=cbs_map_data2['geometry'],
                   locations=cbs_map_data2.index,
                   hover_name = cbs_map_data2['name'],
                   color="number of stations",
                   center={"lat": 38.9049093, "lon": -77.0042995},
                   mapbox_style="stamen-toner",
                   opacity= 0.7,
                   color_continuous_scale="ylorrd",
                   zoom=11, width=750, height=600)
fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
col2.plotly_chart(fig, use_container_width=True)

cbs_map_data2.reset_index(inplace = True)
# gráfico mostrando los clusters proporcionalmente por el número de estaciones que tienen: https://plotly.com/python/treemaps/
fig = px.treemap(cbs_map_data2, path=['neighborhood'], values='number of stations',color_discrete_sequence=px.colors.sequential.Oryel[::-1],
                width=750, height=450)
fig.update_traces(root_color="white")
fig.update_layout(margin = dict(t=40, l=0, r=0, b=0), uniformtext=dict(minsize=9, mode='show'), template='plotly_white',
            title="Agrupaciones por tamaño según la cantidad de estaciones")
col1.plotly_chart(fig, use_container_width=True)

st.write("---")
st.header("¿Cuáles son las estaciones con mayor número de viajes iniciados?")
col1,col2 = st.columns(2)
with col2:
    st.markdown('En el mapa de la izquierda cuanto más grande es la burbuja, más viajes se han iniciado en esa estación durante los \
        últimos 5 años.')

with col1:
    m = folium.Map(location=[38.8949166, -77.0299636], zoom_start=14, tiles= 'cartodbpositron', attr= 'https://deparkes.co.uk/2016/06/10/folium-map-tiles/')
    for i in range(0,len(respuesta[respuesta['anual iniciated trips average (5 last yrs)']>0])):
        folium.CircleMarker(
        location=[respuesta.iloc[i]['latitude'], respuesta.iloc[i]['longitude']],
        tooltip=respuesta.iloc[i][['station', 'anual iniciated trips average (5 last yrs)']],
        radius=float(respuesta.iloc[i]['anual iniciated trips average (5 last yrs)'])/1500,
        color='#ee3123',
        fill=True,
        fill_color='#ee3123'
        ).add_to(m)
    st_data = st_folium(m, width= 700, height= 500) # https://github.com/randyzwitch/streamlit-folium

fig = px.histogram(respuesta[respuesta['anual iniciated trips average (5 last yrs)']>27000].sort_values(by= "anual iniciated trips average (5 last yrs)"), 
            x="anual iniciated trips average (5 last yrs)", y="station", barmode='group',text_auto='.2s',
            color_discrete_sequence=px.colors.sequential.Oryel[::-1])
fig.update_layout(title='Top 10 estaciones por cantidad de viajes', yaxis_title=None, xaxis_title='Cantidad de viajes iniciados', showlegend=False,
                yaxis=dict(showgrid=False), template= 'plotly_white', title_x=0.5)
col2.plotly_chart(fig, use_container_width=True)

st.write("---")
col1,col2 = st.columns(2)
with col1:
    st.header("Cantidad de usuarios por día, año actual y anterior")
    st.markdown('Hagamos un primer vistazo sobre los datos del año actual y el anterior.')
    st.markdown('* Comparando ambos años hasta ostubre, aparentemente el 2022 ha tenido un mayor número de usuarios.')
with col2:
    # streamlit share launches from a directory above so need to account for this in the file path
    imagen = Image.open('cbs_21-22_calendarmap.png')
    st.image(imagen, caption= 'Cada cuadrado representa un día, cuanto más oscuro es el cuadrado, más usuarios han utilizado el servicio \
        ese día.')

st.write("---")
col1,col2 = st.columns(2)
with col2:
    st.header("Cantidad de usuarios por año")
    st.markdown('* En la época pre-Covid-19 el número de usuarios miembros era muy superior al de los usuarios casual, mientras \
        que a partir del 2020 la diferencia entre los usuarios miembros y casual es muy inferior.')
    st.markdown('* El año 2022, a falta de 2 meses de datos, parece que podría terminar el año con un número más parecido a los de \
        la época pre-Covid-19.')

#creo variables para agregar los datos y hacer los gráficos https://www.statology.org/pandas-groupby-bar-plot/
casual_by_year = df_hourly.groupby(['year'])['casual_count'].sum().reset_index()
registered_by_year = df_hourly.groupby(['year'])['registered_count'].sum().reset_index()
newcount_by_year = df_hourly.groupby(['year'])['new_count'].sum().reset_index()

fig = go.Figure()
fig.add_trace(go.Bar(x= casual_by_year['year'], y= casual_by_year['casual_count'],marker=dict(color="wheat"), text=casual_by_year['casual_count'],
            textposition='outside', texttemplate='%{text:.2s}', name='Casual'))
fig.add_trace(go.Bar(x= registered_by_year['year'], y= registered_by_year['registered_count'],marker=dict(color="tomato"), name='Miembro',
            text=registered_by_year['registered_count'], textposition='outside', texttemplate='%{text:.2s}'))
fig.add_trace(go.Line(x= newcount_by_year['year'], y= newcount_by_year['new_count'],marker=dict(size=15, color="goldenrod"), name='Ambos'))
fig.update_layout(template='plotly_white', legend_title_text='Tipo de Usuario',
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
col1.plotly_chart(fig, use_container_width=True)
del casual_by_year, registered_by_year, newcount_by_year

areachart_df = df_hourly.reset_index()
fig = px.area(areachart_df, x='dates', y='new_count', title='Cantidad de usuarios en el tiempo', template= 'plotly_white',
            color_discrete_sequence=["goldenrod"])

fig.update_xaxes(
    rangeslider_visible=True,
    rangeselector=dict(
        buttons=list([
            dict(count=1, label="1m", step="month", stepmode="backward"),
            dict(count=6, label="6m", step="month", stepmode="backward"),
            dict(count=1, label="1y", step="year", stepmode="backward"),
            dict(step="all")
        ])
    )
)
fig.update_layout(yaxis_title=None, xaxis_title=None, showlegend=False,
                yaxis=dict(showgrid=False))
col2.plotly_chart(fig, use_container_width=True)
del areachart_df

st.write("---")
col1, col2, col3= st.columns([1,2,1]) 
with col2:
    st.header("Distribución del nº de usuarios por mes (datos horarios).")
    st.markdown('* En los meses de otoño e invierno la cantidad de usuarios es muy inferior a la de los meses de primavera y verano.')
    st.markdown('* Esta diferencia es más notable en los usuarios casual que en los miembros, pasando de una mediana en enero de 11 \
        usuarios por hora a una mediana de 128 en julio.')

col1,col2 = st.columns(2)
fig = px.violin(df_hourly, y = 'month', x= 'casual_count', color= 'month', color_discrete_sequence=px.colors.sequential.Oryel[::-1], 
        orientation= 'h', template = 'plotly_white', points=False).update_traces(side="positive", width=2)
fig.update_layout(title='Casual', yaxis_title=None, xaxis_title='Cantidad de Usuarios', showlegend=False,
                yaxis=dict(showgrid=False), xaxis= dict(range=[-30,400]), title_x=0.5)
col1.plotly_chart(fig, use_container_width=True)

fig = px.violin(df_hourly, y = 'month', x= 'registered_count', color= 'month', color_discrete_sequence=px.colors.sequential.Oryel, 
        orientation= 'h', template = 'plotly_white', points=False).update_traces(side="positive", width=2)
fig.update_layout(title='Miembro', yaxis_title=None, xaxis_title='Cantidad de Usuarios', showlegend=False,
                yaxis=dict(showgrid=False), xaxis= dict(range=[-50,750]), title_x=0.5)
col2.plotly_chart(fig, use_container_width=True)

st.write("---")

col1, col2, col3 = st.columns([1,2,1])
with col2:
    st.header('Cantidad de usuarios por hora del día')
col1,col2 = st.columns(2)
with col1:
    st.subheader('Distribución')
    st.markdown('* Después de la madrugada, a las 08:00 aumenta sustancialmente el número de usuarios, este desciende bastante a las \
        09:00, pero va paulatinamente subiendo hasta las 17:00, hora en la que encontramos el valor de la mediana más alto. Después de \
        esa hora el número de usuarios baja hasta el nivel mínimo que se mantiene desde las 00:00 hasta las 06:00.')

with col2:
    st.subheader('Media por día de la semana')
    st.markdown('* En los sábados y los domingos no existen los picos que podemos ver a las 08:00 y a las 17:00 de lunes a viernes, \
        pero de madrugada el uso es mayor en estos dos días.')
    st.markdown('* Se mantiene durante la mayor parte de las horas del sábado la media por encima de las horas del domingo.')

col1,col2 = st.columns(2)

fig = px.box(df_hourly, x="hour", y="new_count", color= "hour", template = 'plotly_white', color_discrete_sequence=px.colors.sequential.Oryel[::-1],
            notched= True)
fig.update_layout( yaxis_title=None, xaxis_title='Hora',
    xaxis=dict(showgrid=False, dtick= 1), showlegend=False)
col1.plotly_chart(fig, use_container_width=True)

fig = plt.figure(figsize=[8,7])
fig = px.line(df_hourly.groupby(['weekday','hour'])['new_count'].mean().reset_index(), x='hour', y='new_count', color='weekday', 
                color_discrete_sequence=px.colors.qualitative.D3[::-1], markers=True, template = 'simple_white', 
                category_orders={"weekday": ["L", "M", "X", "J", "V", "S", "D"]})

fig.update_layout(yaxis_title=None, xaxis_title='Hora',
    xaxis=dict(showgrid=True, dtick= 1, range=[0,23]), yaxis= dict(range=[0,1200], showgrid=True), showlegend=True, legend_title_text='Día de la semana',
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
col2.plotly_chart(fig, use_container_width=True)

st.write("---")
col1,col2 = st.columns(2)
with col1:
        # section 2 running a MC simulation
        st.header('Uso en días laborables o no laborables')
        st.markdown('* Los miembros efectúan la mayoría de sus viajes en días laborables, mientras que en los usuarios casual no existe \
            una diferencia muy grande entre los días laborables y no laborables, realizan el 42% de sus viajes en días no laborables, \
            contra un 24% en el caso de los miembros.')

colors = {"Laborable": "#67001F", "No laborable": "#B2182B"} #https://stackoverflow.com/questions/66518387/python-plotly-graph-objects-discrete-color-map-like-in-plotly-express
df_hourly["Color"] = df_hourly['workday'].apply(lambda x: colors.get(x)) #to connect Column value to Color in Dict
# Create subplots: use 'domain' type for Pie subplot
fig = make_subplots(rows=1, cols=2, specs=[[{'type':'domain'}, {'type':'domain'}]])
fig.add_trace(go.Pie(labels= df_hourly['workday'], values=df_hourly['casual_count'],name="Usuarios casuales", 
                insidetextorientation= 'horizontal'), 1, 1)
fig.add_trace(go.Pie(labels= df_hourly['workday'], values= df_hourly['registered_count'], name="Usuarios registrados", 
                insidetextorientation= 'horizontal'), 1, 2)
# Use `hole` to create a donut-like pie chart
fig.update_traces(hole=.4, hoverinfo="label+percent+name",textinfo='label+percent', marker=dict(colors=df_hourly["Color"],
                              line=dict(color='#000000', width=0)))
fig.update_layout(coloraxis_autocolorscale=True, coloraxis_colorscale= ['wheat','tomato'],
    # Add annotations in the center of the donut pies.
    annotations=[dict(text='Casual', x=0.175, y=0.5, font_size=20, showarrow=False),
                dict(text='Miembro', x=0.86, y=0.5, font_size=20, showarrow=False)], showlegend=False,legend_title_text='Día laborable',
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=1))
col2.plotly_chart(fig, use_container_width=True)

st.write("---")
col1,col2 = st.columns(2)
with col2:
        # section 2 running a MC simulation
        st.header('¿Cuál es la duración de los viajes?')
        st.markdown('* Hay una diferencia bastante grande entre la media y la mediana de la duración de los viajes entre los \
            usuarios miembros y los casual. Los miembros realizan unos viajes mucho más cortos que los casual.')

# Creo grupos de la duración media y mediana por tipo de miembro, luego creo dataframe con los datos de la media y la mediana
duration_avg = cbs.groupby('Member type')['Duration (min)'].mean().reset_index()
duration_avg.rename(columns= {'Duration (min)': 'Avg Duration (min)'}, inplace= True)
duration_median = cbs.groupby('Member type')['Duration (min)'].median().reset_index()
duration_median.rename(columns= {'Duration (min)': 'Median Duration (min)'}, inplace= True)
duration_plot = pd.merge(duration_avg, duration_median, how= 'inner', on= 'Member type')
del duration_avg, duration_median

fig= go.Figure() # https://towardsdatascience.com/lollipop-dumbbell-charts-with-plotly-696039d5f85
fig.add_trace(go.Scatter(x = duration_plot["Median Duration (min)"], 
                          y = duration_plot["Member type"],
                          mode = 'markers+text',
                          marker_color = 'royalblue',
                          marker_size = 15,
                          name = 'Mediana',
                          text= duration_plot["Median Duration (min)"],
                          textposition='top center',
                          texttemplate='%{text:.2s}'))
fig.add_trace(go.Scatter(x = duration_plot["Avg Duration (min)"], 
                          y = duration_plot["Member type"],
                          mode = 'markers+text',
                          marker_color = 'tomato', 
                          marker_size = 15,
                          name = 'Media',
                          text= duration_plot["Avg Duration (min)"],
                          textposition='top center',
                          texttemplate='%{text:.2s}'))
for i in range(0, len(duration_plot)):
               fig.add_shape(type='line',
                              x0 = duration_plot["Median Duration (min)"][i],
                              y0 = i,
                              x1 = duration_plot["Avg Duration (min)"][i],
                              y1 = i,
                              line=dict(color='silver', width = 2.5))
fig.update_layout(template='plotly_white', xaxis_title= 'Duración (minutos)',legend=dict(orientation="h", yanchor="bottom", 
                y=1.02, xanchor="right", x=1))
col1.plotly_chart(fig, use_container_width=True)
del duration_plot

st.write("---")
col1, col2, col3= st.columns([1,2,1]) 
with col2:
    st.header("¿Afecta el clima a la cantidad de Usuarios?")

corr =  df_hourly[['casual_count', 'registered_count', 'temperature', 'wind_speed', 'humidity']].corr(method = 'spearman').round(2).sort_values(by = 'registered_count',
                axis = 0, ascending = False).sort_values(by = 'registered_count', axis = 1,ascending = False)

mask = np.triu(np.ones_like(corr, dtype=bool))
corr = corr.mask(mask)
fig = px.imshow(corr.to_numpy().round(2), x=list(corr.index.values), y=list(corr.columns.values), zmin=-1, zmax=1, text_auto=".2f",
    color_continuous_scale='Hot', aspect="auto", template= 'plotly_white')

fig.update_layout(title_text='<b>Matriz de correlación<b>',
                  title_x=0.5,
                  titlefont={'size': 24},
                  width=350, height=350,
                  xaxis_showgrid=False,
                  xaxis={'side': 'bottom'},
                  yaxis_showgrid=False,
                  yaxis_autorange='reversed')
col2.plotly_chart(fig, use_container_width=True)
with col2:
    st.markdown('* Existe una correlación positiva tanto en la cantidad de usuarios miembros cómo en los casual, aunque es más \
        pronunciada en estos segundos.')
    st.markdown('* Vemos una correlación débil negativa de la humedad con el número de usuarios.')
    st.markdown('* La velocidad del viento no tiene correlación con el número de usuarios.')

col1, col2, col3= st.columns([1,2,1]) 
with col2:
    st.subheader("Densidad de usuarios respecto a la temperatura")
    st.write('Visualizamos la correlación con la temperatura de la que hablábamos anteriormente.')

fig = px.density_heatmap(df_hourly, x="temperature", y="new_count", color_continuous_scale="Spectral", template= 'plotly_white',
                    range_y= [0,700], range_x= [-10,38])
col2.plotly_chart(fig, use_container_width=True)

col1, col2, col3= st.columns([1,2,1]) 
with col2:
    st.header('¡Gracias por su atención!')
    st.subheader('¿Alguna pregunta?')
    imagen = Image.open('wordcloud_cbs_tripadv.png')
    st.image(imagen, caption= 'Nube de palabras obtenida de las reseñas en Tripadvisor: https://www.tripadvisor.com/Attraction_Review-g28970-d2478701-Reviews-Capital_Bikeshare-Washington_DC_District_of_Columbia.html')

st.markdown('*Autor: Carlos Moralejo Lozano*')
