"""
Created on 29.03.2023

@@@@@@@@@@@@@@@
@Pedro Alencar@
@@@@@@@@@@@@@@@

Initial script for a wofost app in streamlit

Notes
-----
    
"""

# %% LOAD PACKAGES AND SET PATHS

# system
import sys, os, subprocess\

# streamlit and dashboard apps
import streamlit as st
st.set_page_config(layout="wide")

# system 
import sys, os, subprocess

# plotting
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.dates as mpldates
from matplotlib.gridspec import GridSpec
from matplotlib.dates import DateFormatter
import seaborn as sns
# import plotly.graph_objects as go
import ipyleaflet as L
import folium
from folium.plugins import MarkerCluster
import pydeck as pdk


# data
import pandas as pd
import numpy as np
import datetime as datetime
import timestamp as ts

# wofost 
import pcse
from pcse.fileinput import CABOFileReader
from pcse.fileinput import YAMLAgroManagementReader
from pcse.fileinput import YAMLCropDataProvider
from pcse.fileinput import ExcelWeatherDataProvider
from pcse.fileinput import CABOWeatherDataProvider
from pcse.util import WOFOST72SiteDataProvider
from pcse.base import ParameterProvider
from pcse.models import Wofost72_WLP_FD, Wofost72_PP

# local imports
# from location import location_server, location_ui # creates map input - Source:https://github.com/rstudio/py-shiny/tree/main/examples/airmass
import auxiliar_functions_wofost as afw # auxiliar functions 
 
app_path = os.path.dirname(os.path.realpath(__file__))
os.chdir(app_path)

# set data directory. Here all input files should be organized into folders 
# names: agro, crop, meteo, output, site, and soil
data_dir = os.path.join(os.getcwd(), "data_wofost")

# get metadata of available stations
lst_stations = pd.read_csv("station_data/stations_metadata.csv")


# %% Auxiliar variables
crop_types = [*YAMLCropDataProvider(fpath = os.path.join(data_dir,"crop")).get_crops_varieties().keys()]
crop_varieties = YAMLCropDataProvider(fpath = os.path.join(data_dir,"crop")).get_crops_varieties()
varieties = []
for c_type in crop_types :
    
    var = [*crop_varieties[c_type]]
    varieties = [*varieties, *var]

# years = list(range(1980, 2022))
#%% APP

#%% title
coltitle, colfig1 = st.columns([5,1])
with coltitle:
    st.title("WOFOST model")
    st.subheader("This application has a simple implementation of WOFOST that allows running and\
        vizualizing the outputs of the model for different years, crops and soils.")
    st.write("  ")
    st.write("  ")

with colfig1:
    st.write("  ")
    st.write("  ")
    st.image("figures/logo.png", use_column_width= True)   

#%% input columns

st.subheader("Model input")
col1, col2, col3 = st.columns([1,1,1])

with col1:
    st.write('<p style="font-size:20px"><b>Location input</b></p>',
                     unsafe_allow_html=True)
    lat = st.number_input(label = "Latitude",
                    min_value=0.,
                    max_value= 90., 
                    value = 52.4,
                    key = "lat",
                    step=0.1,format="%.1f")    
    lon = st.number_input(label = "Longitude",
                    min_value=0.,
                    max_value= 90., 
                    value = 13.1,
                    key = "lon",
                    step=0.1,format="%.1f")
    
    df = pd.DataFrame({'lat': [lat], 'lon': [lon]})    
    st.map(df, zoom = 3)
        
    # my_map = folium.Map(location = [lat, lon], zoom_start = 4)
    # folium.Marker(location=[lat, lon]).add_to(my_map)
    # my_map
              
