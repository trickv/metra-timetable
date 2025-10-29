import pandas as pd
from jinja2 import Template
from datetime import date, datetime
import re
import json
import os

def parse_train_number(route_id, trip_id):
    """Parse train number from trip_id based on route patterns"""
    patterns = {
        'UP-W': r'UW(\d+)',
        'UP-N': r'UN(\d+)', 
        'UP-NW': r'UNW(\d+)',
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

# --- STEP 1: Find active services for each schedule type ---
today_str = date.today().strftime("%Y%m%d")

# Define service types
service_types = {
    'weekday': {
        'filters': {
            'monday': 1, 'tuesday': 1, 'wednesday': 1,
            'thursday': 1, 'friday': 1, 'saturday': 0, 'sunday': 0
        }
    },
    'saturday': {
        'filters': {
            'monday': 0, 'tuesday': 0, 'wednesday': 0,
            'thursday': 0, 'friday': 0, 'saturday': 1, 'sunday': 0
        }
    },
    'sunday': {
        'filters': {
            'monday': 0, 'tuesday': 0, 'wednesday': 0,
            'thursday': 0, 'friday': 0, 'saturday': 0, 'sunday': 1
        }
    }
}

def get_services_for_type(service_type_name):
    """Get service IDs for a given schedule type"""
    filters = service_types[service_type_name]['filters']
    mask = (
        (calendar['monday'].astype(int) == filters['monday']) &
        (calendar['tuesday'].astype(int) == filters['tuesday']) &
        (calendar['wednesday'].astype(int) == filters['wednesday']) &
        (calendar['thursday'].astype(int) == filters['thursday']) &
        (calendar['friday'].astype(int) == filters['friday']) &
        (calendar['saturday'].astype(int) == filters['saturday']) &
        (calendar['sunday'].astype(int) == filters['sunday']) &
        (calendar['start_date'].astype(int) <= int(today_str)) &
        (calendar['end_date'].astype(int) >= int(today_str))
    )
    return calendar[mask]['service_id'].tolist()

# Get all available route IDs
available_routes = routes['route_id'].tolist()
print(f"Processing {len(available_routes)} routes: {', '.join(available_routes)}")

# Process each schedule type
for schedule_type in ['weekday', 'saturday', 'sunday']:
    print(f"\n=== Processing {schedule_type.upper()} schedule ===")

    active_services = get_services_for_type(schedule_type)
    print(f"Found {len(active_services)} active {schedule_type} services")

    if not active_services:
        print(f"No {schedule_type} services found, skipping")
        continue

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

        # Filter trips for this route and schedule type
        route_trips_all = trips[trips["route_id"] == route_id]
        route_trips_today = route_trips_all[route_trips_all["service_id"].isin(active_services)]

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
    print(f"Generated {len(all_schedule_data)} {schedule_type} schedule entries")
    schedule_df = pd.DataFrame(all_schedule_data)

    if not schedule_df.empty:
        # Save schedule data for this type
        output_filename = f"metra_all_schedule_data_{schedule_type}.json"
        schedule_df.to_json(output_filename, orient="records")
        print(f"Data saved to {output_filename}")
        print(f"Routes processed: {schedule_df['route_id'].nunique()}")
    else:
        print(f"No {schedule_type} schedule data generated")

# Save route information for frontend (only once)
routes_info = routes[['route_id', 'route_short_name', 'route_long_name', 'route_color']].to_dict('records')
pd.DataFrame(routes_info).to_json("metra_routes.json", orient="records")

# Create metadata file with generation time and schedule validity
gtfs_zip_path = "metra-gtfs/schedule.zip"
gtfs_mtime = datetime.fromtimestamp(os.path.getmtime(gtfs_zip_path)) if os.path.exists(gtfs_zip_path) else None

# Get schedule validity range from calendar
start_dates = calendar['start_date'].astype(str).tolist()
end_dates = calendar['end_date'].astype(str).tolist()
earliest_start = min(start_dates)
latest_end = max(end_dates)

metadata = {
    "generated_at": datetime.now().isoformat(),
    "gtfs_downloaded_at": gtfs_mtime.isoformat() if gtfs_mtime else None,
    "schedule_valid_from": f"{earliest_start[:4]}-{earliest_start[4:6]}-{earliest_start[6:]}",
    "schedule_valid_until": f"{latest_end[:4]}-{latest_end[4:6]}-{latest_end[6:]}",
}

with open("metra_metadata.json", "w") as f:
    json.dump(metadata, f, indent=2)

print("\nAll schedule types processed successfully!")
print(f"Metadata saved to metra_metadata.json")