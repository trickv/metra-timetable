import pandas as pd
from jinja2 import Template
from datetime import date
import re

def parse_train_number(route_id, trip_id):
    """Parse train number from trip_id based on route patterns"""
    patterns = {
        'UP-W': r'UW(\d+)',
        'UP-N': r'UN(\d+)', 
        'UP-NW': r'UPN(\d+)',
        'BNSF': r'BN(\d+)',
        'MD-W': r'MW(\d+)',
        'MD-N': r'MN(\d+)',
        'ME': r'ME(\d+)',
        'RI': r'RI(\d+)',
        'NCS': r'NC(\d+)',
        'SWS': r'SW(\d+)',
        'HC': r'HC(\d+)'
    }
    
    pattern = patterns.get(route_id)
    if pattern:
        match = re.search(pattern, trip_id)
        return match.group(1) if match else None
    return None

def get_central_hub(route_id):
    """Get the central hub station for each route"""
    # Most routes use Chicago Union Station, UP lines use Chicago OTC
    if route_id.startswith('UP-'):
        return "Chicago OTC"
    else:
        return "Chicago Union Station"

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

# Get all available route IDs
available_routes = routes['route_id'].tolist()
print(f"Processing {len(available_routes)} routes: {', '.join(available_routes)}")

all_schedule_data = []

# Process each route
for route_id in available_routes:
    print(f"Processing route: {route_id}")
    
    # Get central hub for this route
    central_hub_name = get_central_hub(route_id)
    central_hub_stop = stops[stops["stop_name"] == central_hub_name]
    
    if central_hub_stop.empty:
        print(f"Warning: Central hub '{central_hub_name}' not found for route {route_id}")
        continue
        
    central_hub_id = central_hub_stop["stop_id"].values[0]
    
    # Filter trips for this route
    route_trips_all = trips[trips["route_id"] == route_id]
    route_trips_today = route_trips_all[route_trips_all["service_id"].isin(weekday_services)]
    
    if route_trips_today.empty:
        print(f"No active trips found for route {route_id}")
        continue
    
    # Get all stop_times for this route
    route_stop_times = stop_times[stop_times["trip_id"].isin(route_trips_today["trip_id"])]
    route_stop_times = pd.merge(route_stop_times, route_trips_today[['trip_id', 'direction_id']], on='trip_id')
    
    # Group by trip and extract times
    for trip_id, group in route_stop_times.groupby("trip_id"):
        group = group.sort_values("stop_sequence")
        stop_ids = group["stop_id"].values
        
        if central_hub_id in stop_ids:
            for dest_stop_id in stop_ids:
                if dest_stop_id != central_hub_id:
                    direction = group["direction_id"].iloc[0]
                    try:
                        hub_time = group[group["stop_id"] == central_hub_id]["departure_time"].values[0][:-3]
                        dest_time = group[group["stop_id"] == dest_stop_id]["departure_time"].values[0][:-3]
                        
                        # Get stop names
                        dest_stop_name = stops[stops["stop_id"] == dest_stop_id]["stop_name"].values[0]
                        
                        # Create start->end time format with train number
                        train_number = parse_train_number(route_id, trip_id)
                        train_label = f" (Train {train_number})" if train_number else ""
                        
                        if direction == 1:  # To central hub
                            time_display = f"{dest_time} -> {hub_time}{train_label}"
                            from_station = dest_stop_name
                            to_station = central_hub_name
                        else:  # From central hub
                            time_display = f"{hub_time} -> {dest_time}{train_label}"
                            from_station = central_hub_name
                            to_station = dest_stop_name
                        
                        all_schedule_data.append({
                            "route_id": route_id,
                            "route_name": routes[routes['route_id'] == route_id]['route_long_name'].values[0],
                            "trip_id": trip_id,
                            "train_number": train_number,
                            "from": from_station,
                            "to": to_station,
                            "time": time_display,
                            "direction": direction
                        })
                    except (IndexError, KeyError) as e:
                        continue

# Convert to DataFrame and save for frontend use
print(f"Generated {len(all_schedule_data)} schedule entries")
schedule_df = pd.DataFrame(all_schedule_data)

if not schedule_df.empty:
    # Save combined data
    schedule_df.to_json("metra_all_schedule_data.json", orient="records")
    
    # Also save route information for frontend
    routes_info = routes[['route_id', 'route_short_name', 'route_long_name', 'route_color']].to_dict('records')
    pd.DataFrame(routes_info).to_json("metra_routes.json", orient="records")
    
    print("Data saved to metra_all_schedule_data.json and metra_routes.json")
    print(f"Routes processed: {schedule_df['route_id'].nunique()}")
    print(f"Sample routes: {schedule_df['route_id'].unique()[:5]}")
else:
    print("No schedule data generated")