with col2:
    st.write('<p style="font-size:20px"><b>Crop and soil</b></p>',
                     unsafe_allow_html=True)
    soil = st.selectbox(label = "Soil Class",
                        options = ("EC1 - Coarse: C<18% + S>65% (BBr)",
                            "EC2 - Medium: 18<C<35% + S>15%;  C<18% + 15<S<65%",
                            "EC3 - Medium fine: C<35%+ S<15%",
                            "EC4 - Fine: 35<C<60%",
                            "EC5 - Very fine: C>60%"),
                        key = "soil")    
    depth = st.number_input(label = "Soil depth (cm)",
                    min_value = 10.,
                    max_value= 150., 
                    value = 100.,
                    key = "depth",
                    step=1.,format="%.1f")    
    wav = st.number_input(label = "Initial SWC (cm)",
                         min_value=0.,
                         max_value= 50., 
                         value = 1.,
                         key = "wav",
                         step=0.1,format="%.1f")
    crop_type = st.selectbox(label = "Crop type",
                        options = crop_types,
                        index = 15,
                        key = "crop_type") 
    
    varieties_ = list(filter(lambda k: crop_type.upper() in k.upper(), varieties))

    crop_var = st.selectbox(label = "Crop type",
                        options = varieties_,
                        key = "crop_var") 
    
    co2 = st.number_input(label = "CO2 (ppm)", 
                          value=360., 
                          min_value=0., 
                          max_value = 700.,
                          key = "co2",
                          step=1.,format="%.1f")
       
    
    
with col3:
    st.write('<p style="font-size:20px"><b>Calendar</b></p>',
                     unsafe_allow_html=True)
    year = st.number_input(label = "Year",
                    min_value=1980,
                    max_value= 2021, 
                    value = 2020,
                    key = "year",
                    step=1)   
    start_date = st.date_input("Start Date (yyyy/mm/dd)",
                               datetime.date(year, 4, 1)) 
    end_date = st.date_input("End Date (yyyy/mm/dd)",
                               datetime.date(year, 11, 1)) 
    max_dur = st.number_input(label = "Max.Duration",
                              min_value=0,
                              max_value=360,
                              value=200,
                              step = 1)
    start_type = st.selectbox(label = "Crop Start Type",
                              options = ("Emergence", "Sowing"))
    end_type = st.selectbox(label = "Crop End Type",
                              options = ("Maturity", "Harvest"))
    
st.markdown("""---""")

