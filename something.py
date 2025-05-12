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

def build_timetable(trips_df, stop_times_df, stops_df):
    merged = pd.merge(trips_df[['trip_id']], stop_times_df, on='trip_id')

    if 'stop_sequence' not in merged.columns:
        raise KeyError("'stop_sequence' column not found in merged DataFrame")

    merged['stop_sequence'] = merged['stop_sequence'].astype(int)
    merged = merged.sort_values(by=['trip_id', 'stop_sequence'])

    pivot = merged.pivot(index='stop_id', columns='trip_id', values='departure_time')

    # Preserve stop sequence order
    stop_order = (
        merged[['stop_id', 'stop_sequence']]
        .drop_duplicates()
        .sort_values('stop_sequence')
        .drop_duplicates('stop_id', keep='first')
        .set_index('stop_id')
    )
    pivot = pivot.loc[stop_order.index]

    # Join stop names
    stop_names = stops_df.set_index("stop_id")["stop_name"]
    pivot.index = [stop_names.get(sid, sid) for sid in pivot.index]

    return pivot

# Build both directions
inbound_table = build_timetable(inbound, stop_times, stops)
outbound_table = build_timetable(outbound, stop_times, stops)

# --- HTML rendering ---
html_template = """
<!DOCTYPE html>
<html>
<head>
    <title>{{ title }}</title>
    <style>
        body { font-family: sans-serif; padding: 20px; }
        table { border-collapse: collapse; width: 100%; font-size: 12px; }
        th, td { border: 1px solid #ccc; padding: 4px; text-align: center; }
        th { background: #eee; position: sticky; top: 0; }
        td:first-child { text-align: left; }
    </style>
</head>
<body>
<h2>{{ title }}</h2>
<table>
    <tr>
        <th>Station</th>
        {% for col in columns %}
            <th>{{ col }}</th>
        {% endfor %}
    </tr>
    {% for station, row in rows %}
    <tr>
        <td>{{ station }}</td>
        {% for cell in row %}
            <td>{{ cell or "" }}</td>
        {% endfor %}
    </tr>
    {% endfor %}
</table>
</body>
</html>
"""

def save_html(df, title, filename):
    tmpl = Template(html_template)
    html = tmpl.render(
        title=title,
        columns=df.columns.tolist(),
        rows=list(df.iterrows())
    )
    with open(filename, "w") as f:
        f.write(html)

# Save both timetables
save_html(inbound_table, "UP-W Inbound Weekday Schedule", "upw_inbound_weekday.html")
save_html(outbound_table, "UP-W Outbound Weekday Schedule", "upw_outbound_weekday.html")
