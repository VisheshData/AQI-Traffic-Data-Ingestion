import time

def your_script():
    # Your Python script code here
    print("Executing the script...")
    import requests
    import pandas as pd
    from datetime import datetime
    import gspread
    from oauth2client.service_account import ServiceAccountCredentials

    # Function to fetch AQI data
    def fetch_aqi_data(token, latlngbox):
        base_url = "https://api.waqi.info"
        r = requests.get(base_url + f"/map/bounds/?latlng={latlngbox}&token={token}")
        return r

    # Function to create DataFrame from AQI data
    def make_dataframe(r):
        rows = []
        for item in r.json()['data']:
            rows.append([item['lat'], item['lon'], item['aqi'], item['station']['name']])
        df = pd.DataFrame(rows, columns=['lat', 'lon', 'aqi', 'name'])
        df['aqi'] = pd.to_numeric(df.aqi, errors='coerce')
        df['timestamp'] = datetime.now()
        return df

    # Function to fetch traffic data
    def fetch_traffic_data(df, tomtom_api_key, radius):
        traffic_data_list = []
        for index, row in df.iterrows():
            LAT = row['lat']
            LON = row['lon']
            traffic_url = f"https://api.tomtom.com/traffic/services/4/flowSegmentData/absolute/10/json?point={LAT}%2C{LON}&radius={radius}&key={tomtom_api_key}"
            traffic_response = requests.get(traffic_url)

            if traffic_response.status_code == 200:
                traffic_data = traffic_response.json().get('flowSegmentData', {})
                traffic_data_list.append({
                    'frc': traffic_data.get('frc'),
                    'currentSpeed': traffic_data.get('currentSpeed'),
                    'freeFlowSpeed': traffic_data.get('freeFlowSpeed'),
                    'currentTravelTime': traffic_data.get('currentTravelTime'),
                    'freeFlowTravelTime': traffic_data.get('freeFlowTravelTime'),
                    'confidence': traffic_data.get('confidence'),
                    'roadClosure': traffic_data.get('roadClosure'),
                    'lat': LAT,
                    'lon': LON
                })
            else:
                traffic_data_list.append({
                    'frc': None,
                    'currentSpeed': None,
                    'freeFlowSpeed': None,
                    'currentTravelTime': None,
                    'freeFlowTravelTime': None,
                    'confidence': None,
                    'roadClosure': None,
                    'lat': LAT,
                    'lon': LON
                })
        return pd.DataFrame(traffic_data_list)

    import numpy as np

    # Function to update Google Sheets
    def update_google_sheet(merged_df, creds_file, sheet_id):
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_name(creds_file, scope)
        client = gspread.authorize(creds)
        sheet = client.open_by_key(sheet_id).sheet1

        # Replace NaN and inf values with None
        merged_df.replace([np.inf, -np.inf], np.nan, inplace=True)
        merged_df = merged_df.where(pd.notnull(merged_df), None)

        for index, row in merged_df.iterrows():
            row_data = row.tolist()
            for i, value in enumerate(row_data):
                if isinstance(value, datetime):
                    row_data[i] = value.isoformat()
                elif value is None:
                    row_data[i] = ""
                else:
                    row_data[i] = str(value)
            sheet.append_row(row_data)

    # Main script
    if __name__ == "__main__":
        # Read secret token from file
        token = "f2b37c532037c9afb8bd3bf0caadbddca1a75741"
        latlngbox = "28.402,76.838,28.883,77.348"

        # Fetch AQI data
        r = fetch_aqi_data(token, latlngbox)
        df = make_dataframe(r)

        # Fetch traffic data
        TOMTOM_API_KEY = 'GgQ1W4Fwe9AruIX6rwtM7vJdHqeFo3pa'
        RADIUS = 2000
        traffic_df = fetch_traffic_data(df, TOMTOM_API_KEY, RADIUS)

        # Merge dataframes
        merged_df = pd.merge(df, traffic_df, on=['lat', 'lon'], how='inner')
        merged_df['timestamp'] = merged_df['timestamp'].astype(str)

        # Update Google Sheets
        creds_file = 'cred_file.json'  # Path to your Google Sheets API credentials JSON file
        sheet_id = '1oe78_HdeBeXWorYuLRHyUEo0LctRSeqPXwqE4FjGamg'  # Your Google Sheet ID
        update_google_sheet(merged_df, creds_file, sheet_id)



def run_script_with_delay(script_function, delay, repetitions):
    for i in range(repetitions):
        # Run the script function
        script_function()

        # Wait for the specified delay before running the script again
        if i < repetitions - 1:
            time.sleep(delay)

    print("Completed all repetitions.")

# Example usage
delay_in_seconds = 3600  # Delay between repetitions in seconds
number_of_repetitions = 24  # Number of times to repeat the script

run_script_with_delay(your_script, delay_in_seconds, number_of_repetitions)