#%% Calculate
if st.button('Run Simulation', type = "primary"):

    # parameters
    crop_type_ = crop_type
    crop_var_ = crop_var
    soil_ = soil[0:3]+'.yaml'
    depth_ =depth
    wav_ = wav
    co2_ = co2

    sited = WOFOST72SiteDataProvider(WAV=wav_) 
    sited['CO2'] = co2_    
        
    cropd = YAMLCropDataProvider(fpath = os.path.join(data_dir,"crop")) 
    cropd.set_active_crop(crop_type_, crop_var_)
    
    soild = afw.YamlSoilReader(os.path.join(data_dir, 'soil',soil_))
    soild['RDMSOL'] = depth_
    
    parameters = ParameterProvider(cropdata=cropd, soildata=soild, sitedata=sited)
    
    # agromanagement
    year_= year
    start_date_ = start_date
    end_date_ = end_date
    max_dur_ = max_dur
    start_type_ = start_type.lower()
    end_type_ = end_type.lower()
        
    agromanagement = afw.SimpleAgromanagementEdition(path = os.path.join(data_dir, 'agro', 'basic.agro'), 
                    year = year_, 
                    D_start = start_date_, 
                    T_start = start_type_, 
                    D_end = end_date_, 
                    T_end = end_type_,
                    max_dur = max_dur_,
                    parameters = parameters)
    
    # weather
    # find closest station to selected coordinates
    code = afw.ClosestStation(lst_st=lst_stations, map_lat=lat, map_lon=lon)
    
    # load weather data
    weatherfile = os.path.join(data_dir, 'meteo', "Germany")
    wdp  = CABOWeatherDataProvider(code.code+"1", fpath=weatherfile)
    
    # run WOFOST
    # Potential production
    wofsim_pp = Wofost72_PP(parameters, wdp, agromanagement)
    wofsim_pp.run_till_terminate()
    df_results_pp = pd.DataFrame(wofsim_pp.get_output())
    df_results_pp = df_results_pp.set_index("day")
    
    # Water limited production
    wofsim_wlp = Wofost72_WLP_FD(parameters, wdp, agromanagement)
    wofsim_wlp.run_till_terminate()
    df_results_wlp = pd.DataFrame(wofsim_wlp.get_output())
    df_results_wlp = df_results_wlp.set_index("day")
    
    # Weather df
    df_weather = pd.DataFrame(wdp.export())
    df_weather = df_weather[pd.DatetimeIndex(df_weather['DAY']).year  == year_]
    
    
    # GET PLOTS
    # plot 1
    
    df_results_wlp['type'] = 'wlp'
    df_results_pp['type'] = 'pp'
    
    df = pd.concat([df_results_wlp, df_results_pp]).reset_index(drop=False)
    
    df['TAGP'] =  df['TAGP']/1000
    df['TWSO'] =  df['TWSO']/1000
    
    df_results_wlp["smw"] = parameters._soildata['SMW']
    
    ### MESSAGE 1
    st.write(
    """
    <style>
    r { color: Red }
    z { color: Blue }
    </style>

    Bellow we present some plots with:
    * TAGP: Total Aboge Ground Production
    * TWSO: Total Weight of Storage Organs
    * LAI: Leaf Area Index
    * TRA: Transpiration
    * SM: Soil Moisture

    The <b><r>red line</r></b> indicates the values for Water Limited Production and the <b><z>blue line</z></b> for the 
    potential production (soil moisture constant at the field capacity).
    """,
    unsafe_allow_html=True)
    
    text = "**Weather data retrieved from {} (station id: {}).**".format(code.SOUNAME.capitalize(), code.STAID)    
    st.write(text)

    
    ### Fig 1 
    plt.rcParams.update({'font.size': 6,
                         'text.color': "#242630",
                         'font.family': "TyfoonSans"})
    fig1 = plt.figure(constrained_layout=True)
    gs = GridSpec(3, 2, figure=fig1)
    fig1.subplots_adjust(hspace=0.5, wspace=0.35)
    date_form = DateFormatter("%m")

    ax1 = fig1.add_subplot(gs[0, 0]).xaxis.set_major_formatter(date_form)
    sns.lineplot(data=df, x = 'day', y = 'TAGP', hue = 'type', errorbar=None, legend=False,
                palette = ['red', 'blue']).set(
                    title='Total above ground production', xlabel = None, 
                    xticklabels=[], ylabel='TAGP (Mg/ha)')

    ax2 = fig1.add_subplot(gs[0, 1]).xaxis.set_major_formatter(date_form)
    sns.lineplot(data=df, x = 'day', y = 'LAI', hue = 'type', errorbar=None, legend=False,
                palette = ['red', 'blue']).set(
                    title='Leaf area index', xlabel = None, xticklabels=[], ylabel='LAI (-)')

    ax3 = fig1.add_subplot(gs[1, 0]).xaxis.set_major_formatter(date_form)
    sns.lineplot(data=df, x = 'day', y = 'TWSO', hue = 'type', errorbar=None, legend=False,
                palette = ['red', 'blue']).set(
                    title='Total weight of storage organs',xlabel = 'Month', ylabel='TWSO (Mg/ha)')

    ax4 = fig1.add_subplot(gs[1, 1]).xaxis.set_major_formatter(date_form)
    sns.lineplot(data=df, x = 'day', y = 'TRA', hue = 'type', errorbar=None, legend=False,
                palette = ['red', 'blue']).set(
                    title='Transpiration', xlabel = 'Month', ylabel="TRA (mm/day)")

    ax5 = fig1.add_subplot(gs[2, :]).xaxis.set_major_formatter(date_form)
    sns.lineplot(data=df, x = 'day', y = 'SM', hue = 'type', errorbar=None, legend=False,
                palette = ['red', 'blue']).set(
                    title='Soil Moisture', xlabel = 'Month', ylabel="SM (-)")
    sns.lineplot(data=df_results_wlp, x = 'day', y = 'smw', errorbar=None, legend=True, color="grey",
                    linewidth = 1)  
    
                    
    fig1.suptitle('Crop gaps {}'.format(year)) # or plt.suptitle('Main title')    
    st.pyplot(fig1)
    
    ### Fig 2
    weather = df_weather
    weather["RAIN"] = weather["RAIN"]*10
    weather["ET0"] = weather["ET0"]*10
    weather["TEMP"] = (weather["TMAX"] +  weather["TMIN"])/2    
    
    fig2 = plt.figure(constrained_layout=True)
    gs = GridSpec(3, 1, figure=fig2)
    fig2.subplots_adjust(hspace=0.5, wspace=0.35)
    date_form = DateFormatter("%m")
    
    ax1 = fig2.add_subplot(gs[0, 0]).xaxis.set_major_formatter(date_form)
    sns.lineplot(data=weather, x = 'DAY', y = 'RAIN', errorbar=None, color = 'blue',legend=False,
                ).set(title='Precipitation', xlabel = None, xticklabels=[],
                        ylabel = "P (mm/day)")
    
    ax2 = fig2.add_subplot(gs[1, 0]).xaxis.set_major_formatter(date_form)
    sns.lineplot(data=weather, x = 'DAY', y = 'TEMP', errorbar=None, legend=False, color="blue",
                ).set(title='Temperature', xlabel = None, xticklabels=[],
                        ylabel = "T (Celcius)")
    sns.lineplot(data=weather, x = 'DAY', y = 'TMIN', errorbar=None, legend=False, color="grey",
                    linewidth = 0.5).set(title='Temperature', xlabel = None, xticklabels=[],
                        ylabel = "T (Celcius)")    
    sns.lineplot(data=weather, x = 'DAY', y = 'TMAX', errorbar=None, legend=False, color="grey",
                    linewidth = 0.5).set(title='Temperature', xlabel = None, xticklabels=[],
                        ylabel = "T (Celcius)")    

    
    ax3 = fig2.add_subplot(gs[2, 0]).xaxis.set_major_formatter(date_form)
    sns.lineplot(data=weather, x = 'DAY', y = 'ET0', errorbar=None, legend=False,color="blue",
                ).set(title='Potential Evapotranspiration {}'.format(year), xlabel = "Month",
                        ylabel = "ET0 (mm/day)")  
                
    fig2.suptitle('Weather variables {}'.format(year)) 
    st.pyplot(fig2)

   

