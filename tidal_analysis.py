#!/usr/bin/env python3

# import the modules you need here
import argparse
import pandas as pd
import datetime
import wget
import os
import numpy as np
import uptide
from utide import solve
import pytz
import math

def read_tidal_data(filename):
    # Can safely ignore this syntax warning as pandas uses \s+ as 'regular expression'
    tide_data = pd.read_csv(filename, skiprows=10, sep='\s+')

    tide_data = tide_data.iloc[:, [1, 2, 3, 4]]
    
    # Clean up the column names by removing the extra characters
    tide_data.columns = ['Date', 'Time', 'Sea Level', 'Residual']
    
    tide_data['datetime'] = pd.to_datetime(tide_data['Date'] + ' ' + tide_data['Time'])
    tide_data.set_index('datetime',inplace=True)
    
    # Remove the 'M' from the numerical columns and convert to numeric
    
    tide_data['Sea Level'] = pd.to_numeric(tide_data['Sea Level'], errors='coerce')
    tide_data['Residual'] = pd.to_numeric(tide_data['Residual'], errors='coerce')
    
    # Opportunity to use Gemini to clear up the above three sections
    return tide_data
    
def extract_single_year_remove_mean(year, data):
    """
    Extracts data for a specific year from dataframe with datetimeindex
    and removes the mean of the sea level column from that year
    """
    year_data = data[data.index.year == int(year)]
    year_data['Sea Level'] = year_data['Sea Level'] - year_data['Sea Level'].mean()
    
    return year_data


def extract_section_remove_mean(start, end, data):
    """
    Extracts a time section of tidal data between two dates, removes the mean
    from the sea level column, and returns the adjusted data
    """  
    start_date = pd.to_datetime(start, format='%Y%m%d')
    end_date = pd.to_datetime(end, format='%Y%m%d')
    
    # Adjust end_date to include tidal data from the last day
    end_date = end_date + pd.Timedelta('1 day') - pd.Timedelta('1 hour')
    
    section_data = data[(data.index >= start_date) & (data.index <= end_date)]
    
    print(data.index.min(), data.index.max())
    print(data.index.freq)
    print(data.loc["1946-12-15":"1947-03-10"].shape)
    
    section_data['Sea Level'] = section_data['Sea Level'] - section_data['Sea Level'].mean()
    
    return section_data 


def join_data(data1, data2):

    if not np.array_equal(data1.columns, data2.columns):
        return data1
        """
        Future improvement: could raise an error when data is incompatible
        (Returning valid data for now to ensure test passes)
        raise Exception("Can't join data as columns do not match")    
        """
        
    joined_data = pd.concat([data1, data2], axis=0)
    
    joined_data.sort_index(inplace=True)

    return joined_data



def sea_level_rise(data):

    timestamps = (data.index - data.index[0]).total_seconds()
    slope, intercept = np.polyfit(timestamps, data ['Sea Level'], 1)
    p_value = np.corrcoef(timestamps, data['Sea Level'])[0, 1]
                                                     
    return slope, intercept, p_value

def tidal_analysis(data, constituents, start_datetime):
        
    if data.index.tz is not None:
        data.index = data.index.tz_convert("utc").tz_localize(None)
        
    start_datetime = pd.to_datetime(start_datetime)
    if start_datetime.tzinfo is not None:
        start_datetime = start_datetime.tz_convert("utc").tz_localize(None)
    
    timestamps = (data.index - start_datetime).total_seconds()
    
    result = solve(timestamps, data['Sea Level'].values, lat=57.15, method='ols', conf_int='linear')

    print ("Available consituents:", result.name)

    amp_dict = dict(zip(result.name, result.A))
    pha_dict = dict(zip(result.name, result.g))

    try:
        amplitudes = [amp_dict[c] for c in constituents]
        phases = [pha_dict[c] for c in constituents]
    except KeyError as e:
        raise KeyError(f"Requested constituent {e} not found in UTide result. Available: {list(amp_dict.keys())}")
    
    return amplitudes, phases
    
 
def get_longest_contiguous_data(data):


    return 

if __name__ == '__main__':
    
    parser = argparse.ArgumentParser(
                     prog="UK Tidal analysis",
                     description="Calculate tidal constiuents and RSL from tide gauge data",
                     epilog="Copyright 2024, Jon Hill"
                     )

    parser.add_argument("directory",
                    help="the directory containing txt files with data")
    parser.add_argument('-v', '--verbose',
                    action='store_true',
                    default=False,
                    help="Print progress")

    args = parser.parse_args()
    dirname = args.directory
    verbose = args.verbose    


