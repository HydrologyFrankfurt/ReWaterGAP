# Import necessary libraries
import xarray as xr
import pandas as pd


def convert_csv(out_path='./calibration/regionalization_input/'):
    # =========================================================================
    # Load and process temperature data (1971-2000)
    # =========================================================================
    # Define file path and load temperature data
    temperature_path = "./input_data/climate_forcing/temperature/*.nc"
    temperature_data = xr.open_mfdataset(temperature_path)

    # Select data for the years 1971 to 2000 and convert temperature from Kelvin to Celsius
    temperature_1971_2000 = temperature_data.tas.sel(time=slice("1971-01-01", "2000-12-31")) - 273.15

    # Calculate yearly and overall mean temperature for the selected period
    temperature_1971_2000_yearly_mean = temperature_1971_2000.resample(time='Y').mean()
    temperature_1971_2000_mean = temperature_1971_2000.mean(dim='time')

    # Convert the xarray data to a pandas DataFrame
    temperature_1971_2000_mean_df = temperature_1971_2000_mean.load().to_dataframe(name='GTEMP_1971_2000')

    # =========================================================================
    # Load and process maximum soil moisture data
    # =========================================================================
    smax_path = "./output_data/smax.nc"
    smax = xr.open_dataarray(smax_path, decode_times=False)
    smax_df = smax.to_dataframe(name='max_soil_water_content')

    # =============================================================================
    # Load and process maximum groundwater recharge
    # =============================================================================
    max_gw_recharge_path = "./input_data/static_input/soil_storage/watergap_22d_max_recharge.nc4"
    max_gw_recharge = xr.open_dataarray(max_gw_recharge_path, decode_times=False)
    max_gw_recharge_df = max_gw_recharge .to_dataframe(name='max_groundwater_recharge')

    # =============================================================================
    # Load Arc_ID data and merge with soil moisture and temperature data
    # =============================================================================
    # Load Arc_ID data
    arcid_path = "./input_data/static_input/arc_id.nc"
    arcid = xr.open_dataarray(arcid_path, decode_times=False)

    # Convert Arc_ID xarray data to a DataFrame for merging
    arcid_df = arcid.to_dataframe(name="Arc_ID")
    arcid_df = arcid_df.dropna()
    arcid_df["Arc_ID"] = arcid_df["Arc_ID"].astype(int)

    # Merge Arc_ID data with temperature data on latitude and longitude
    merge_temp_df = pd.merge(arcid_df, temperature_1971_2000_mean_df, on=['lat', 'lon'], how='left')
    merge_smax_df = pd.merge(arcid_df, smax_df, on=['lat', 'lon'], how='left')
    max_gw_recharge_df = pd.merge(arcid_df, max_gw_recharge_df, on=['lat', 'lon'], how='left')

    # Adjust temperature values and drop rows with missing data (per 100°C)
    merge_temp_df['GTEMP_1971_2000'] = merge_temp_df['GTEMP_1971_2000'] * 100
    merge_temp_df = merge_temp_df.astype(int)

    # =============================================================================
    # Export the merged data
    # =============================================================================
    # Save the merged DataFrame to a CSV file
    merge_temp_df.to_csv(out_path+"GTEMP_1971_2000.csv", sep=',', index=False)
    merge_smax_df.to_csv(out_path+"max_soil_water_content.csv", sep=',', index=False)
    max_gw_recharge_df.to_csv(out_path+"max_groundwater_recharge.csv", sep=',', index=False) 
