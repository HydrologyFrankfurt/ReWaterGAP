# -*- coding: utf-8 -*-
"""
Created on Wed Jun 19 14:03:44 2024

@author: nyenah
"""

import pandas as pd
import json
import numpy as np 

# Sample function to load your data
def load_data(file_path):
    with open(file_path, 'r') as file:
        dis = json.load(file)
    dis = pd.DataFrame.from_dict(dis.get("streamflow"))
    dis['date'] = pd.to_datetime(dis['date']).dt.year
    dis.set_index('date', inplace=True)
    return dis

def generate_river_dis(df):
    start=1981 
    end=2010
    data_dis=[]
    years = []

    def add_next_value(i):
        value = df.loc[i].values[0]
        if value != "NA":
            data_dis.append(np.float32(value))
            years.append(i)
            
    def insert_value_at_start(i):       
        value=df.loc[i].values[0]
        if value != "NA":
            data_dis.insert(0, np.float32(value))
            years.insert(0, i) 

    for i in range(start, end):
        add_next_value(i)

  
    # Check if we have 30  years of discharge data

    if len(data_dis) == 30:
        # data has complete 30 years
        pass
    else:
        # go back to 1979 as start year
        for i in range(1979, start):
            insert_value_at_start(i)
            if len(data_dis) == 30:
               # data has complete 30 years
               break
    
    # extent the years after 2010     
    for i in range(end, 2019):
        if len(data_dis) != 30:
            add_next_value(i)
        else:
            # data has complete 30 years
            break
               
    
    # Check if we have 30  years of discharge data
    if len(data_dis) == 30:
        # data has complete 30 years
        pass
    else:
        # go back year by year starting from 1978 until 1901 as start year
        for i in range(1978, 1900, -1):
            insert_value_at_start(i)  
            if len(data_dis) == 30:
                # data has complete 30 years
                break
        

    dis = pd.DataFrame({'Year': years, 'obs_dis': data_dis})
    dis_sorted = dis.sort_values(by='Year')
    dis_sorted.set_index('Year', inplace =True)
    return dis_sorted      





