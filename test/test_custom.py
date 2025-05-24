import sys
sys.path.insert(0,"../")
sys.path.insert(0,"./")
from tidal_analysis import *
import pandas as pd

class TestCustom():
    
    def test_gaps_in_data(self):
        # Test that gaps in data are handled correctly
        gauge_files = ['data/1946ABE.txt', 'data/1947ABE.txt']
        data1 = read_tidal_data(gauge_files[1])
        data2 = read_tidal_data(gauge_files[0])
        data = join_data(data1, data2)

        gaps = get_gaps_in_data(data)

        assert gaps.index.size == 28

    def test_sea_level_rise_per_year(self):
        gauge_files = ['data/1946ABE.txt', 'data/1947ABE.txt']
        data1 = read_tidal_data(gauge_files[1])
        data2 = read_tidal_data(gauge_files[0])
        data = join_data(data1, data2)

        result_df = get_sea_level_rise_per_year(data)

        # Check the DataFrame structure
        assert "Rate of Change" in result_df.columns
        assert "Significance Level" in result_df.columns
        assert result_df.index.name == "Year"

        # Check that the DataFrame has the correct number of rows
        assert len(result_df) == data.index.year.max() - data.index.year.min() + 1

        # Check that the rate of change and significance level are floats
        assert pd.api.types.is_float_dtype(result_df["Rate of Change"])
        assert pd.api.types.is_float_dtype(result_df["Significance Level"])

        # Check that the values are within a reasonable range
        assert result_df["Rate of Change"].between(-0.1, 0.1).all()
        assert result_df["Significance Level"].between(0, 1).all()
        