st.write(
"""

<style>
r { color: Red }
z { color: Blue }
</style>


<br>

---

<b>About WOFOST</b>
<br>
<br>

[WOFOST](https://www.wur.nl/en/research-results/research-institutes/environmental-research/facilities-tools/software-models-and-databases/wofost.htm)
(WOrld FOod STudies) is a simulation model for the quantitative analysis of the growth and 
production of annual field crops. The model is one of the key components of the [European MARS crop yield 
forecast system](https://joint-research-centre.ec.europa.eu/monitoring-agricultural-resources-mars_en). 
It is also used in the Global Yield Gap Atlas ([GYGA](http://www.yieldgap.org/)) to estimate the 
untapped crop production potential on existing farmland based on current climate and available soil 
and water resources.

_Source: [WOFOST webpage](https://www.wur.nl/en/research-results/research-institutes/environmental-research/facilities-tools/software-models-and-databases/wofost.htm)_

---

<b>About this app</b>
<br>

This application was developed by [Pedro Alencar](https://www.oekohydro.tu-berlin.de/menue/team/pedro_alencar/)
and is independent of the WOFOST developing group. 

All information used is open source. The WOFOST model can be accessed at https://github.com/ajwdewit/pcse. 
Weather data from [DWD](https://www.dwd.de/DE/Home/home_node.html). The script for this app is available at
the author's github.

""",
unsafe_allow_html=True
)


