#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jul 27 14:01:47 2022

@author: alencar
"""

#%% Load packages and modules; set relevant path variables

# %matplotlib inline
import sys, os
import matplotlib
# matplotlib.style.use("ggplot")

import yaml 
from yaml.loader import SafeLoader
import datetime

data_dir = os.path.join(os.getcwd(), "data_wofost_pedro")

import pcse
from pcse.fileinput import CABOFileReader
from pcse.fileinput import YAMLAgroManagementReader


#%% User functions

# create YAML from default CABO files
def create_yaml_soil(data_dir, soil_classes):

    for soil_class in soil_classes:
        soilfile = os.path.join(data_dir, 'soil', soil_class+'.NEW')
        soild = CABOFileReader(soilfile)

        with open(os.path.join(data_dir, 'soil', soil_class+'.yaml'), 'w') as outfile:
            yaml.dump(soild, outfile, default_flow_style=False)

        # remove fist line    
        lines = []
        with open(os.path.join(data_dir, 'soil', soil_class+'.yaml'), 'r') as fy:
            lines = fy.readlines()

        with open(os.path.join(data_dir, 'soil', soil_class+'.yaml'), 'w') as fp:
            for number, line in enumerate(lines):
                if number not in [0]:
                    fp.write(line)
        
        print("File {0} created!".format(soil_class+'.yaml'))   
        

# read new YAML files
def YamlSoilReader(path_to_file):
    
    with open(path_to_file) as f:
        data = yaml.load(f, Loader=SafeLoader)
        data = data['dictitems']
        
        return data
    
# convert julian to date (format = '%Y-%m-%d')
def JulianToDate(year, julian):
    
    Jdate = str(year)+str(julian)
    date_complete = datetime.datetime.strptime(Jdate, '%Y%j').date()
    
    return date_complete

# function to convert old ISTCHO (WCC) to crop_start_type (pcse) format
def CropStartType(op):
    
    if op not in [0,1]: 
         print('Invalid options. Choose 0 or 1!')
    elif op == 0:
        starttype = 'emergence'
    else:
        starttype = 'sowing'
        
    return starttype        

# function to convert old IENCHO (WCC) to crop_end_type (pcse) format
def CropEndType(op):
    
    if op not in [1,2,3]:        
        print('Invalid options. Choose 1, 2 or 3!')
    elif op == 2:
        endtype = 'maturity'
    else:
        endtype = 'harvest'
        
    return endtype

# function to edit and create new agromanagement files with option of multiple years
def AgromanagementEdition(path, parameters,max_dur, year, month = 1, day= 1, J_start = 1, T_start = 1, 
                          J_end = 365, T_end = 1, fallow = False):
    
    if (fallow):    
        agromanagement = YAMLAgroManagementReader(path)

        # create a new key with the year of interest
        agromanagement[0][datetime.date(year, month, day)] = agromanagement[0][datetime.date(9999, 1, 1)]
        # remove the old one with the default year (9999)
        agromanagement[0].pop(datetime.date(9999, 1, 1))

        agromanagement[0][datetime.date(year, month, day)]['CropCalendar'] = None 
    else:
        agromanagement = YAMLAgroManagementReader(path)

        # create a new key with the year of interest
        agromanagement[0][datetime.date(year, month, day)] = agromanagement[0][datetime.date(9999, 1, 1)]
        # remove the old one with the default year (9999)
        agromanagement[0].pop(datetime.date(9999, 1, 1))

        agromanagement[0][datetime.date(year, month, day)]['CropCalendar']['crop_name'] = parameters._cropdata.current_crop_name
        agromanagement[0][datetime.date(year, month, day)]['CropCalendar']['variety_name'] = parameters._cropdata.current_variety_name
        agromanagement[0][datetime.date(year, month, day)]['CropCalendar']['crop_start_date'] = JulianToDate(year, J_start)
        agromanagement[0][datetime.date(year, month, day)]['CropCalendar']['crop_start_type'] = CropStartType(T_start)
        agromanagement[0][datetime.date(year, month, day)]['CropCalendar']['crop_end_date'] = JulianToDate(year, J_end)
        agromanagement[0][datetime.date(year, month, day)]['CropCalendar']['crop_end_type'] = CropEndType(T_end)
        agromanagement[0][datetime.date(year, month, day)]['CropCalendar']['max_duration'] = max_dur
        
    
    return agromanagement

# simpler function to edit and create new agromanagement file
def SimpleAgromanagementEdition(path, parameters,max_dur, year, D_start = "2021-04-15", T_start = "sowing", 
                          D_end = "2021-10-15", T_end = "harvest"):
    
    agromanagement = YAMLAgroManagementReader(path)

    # create a new key with the year of interest
    agromanagement[0][datetime.date(year, 1, 1)] = agromanagement[0][datetime.date(9999, 1, 1)]
    # remove the old one with the default year (9999)
    agromanagement[0].pop(datetime.date(9999, 1, 1))

    agromanagement[0][datetime.date(year, 1, 1)]['CropCalendar']['crop_name'] = parameters._cropdata.current_crop_name
    agromanagement[0][datetime.date(year, 1, 1)]['CropCalendar']['variety_name'] = parameters._cropdata.current_variety_name
    agromanagement[0][datetime.date(year, 1, 1)]['CropCalendar']['crop_start_date'] = D_start
    agromanagement[0][datetime.date(year, 1, 1)]['CropCalendar']['crop_start_type'] = T_start
    agromanagement[0][datetime.date(year, 1, 1)]['CropCalendar']['crop_end_date'] = D_end
    agromanagement[0][datetime.date(year, 1, 1)]['CropCalendar']['crop_end_type'] = T_end
    agromanagement[0][datetime.date(year, 1, 1)]['CropCalendar']['max_duration'] = max_dur       
    
    return agromanagement

# function to get closest available station
def ClosestStation(lst_st, map_lat, map_lon):
    
    # get positio min distance
    st_min = lst_st.assign(dist=lambda x: (x.LAT-map_lat)**2 + (x.LON-map_lon)**2)['dist'].idxmin()
    
    # extrect row with meta data
    code = lst_st.iloc[st_min]
    
    return code
    

