import os
import subprocess
import re

# Check if isimip_client is installed if not install it.
try:
    from isimip_client.client import ISIMIPClient
except ImportError:
    print("isimip_client is not installed. Installing...")
    subprocess.run(["pip", "install", "isimip-client"])
    from isimip_client.client import ISIMIPClient

# Initialize ISIMIP client
client = ISIMIPClient()

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++
# USER SHOULD MODIFY HERE 
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++
# Data is made in intervals of 10 years (eg. 1901-1910) 
# except year 1850 which starts and ends at the same year

# Common parameters for the query
common_query_params = {
    'simulation_round': 'ISIMIP3b',
    'product': 'InputData',
    'climate_forcing': 'gfdl-esm4',
    'start_year': 1901,
    'end_year': 1901
}
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++

# Function to download data using wget
def download_data(url, folder):
    command = f"wget -P {folder} {url}"
    subprocess.run(command, shell=True)

# Function to delete text files in a folder
def delete_text_files(folder):
    for file in os.listdir(folder):
        if file.endswith(".txt"):
            os.remove(os.path.join(folder, file))

# Function to fetch data for a given climate variable
def fetch_data(climate_variable):
    query_params = common_query_params.copy()
    
    # Get all keys except the last two
    keys_to_remove = list(query_params.keys())[-2:]

    # Remove the last two items from the dictionary
    for key in keys_to_remove:
        query_params.pop(key)

    query_params['climate_variable'] = climate_variable

    response = client.datasets(**query_params)
    
    urls = []
    for item in response['results'][0]['files']:
        if 'file_url' in item:
            urls.append(item.get('file_url'))
    return urls

# Function to extract year range from URL
def extract_year_range(url):
    match = re.search(r'(\d{4})_(\d{4})\.nc$', url)
    if match:
        start_year = int(match.group(1))
        end_year = int(match.group(2))
        return start_year, end_year
    return None


# List of climate variables to download
variables_to_download = ['rsds', 'rlds', 'tas', 'pr']  

# Dictionary mapping climate variables to folder names
variable_to_folder = {
    'rsds': 'rad_shortwave',
    'rlds': 'rad_longwave',
    'tas': 'temperature',
    'pr': 'precipitation'  # Added 'pr' to the mapping
}

# Download data for each variable in the list
for variable in variables_to_download:
    urls = fetch_data(variable)
    
    if not urls:
        print(f"No data found for {variable}.")
        continue
    
    cf_folder = './input_data/climate_forcing/'+variable_to_folder.get(variable)
    print(cf_folder)
    if cf_folder:
        # Delete text files in the folder before downloading
        delete_text_files(cf_folder)
    
    for url in urls:
        year_range = extract_year_range(url)
        if year_range:
            start, end = year_range
            if common_query_params['start_year'] >= start and common_query_params['end_year']<= end:
                if cf_folder:
                    download_data(url, cf_folder)
                    print(f"Downloaded {url} to {cf_folder} folder for variable {variable}.")
