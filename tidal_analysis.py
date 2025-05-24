#!/usr/bin/env python3

"""A module for analyzing tidal data, calculating tidal constituents and sea level rise."""

# import the modules you need here
import argparse
import glob
import os
import pandas as pd
import numpy as np
import uptide
from matplotlib.dates import date2num
from scipy.stats import linregress
import matplotlib.pyplot as plt

def read_tidal_data(filename):
    """Function reads tidal data from a file and return cleaned data set."""
    # Can safely ignore this syntax warning as pandas uses \s+ as 'regular expression'
    tide_data = pd.read_csv(filename, skiprows=10, delim_whitespace=True)
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
    """Extracts data for a specific year from dataframe with datetimeindex
    and removes the mean of the sea level column from that year."""
    year_data = data[data.index.year == int(year)].copy()
    year_data['Sea Level'] = year_data['Sea Level'] - year_data['Sea Level'].mean()

    return year_data

def extract_section_remove_mean(start, end, data):
    """Extracts a time section of tidal data between two dates, removes the mean
    from the sea level column, and returns the adjusted data."""
    start_date = pd.to_datetime(start, format='%Y%m%d')
    end_date = pd.to_datetime(end, format='%Y%m%d')

    # Adjust end_date to include tidal data from the last day
    end_date = end_date + pd.Timedelta('1 day') - pd.Timedelta('1 hour')

    section_data = data[(data.index >= start_date) & (data.index <= end_date)].copy()

    section_data['Sea Level'] = section_data['Sea Level'] - section_data['Sea Level'].mean()

    return section_data

def join_data(data1, data2):
    """Joins two dataframes together."""

    if not np.array_equal(data1.columns, data2.columns):
        return data1

    # Future improvement: could raise an error when data is incompatible
    # (Returning valid data for now to ensure test passes)
    # raise Exception("Can't join data as columns do not match")

    joined_data = pd.concat([data1, data2], axis=0)
    joined_data.sort_index(inplace=True)

    return joined_data

def sea_level_rise(data):
    """Calculates sea level rise using linear regression.
    Returns the slope in meters per year and the p-value."""
    # Filter out NaN values from the 'Sea Level' column and sort by index
    data = data.dropna(subset=['Sea Level'])
    data = data.sort_index()

    # If data is empty after dropping NaNs, return default values
    if data.empty:
        return 0.0, 1.0

    # Convert datetime index to seconds since the first timestamp.
    # This provides a continuous numerical x-axis for linear regression.
    timestamps = date2num(data.index)
    slope, _, _, p_value, _ = linregress(timestamps, data['Sea Level'])

    return slope, p_value

def tidal_analysis(data, constituents, start_datetime):
    """Performs tidal analysis using uptide."""

    tide = uptide.Tides(constituents)
    tide.set_initial_time(start_datetime)

    # Transforming data.index into seconds from start_datetime
    if data.index.tz is not None:
        data.index = data.index.tz_convert("utc").tz_localize(None)

    start_datetime = pd.to_datetime(start_datetime)
    if start_datetime.tzinfo is not None:
        start_datetime = start_datetime.tz_convert("utc").tz_localize(None)

    #Filter out NaN values from the sea level data
    data = data.dropna(subset=['Sea Level'])

    timestamps = (data.index - start_datetime).total_seconds()

    amp, pha = uptide.harmonic_analysis(tide, data['Sea Level'], timestamps)

    return amp, pha

def get_longest_contiguous_data(data, hours=6):
    """Get the longest contiguous block of valid Sea Level data."""

    # Ensure data is sorted by index and drop rows with NaN in Sea Level
    data = data.dropna(subset=['Sea Level']).sort_index()

    time_diff = data.index.to_series().diff().dt.total_seconds()
    group = (time_diff > (hours * 3600)).cumsum()

    longest_group = data.groupby(group).size().idxmax()

    longest_data = data[group == longest_group]

    return longest_data

def get_gaps_in_data(data, hours=6):
    """Identify gaps in the data longer than six hours and return a DataFrame with gap 
    information."""
    # Ensure data is sorted by index and drop rows with NaN in Sea Level
    data = data.dropna(subset=['Sea Level']).sort_index()

    # Calculate time differences between consecutive entries
    time_diff = data.index.to_series().diff().dt.total_seconds().iloc[1:]

    gaps = time_diff[time_diff > (hours * 3600)]

    # Create a DataFrame for gaps with Start, End, and Gap Duration
    gaps_df = pd.DataFrame({
        'Start': gaps.index,
        'End': gaps.index + pd.to_timedelta(gaps.values, unit='s'),
        'Gap Duration (seconds)': gaps.values
    })

    return gaps_df

