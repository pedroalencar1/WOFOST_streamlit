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


# streamlit and dashboard apps
import streamlit as st
st.set_page_config(layout="wide")
# st.echarts(options=options,map=map, height = "500px")


# system 
import sys, os

# plotting
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.dates as mpldates
from matplotlib.gridspec import GridSpec
from matplotlib.dates import DateFormatter
import seaborn as sns
# import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.graph_objects as go
import plotly.express as px
# import pyautogui
import Tkinter





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
                    value = 51.2,
                    key = "lat",
                    step=0.1,format="%.1f")    
    lon = st.number_input(label = "Longitude",
                    min_value=0.,
                    max_value= 90., 
                    value = 10.5,
                    key = "lon",
                    step=0.1,format="%.1f")
    
    df = pd.DataFrame({'lat': [lat], 'lon': [lon]})
    # st.map(df, zoom = 4.5)
    
    # screen_width = pyautogui.size()[0]
    root = Tkinter.Tk()
    screen_width = root.winfo_screenwidth()

    fig = px.scatter_mapbox(df, lat="lat", lon="lon", zoom=4, size = "lon",
                            height=320, width = 0.285*screen_width,
                            color_discrete_sequence=["#b60018"],
                            size_max = 8)
    # "open-street-map", "carto-positron", "carto-darkmatter", 
    # "stamen-terrain", "stamen-toner" or "stamen-watercolor" 
    fig.update_layout(mapbox_style="carto-positron")
    fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
    # fig.show()  
    
    st.plotly_chart(fig)
              
with col2:
    st.write('<p style="font-size:20px"><b>Crop and soil</b></p>',
                     unsafe_allow_html=True)
    soil = st.selectbox(label = "Soil Class",
                        options = ("EC1 - Coarse: C<18% + S>65%",
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
    r { color: #b60018 }
    z { color: #0018b6 }
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
    
    df = pd.DataFrame(data=df)  
    df = df.fillna(0)
    df_results_wlp["day"] = df_results_wlp.index
    df_wlp = df[df["type"] == "wlp"]
    df_pp = df[df["type"] == "pp"]
    
    df_print = pd.concat([df_wlp.tail(1), df_pp.tail(1)]).reset_index(drop=True)
    
    # st.write(" ")
    # st.write("**Summary:**")
    # st.dataframe(df_print)

    col41, col42, col43 = st.columns([1,4,1])

    with col42:  
        
        ### Fig 1 
        fig1 = make_subplots(
            rows=3, cols=2,
            specs=[[{}, {}],
                   [{}, {}],
                   [{"colspan": 2}, None]],
            subplot_titles=('Total above ground production',
                            'Leaf area index',
                            'Total weight of storage organs',
                            'Transpiration',
                            'Soil Moisture'))

        fig1.add_trace(
            go.Scatter(x=df_wlp["day"], 
                       y=df_wlp["TAGP"],
                       line=dict(color="#b60018")),
            row=1, col=1)
        fig1.add_trace(
            go.Scatter(x=df_pp["day"], 
                       y=df_pp["TAGP"],
                       line=dict(color="#0018b6")),
            row=1, col=1)

        fig1.add_trace(
            go.Scatter(x=df_wlp["day"], 
                       y=df_wlp["LAI"],
                       line=dict(color="#b60018")),
            row=1, col=2)
        fig1.add_trace(
            go.Scatter(x=df_pp["day"], 
                       y=df_pp["LAI"],
                       line=dict(color="#0018b6")),
            row=1, col=2)
        
        fig1.add_trace(
            go.Scatter(x=df_wlp["day"], 
                       y=df_wlp["TWSO"],
                       line=dict(color="#b60018")),
            row=2, col=1)
        fig1.add_trace(
            go.Scatter(x=df_pp["day"], 
                       y=df_pp["TWSO"],
                       line=dict(color="#0018b6")),
            row=2, col=1)
        
        fig1.add_trace(
            go.Scatter(x=df_wlp["day"], 
                       y=df_wlp["TRA"],
                       line=dict(color="#b60018")),
            row=2, col=2)
        fig1.add_trace(
            go.Scatter(x=df_pp["day"], 
                       y=df_pp["TRA"],
                       line=dict(color="#0018b6")),
            row=2, col=2)
        
        fig1.add_trace(
            go.Scatter(x=df_wlp["day"], 
                       y=df_wlp["SM"],
                       line=dict(color="#b60018")),
            row=3, col=1)
        fig1.add_trace(
            go.Scatter(x=df_pp["day"], 
                       y=df_pp["SM"],
                       line=dict(color="#0018b6")),
            row=3, col=1)
        fig1.add_trace(
            go.Scatter(x=df_results_wlp["day"], 
                       y=df_results_wlp["smw"],
                       line=dict(color="grey")),
            row=3, col=1)
        
        fig1.update_yaxes(title_text="TAGP (Mg/ha)", row=1, col=1)
        fig1.update_yaxes(title_text="LAI (-)", row=1, col=2)
        fig1.update_yaxes(title_text="TWSO (Mg/ha)", row=2, col=1)
        fig1.update_yaxes(title_text="TRA (mm/day)", row=2, col=2)
        fig1.update_yaxes(title_text="SM (-)", range=[0, 0.5], row=3, col=1)

        fig1.update_layout(showlegend=False, 
                           title_text='Crop gaps {}'.format(year), 
                           height=900)    
        st.plotly_chart(fig1)
        
        ### Fig 2
        weather = df_weather
        weather["RAIN"] = weather["RAIN"]*10
        weather["ET0"] = weather["ET0"]*10
        weather["TEMP"] = (weather["TMAX"] +  weather["TMIN"])/2   
        
        fig2 = make_subplots(
            rows=3, cols=1,
            subplot_titles=('Precipitation',
                            'Temperature',
                            'Evapotranspiration'))

        fig2.add_trace(
            go.Scatter(x=weather["DAY"], 
                       y=weather["RAIN"],
                       line=dict(color="#0018b6")),
            row=1, col=1)  
        
        fig2.add_trace(
            go.Scatter(x=weather["DAY"], 
                       y=weather["TEMP"],
                       line=dict(color="#0018b6")),
            row=2, col=1)
        fig2.add_trace(
            go.Scatter(x=weather["DAY"], 
                       y=weather["TMAX"],
                       line=dict(color="grey",
                                 width = 0.5)),
            row=2, col=1)
        fig2.add_trace(
            go.Scatter(x=weather["DAY"], 
                       y=weather["TMIN"],
                       line=dict(color="grey",
                                 width = 0.5)),
            row=2, col=1)
        
        fig2.add_trace(
            go.Scatter(x=weather["DAY"], 
                       y=weather["ET0"],
                       line=dict(color="#0018b6")),
            row=3, col=1)  
        
        fig2.update_yaxes(title_text="P (mm/day)", row=1, col=1)
        fig2.update_yaxes(title_text="T (Celcius)", row=2, col=1)
        fig2.update_yaxes(title_text="ET0 (mm/day)", row=3, col=1)

        
        fig2.update_layout(showlegend=False, 
                           title_text='Weather {}'.format(year), 
                           height=900)        
            
        st.plotly_chart(fig2)     


st.write(
"""

<style>
r { color: #b60018 }
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


