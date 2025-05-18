#!/usr/bin/env python3

# import the modules you need here
import argparse
import pandas as pd
import datetime
import wget
import os
import numpy as np
import uptide
import pytz
import math

def read_tidal_data(filename):
    tide_data = pd.read_csv(filename, skiprows=10, sep='\s+')
    tide_data = tide_data.iloc[:, [1, 2, 3, 4]]
    print(tide_data.head())
    # Clean up the column names by removing the extra characters
    tide_data.columns = ['Date', 'Time', 'Sea Level', 'Residual']
    
    tide_data['datetime'] = pd.to_datetime(tide_data['Date'] + ' ' + tide_data['Time'])
    tide_data.set_index('datetime',inplace=True)
    tide_data.drop(columns=['Date', 'Time'], inplace=True)
    
    # Remove the 'M' from the numerical columns and convert to numeric
    '''
    tide_data['Sea Level'] = tide_data['Sea Level'].str.replace('M', '')
    tide_data['Residual'] = tide_data['Residual'].str.replace('M', '')
    
    tide_data['Sea Level'] = tide_data['Sea Level'].str.replace('N', '')
    tide_data['Residual'] = tide_data['Residual'].str.replace('N', '')
    
    tide_data['Sea Level'] = tide_data['Sea Level'].str.replace('T', '').astype(float)
    tide_data['Residual'] = tide_data['Residual'].str.replace('T', '').astype(float)
    '''
    
    tide_data['Sea Level'] = pd.to_numeric(tide_data['Sea Level'], errors='coerce')
    tide_data['Residual'] = pd.to_numeric(tide_data['Residual'], errors='coerce')
    
    # Opportunity to use Gemini to clear up the above three sections
    
    print(tide_data)
    
   
    return tide_data
    
def extract_single_year_remove_mean(year, data):
   

    return 


def extract_section_remove_mean(start, end, data):


    return 


def join_data(data1, data2):

    return 



def sea_level_rise(data):

                                                     
    return 

def tidal_analysis(data, constituents, start_datetime):


    return 

def get_longest_contiguous_data(data):


    return 

if __name__ == '__main__':
    '''
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
    '''
    read_tidal_data("data/1947ABE.txt")
    