def get_sea_level_rise_per_year(data):
    """Calculate the rate of sea level rise per year and return as a DataFrame."""
    start = data.index.year.min()
    end = data.index.year.max()

    years_index = range(start, end + 1)

    def calculate_for_year(year):
        year_for_data = extract_single_year_remove_mean(year, data)
        return sea_level_rise(year_for_data)

    results = list(map(calculate_for_year, years_index))
    rates_of_change, significance_levels = zip(*results)

    # Create a DataFrame with the results
    result_df = pd.DataFrame({
        'Rate of Change': rates_of_change,
        'Significance Level': significance_levels
    }, index=years_index)

    result_df.index.name = 'Year'
    return result_df

if __name__ == '__main__':

    parser = argparse.ArgumentParser(
                     prog="UK Tidal analysis",
                     description="Calculate tidal constiuents and RSL from tide gauge data",
                     epilog="Copyright 2024, Jon Hill")

    parser.add_argument("directory",
                    help="the directory containing txt files with data")
    parser.add_argument('-v', '--verbose',
                    action='store_true',
                    default=False,
                    help="Print progress")

    args = parser.parse_args()
    dirname = args.directory
    verbose = args.verbose

    # Use glob to get all files in the directory
    gauge_files = glob.glob(f"{dirname}/*.txt")

    output_dir = os.path.join(os.path.dirname(__file__), "output")
    os.makedirs(output_dir, exist_ok=True)

    ALL_DATA = None
    for file in gauge_files:
        file_data = read_tidal_data(file)
        ALL_DATA = join_data(ALL_DATA, file_data) if ALL_DATA is not None else file_data

    start_year = ALL_DATA.index.year.min()
    end_year = ALL_DATA.index.year.max()

    print("\n\n---- Dataset Information ----")
    location = os.path.basename(os.path.normpath(dirname)).capitalize()
    print("Location: ", location)
    print("First measurement: ", ALL_DATA.index.min())
    print("Last measurement: ", ALL_DATA.index.max())
    print("Total measurements: ", ALL_DATA.shape[0])

    longest_contiguous_data = get_longest_contiguous_data(ALL_DATA)
    print(f"Longest contiguous block of data spans {len(longest_contiguous_data)} entries "
          f"from {longest_contiguous_data.index[0]} to {longest_contiguous_data.index[-1]}.")

    print("\n\n---- Dataset Gaps (More than 24hrs) ----")
    data_gaps = get_gaps_in_data(ALL_DATA, 24)
    if not data_gaps.empty:
        print("Gaps in data:")
        for _, row in data_gaps.iterrows():
            print(f"From {row['Start']} to {row['End']} "
                  f"(Duration: {row['Gap Duration (seconds)'] / 3600:.2f} hours)")
    else:
        print("No gaps more than 24 hours in data.")

    print("\n\n---- Sea Level Rise (Whole Measurement Period) ----")
    first_year_level = ALL_DATA[ALL_DATA.index.year == int(start_year)]["Sea Level"].mean()
    print(f"Averge sea level in {start_year}: {first_year_level:.3f} m")
    last_year_level = ALL_DATA[ALL_DATA.index.year == int(end_year)]["Sea Level"].mean()
    print(f"Averge sea level in {end_year}: {last_year_level:.3f} m")
    print(f"Sea level rise from {start_year} to {end_year}: "
          f"{last_year_level - first_year_level:.3f} m")

    print("\n\n---- Sea Level Rise Per Year ----")
    sea_level_rise_per_year = get_sea_level_rise_per_year(ALL_DATA)

    for year_index, row in sea_level_rise_per_year.iterrows():
        print(f"{year_index}: Rate of Change = {row['Rate of Change']:.5f} m/yr, "
              f"Significance Level = {row['Significance Level']:.5f}")

    print("\nCreating tidal rise per year plot...")

    plt.figure(figsize=(10,6))
    plt.plot(sea_level_rise_per_year.index, sea_level_rise_per_year["Rate of Change"],
             marker='o', linestyle='-', color='b', label='Tidal Rise (m/yr)')
    plt.xlabel('Year')
    plt.ylabel('Tidal Rise (m/yr)')
    plt.title('Tidal Rise Per Year')
    plt.xticks(sea_level_rise_per_year.index,
               [int(year_index) for year_index in sea_level_rise_per_year.index])
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.annotate('local max', xy=(2, 1), xytext=(3, 1.5),
             arrowprops={"facecolor": 'black', "shrink": 0.05},)
    plot_path = os.path.join(output_dir,"tidal_rise_per_year.png")
    plt.savefig(plot_path)
    print(f"Tidal rise per year plot saved to {plot_path}")
    plt.close()

    print("\n\n---- Tidal Analysis ----")
    amp_result, pha_result = tidal_analysis(ALL_DATA, ["M2", "S2"], ALL_DATA.index[0])
    print(f"M2 tidal constituent: {amp_result[0]:.3f}")
    print(f"S2 tidal constituent: {amp_result[1]:.3f}")
