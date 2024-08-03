# AQI and Traffic Data Automation Project(Simple pipeline without any Cloud service. !Free)

This project automates the extraction of Air Quality Index (AQI) and traffic data, merges them, and updates the results in a Google Sheet. The script is designed to run every hour using the free PythonAnywhere's scheduled tasks feature.

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Project Setup](#project-setup)
3. [Script Explanation](#script-explanation)
   - [Latitude-Longitude Bounding Box (latlngbox)](#latitude-longitude-bounding-box-latlngbox)
   - [Fetching AQI Data](#fetching-aqi-data)
   - [Creating DataFrame from AQI Data](#creating-dataframe-from-aqi-data)
   - [Fetching Traffic Data](#fetching-traffic-data)
   - [Logic of AQICN and TOMTOM API Integration](#Logic-of-AQICN-&-TOMTOM-API-Integration)
   - [Merging AQI and Traffic Data](#merging-aqi-and-traffic-data)
   - [Updating Google Sheets](#updating-google-sheets)
4. [Automation on PythonAnywhere](#automation-on-pythonanywhere)

## Prerequisites

- Python 3.x
- `requests` library
- `pandas` library
- `gspread` library
- `oauth2client` library
- API tokens for AQICN and TomTom
- Google Sheets API credentials JSON file

## Project Setup

1. Clone the repository:
    ```sh
    git clone https://github.com/yourusername/Automated-AQI-Traffic-Data-Ingestion.git
    cd aqi-traffic-automation
    ```

2. Install the required libraries:
    ```sh
    pip install requests pandas gspread oauth2client
    ```

3. Set up your Google Sheets API credentials by following the instructions [here](https://developers.google.com/sheets/api/quickstart/python).

4. Update the `creds_file.json` path, AQICN token, TomTom API key, and Google Sheet ID in the script.

## Script Explanation

### Latitude-Longitude Bounding Box (latlngbox)

The `latlngbox` specifies the geographical area for which you want to fetch AQI data. It defines a rectangular area using the latitude and longitude of the bottom-left and top-right corners. In the script I have taken geographical area of New Delhi.

```python
latlngbox = "28.402,76.838,28.883,77.348"
```
Fetching AQI Data
The fetch_aqi_data function uses the AQICN API to fetch AQI data within the specified bounding box.
```
python

def fetch_aqi_data(token, latlngbox):
    base_url = "https://api.waqi.info"
    r = requests.get(base_url + f"/map/bounds/?latlng={latlngbox}&token={token}")
    return r
```
Creating DataFrame from AQI Data
The make_dataframe function processes the JSON response from the AQICN API and converts it into a Pandas DataFrame.
```
python

def make_dataframe(r):
    rows = []
    for item in r.json()['data']:
        rows.append([item['lat'], item['lon'], item['aqi'], item['station']['name']])
    df = pd.DataFrame(rows, columns=['lat', 'lon', 'aqi', 'name'])
    df['aqi'] = pd.to_numeric(df.aqi, errors='coerce')
    df['timestamp'] = datetime.now()
    return df
```
Fetching Traffic Data
The fetch_traffic_data function retrieves traffic data for each AQI monitoring station using the TomTom API.
```

python

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
```
### Logic of AQICN and TOMTOM API Integration
Various stations within the city give the AQI in their respective regions. In Delhi, AQICN records data from 34 stations and each station covers a radius of approx 2 km(Source- https://wri-india.org/blog/delhis-air-quality-needs-data-driven-action#:~:text=The%20State%20of%20Air%20Quality%20Data&text=Delhi%20has%2040%20Continuous%20Ambient,Air%20Monitoring%20Programs%20(NAMP)).<br> 
Hence TOMTOM API radius input in the URL which we have set to 2 km (2000 value to be given to radius variable) to see traffic issues corresponding to each station's latitude and longitude coordinates and can be correlated.

Merging AQI and Traffic Data
After fetching both AQI and traffic data, they are merged into a single DataFrame based on the station coordinates.
```
python

merged_df = pd.merge(df, traffic_df, on=['lat', 'lon'], how='inner')
merged_df['timestamp'] = merged_df['timestamp'].astype(str)
```
Updating Google Sheets
The update_google_sheet function updates a specified Google Sheet with the merged AQI and traffic data. Timestamp converted to string format(Type casting)
```
python

def update_google_sheet(merged_df, creds_file, sheet_id):
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name(creds_file, scope)
    client = gspread.authorize(creds)
    sheet = client.open_by_key(sheet_id).sheet1

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
```
In the code I am also recording timestamp which needs to be converted to isoformat and converted to string as mentioned above in the data merging part because google api is unable to serialize values other than string format values(Code can need improvement in order to solve this).


### Automation on PythonAnywhere
To automate the script using PythonAnywhere:

1. Sign up for a PythonAnywhere account.
2. Upload your script and required files (e.g., creds_file.json google sheet api credentials).
3. Go to the Tasks tab and schedule your script to run daily.
4. To simulate hourly execution, use a time.sleep loop within your script. This is required to be done within the script because free version of pythonanywhere donot allow for hourly task schedule.

## Resultant Data Image

![image](https://github.com/user-attachments/assets/6d87bdf6-bc2e-4e80-a660-1aab907299af)

### Feel free to clone it and use the code for free automated data extraction of AQI and Traffic for your city. Change the LatLon Box coordinates for your city and everything is good to go. If there are other places online where we can automate this type of data ingestion for free or without developing complex pipleine on cloud service let me know.


