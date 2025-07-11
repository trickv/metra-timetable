import pandas as pd
from jinja2 import Template
from datetime import date
import sys

# Load GTFS CSVs
routes = pd.read_csv("metra-gtfs/routes.txt", skipinitialspace=True)
trips = pd.read_csv("metra-gtfs/trips.txt", skipinitialspace=True)
stop_times = pd.read_csv("metra-gtfs/stop_times.txt", skipinitialspace=True)
stops = pd.read_csv("metra-gtfs/stops.txt", skipinitialspace=True)
calendar = pd.read_csv("metra-gtfs/calendar.txt", skipinitialspace=True)

# --- STEP 1: Find active weekday services ---
today_str = date.today().strftime("%Y%m%d")
weekday_services = calendar[
    (calendar['monday'].astype(int) == 1) &
    (calendar['tuesday'].astype(int) == 1) &
    (calendar['wednesday'].astype(int) == 1) &
    (calendar['thursday'].astype(int) == 1) &
    (calendar['friday'].astype(int) == 1) &
    (calendar['saturday'].astype(int) == 0) &
    (calendar['sunday'].astype(int) == 0) &
    (calendar['start_date'].astype(int) <= int(today_str)) &
    (calendar['end_date'].astype(int) >= int(today_str))
]['service_id'].tolist()

# --- STEP 2: Filter UP-W trips on valid weekdays ---
if 'service_id' not in trips.columns:
    raise KeyError("'service_id' column not found in trips.txt")

upw_trips = trips[
    (trips["route_id"] == "UP-W") &
    (trips["service_id"].isin(weekday_services))
]

# --- STEP 3: Inbound and outbound trips ---
inbound = upw_trips[upw_trips["direction_id"] == 1]
outbound = upw_trips[upw_trips["direction_id"] == 0]

# Merge stop_times with trips
all_stop_times = pd.merge(stop_times, trips[['trip_id', 'direction_id', 'service_id']], on='trip_id')

# Join stop names
stop_names = stops.set_index("stop_id")["stop_name"].to_dict()

# Get the station name to filter from command-line argument
if len(sys.argv) != 2:
    print("Usage: python something.py 'Station Name'")
    sys.exit(1)

selected_station = sys.argv[1]
selected_stop_id = stops[stops["stop_name"] == selected_station]["stop_id"].values
if len(selected_stop_id) == 0:
    print(f"Station '{selected_station}' not found.")
    sys.exit(1)
selected_stop_id = selected_stop_id[0]

# Find stop_id for Chicago OTC
chicago_stop_id = stops[stops["stop_name"] == "Chicago OTC"]["stop_id"].values[0]

# Filter stop_times to selected station
filtered_stop_times = all_stop_times[
    (all_stop_times["stop_id"].isin([selected_stop_id, chicago_stop_id])) &
    (all_stop_times["service_id"].isin(weekday_services))
].copy()

# --- Create time pairs ---
time_pairs = []
trip_groups = filtered_stop_times.groupby("trip_id")
for trip_id, group in trip_groups:
    group = group.sort_values("stop_sequence")
    stop_ids = group["stop_id"].values
    if chicago_stop_id in stop_ids and selected_stop_id in stop_ids:
        chicago_time = group[group["stop_id"] == chicago_stop_id]["departure_time"].values[0][:-3]
        dest_time = group[group["stop_id"] == selected_stop_id]["departure_time"].values[0][:-3]
        direction = group["direction_id"].values[0]
        if direction == 1:
            time_label = f"{dest_time} -> {chicago_time}"
        else:
            time_label = f"{chicago_time} -> {dest_time}"
        time_pairs.append({"trip_id": trip_id, "time": time_label, "direction": direction})

# Convert to DataFrame
filtered_df = pd.DataFrame(time_pairs)

# Filter inbound and outbound
filtered_inbound = filtered_df[filtered_df["direction"] == 1]
filtered_outbound = filtered_df[filtered_df["direction"] == 0]

# --- HTML rendering ---
html_template = """
<!DOCTYPE html>
<html>
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{{ title }}</title>
    <style>
        body {
            font-family: sans-serif;
            padding: 20px;
            margin: 0;
        }
        h2 {
            font-size: 1.4em;
            text-align: center;
            word-wrap: break-word;
            margin-bottom: 20px;
        }
        table {
            border-collapse: collapse;
            font-size: 16px;
            width: 80%;
            margin: 0 auto;
        }
        th, td {
            border: 1px solid #ccc;
            padding: 10px;
            text-align: center;
        }
        th {
            background: #eee;
        }
        td:hover::after {
            content: attr(data-tooltip);
            position: absolute;
            background: #333;
            color: #fff;
            padding: 2px 6px;
            border-radius: 4px;
            white-space: nowrap;
            font-size: 12px;
            transform: translateX(10px) translateY(-10px);
            z-index: 9999;
        }
    </style>
</head>

<body>
<h2>{{ title }}</h2>
<table>
    <tr><th>{{ station }}</th></tr>
    {% for time, tooltip in times %}
    <tr><td data-tooltip="Trip ID: {{ tooltip }}">{{ time }}</td></tr>
    {% endfor %}
</table>
</body>
</html>
"""

def save_vertical_html(df, title, station, filename):
    tmpl = Template(html_template)
    html = tmpl.render(
        title=title,
        station=station,
        times=zip(df["time"], df["trip_id"])
    )
    with open(filename, "w") as f:
        f.write(html)

# Save both filtered timetables
save_vertical_html(
    filtered_inbound,
    f"UP-W Inbound Departures - {selected_station}",
    selected_station,
    "upw_inbound_filtered.html"
)
save_vertical_html(
    filtered_outbound,
    f"UP-W Outbound Departures from Chicago OTC to {selected_station}",
    selected_station,
    "upw_outbound_filtered.html"
)
