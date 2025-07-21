import pandas as pd
from jinja2 import Template
from datetime import date

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

# --- STEP 2: Filter UP-W trips ---
if 'service_id' not in trips.columns:
    raise KeyError("'service_id' column not found in trips.txt")

upw_trips_all = trips[trips["route_id"] == "UP-W"]
upw_trips_today = upw_trips_all[upw_trips_all["service_id"].isin(weekday_services)]

# Merge all stop_times with full UP-W trips
all_stop_times = pd.merge(stop_times, upw_trips_all[['trip_id', 'direction_id', 'service_id']], on='trip_id')

# Determine unique stop_ids for UP-W route
upw_stop_ids = stop_times[stop_times["trip_id"].isin(upw_trips_all["trip_id"])]
upw_stop_ids = upw_stop_ids["stop_id"].unique()

# Convert to stop names
upw_stops = stops[stops["stop_id"].isin(upw_stop_ids)].copy()
upw_stops = upw_stops.sort_values("stop_sequence") if "stop_sequence" in upw_stops.columns else upw_stops

# Find stop_id for Chicago OTC
chicago_stop_id = stops[stops["stop_name"] == "Chicago OTC"]["stop_id"].values[0]

# Filter stop_times for today and Chicago OTC + any destination stop on UP-W
filtered_stop_times = stop_times[stop_times["trip_id"].isin(upw_trips_today["trip_id"])]
filtered_stop_times = pd.merge(filtered_stop_times, upw_trips_today[['trip_id', 'direction_id']], on='trip_id')

# Group by trip and extract times
time_rows = []
for trip_id, group in filtered_stop_times.groupby("trip_id"):
    group = group.sort_values("stop_sequence")
    stop_ids = group["stop_id"].values
    if chicago_stop_id in stop_ids:
        for dest_stop_id in stop_ids:
            if dest_stop_id != chicago_stop_id:
                direction = group["direction_id"].iloc[0]
                try:
                    chicago_time = group[group["stop_id"] == chicago_stop_id]["departure_time"].values[0][:-3]
                    dest_time = group[group["stop_id"] == dest_stop_id]["departure_time"].values[0][:-3]
                    
                    # Get stop names
                    dest_stop_name = stops[stops["stop_id"] == dest_stop_id]["stop_name"].values[0]
                    chicago_stop_name = stops[stops["stop_id"] == chicago_stop_id]["stop_name"].values[0]
                    
                    # Create start->end time format
                    if direction == 1:  # To Chicago
                        time_display = f"{dest_time} -> {chicago_time}"
                    else:  # From Chicago
                        time_display = f"{chicago_time} -> {dest_time}"
                    
                    time_rows.append({
                        "trip_id": trip_id,
                        "from": dest_stop_name if direction == 1 else chicago_stop_name,
                        "to": chicago_stop_name if direction == 1 else dest_stop_name,
                        "time": time_display,
                        "direction": direction
                    })
                except IndexError:
                    continue

# Convert to DataFrame and save for frontend use
schedule_df = pd.DataFrame(time_rows)
schedule_df.to_json("upw_schedule_data.json", orient="records")
