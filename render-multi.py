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

# Merge stop_times with trips
all_stop_times = pd.merge(stop_times, trips[['trip_id', 'direction_id', 'service_id']], on='trip_id')

# Find stop_id for Chicago OTC
chicago_stop_id = stops[stops["stop_name"] == "Chicago OTC"]["stop_id"].values[0]

# --- Create time pairs ---
time_pairs = []
trip_groups = all_stop_times[all_stop_times["service_id"].isin(weekday_services)].groupby("trip_id")
for trip_id, group in trip_groups:
    group = group.sort_values("stop_sequence")
    stop_ids = group["stop_id"].values
    if chicago_stop_id in stop_ids:
        for dest_stop_id in stop_ids:
            if dest_stop_id == chicago_stop_id:
                continue
            chicago_time = group[group["stop_id"] == chicago_stop_id]["departure_time"].values[0][:-3]
            dest_time = group[group["stop_id"] == dest_stop_id]["departure_time"].values[0][:-3]
            direction = group["direction_id"].values[0]
            time_label = f"{chicago_time} -> {dest_time}" if direction == 0 else f"{dest_time} -> {chicago_time}"
            stop_name = stops[stops["stop_id"] == dest_stop_id]["stop_name"].values[0]
            time_pairs.append({"trip_id": trip_id, "time": time_label, "direction": direction, "station": stop_name})

# Convert to DataFrame
schedule_df = pd.DataFrame(time_pairs)

# --- HTML rendering with JavaScript filtering ---
html_template = """
<!DOCTYPE html>
<html>
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>UP-W Schedule</title>
    <style>
        body { font-family: sans-serif; padding: 20px; margin: 0; }
        h2 { font-size: 1.4em; text-align: center; margin-bottom: 20px; }
        select { font-size: 16px; margin: 0 auto 20px auto; display: block; }
        table { border-collapse: collapse; font-size: 16px; width: 80%; margin: 0 auto; }
        th, td { border: 1px solid #ccc; padding: 10px; text-align: center; }
        th { background: #eee; }
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
<h2>UP-W Departures</h2>
<label for="stationPicker">Select a Station:</label>
<select id="stationPicker" onchange="updateTable()">
    <option value="">-- Choose a Station --</option>
    {% for station in stations %}<option value="{{ station }}">{{ station }}</option>{% endfor %}
</select>
<table id="scheduleTable">
    <thead><tr><th>Departure Window</th></tr></thead>
    <tbody></tbody>
</table>
<script>
const schedule = {{ schedule_json | safe }};
function updateTable() {
    const station = document.getElementById('stationPicker').value;
    const tbody = document.querySelector('#scheduleTable tbody');
    tbody.innerHTML = '';
    if (!station) return;
    const rows = schedule.filter(r => r.station === station);
    rows.forEach(row => {
        const tr = document.createElement('tr');
        const td = document.createElement('td');
        td.textContent = row.time;
        td.setAttribute('data-tooltip', `Trip ID: ${row.trip_id}`);
        tr.appendChild(td);
        tbody.appendChild(tr);
    });
}
</script>
</body>
</html>
"""

from jinja2 import Template
html = Template(html_template).render(
    schedule_json=schedule_df.to_dict(orient="records"),
    stations=sorted(schedule_df["station"].unique())
)

with open("upw_schedule_interactive.html", "w") as f:
    f.write(html)
