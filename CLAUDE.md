# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Metra timetable generator that processes GTFS (General Transit Feed Specification) data to create HTML timetables for Chicago's Metra UP-W (Union Pacific West) line. The project fetches real-time schedule data and generates filtered timetables for specific stations.

## Key Components

- **get-schedule.sh**: Downloads and extracts the latest GTFS schedule data from Metra's API
- **render-multi.py**: Generates JSON schedule data for frontend consumption, focusing on Chicago OTC as the central hub
- **render-static-version.py**: Creates filtered HTML timetables for specific stations with inbound/outbound departures
- **requirements.txt**: Python dependencies (jinja2, pandas)

## Common Commands

### Setup Environment
```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Linux/Mac
# or
venv\Scripts\activate     # On Windows

# Install dependencies
pip install -r requirements.txt
```

### Data Operations
```bash
# Download latest GTFS data
./get-schedule.sh

# Generate JSON schedule data
python render-multi.py

# Generate HTML timetable for specific station
python render-static-version.py "Station Name"
```

## Architecture

The project follows a data pipeline approach:

1. **Data Acquisition**: `get-schedule.sh` fetches GTFS data from Metra and extracts it to `metra-gtfs/`
2. **Data Processing**: Both Python scripts read GTFS CSV files (routes.txt, trips.txt, stop_times.txt, stops.txt, calendar.txt) using pandas
3. **Schedule Filtering**: Scripts filter for UP-W route, weekday services, and specific direction/station combinations
4. **Output Generation**: Creates either JSON data files or HTML timetables with Jinja2 templates

### Key Data Flow
- Both scripts identify active weekday services based on current date
- UP-W route trips are filtered by service_id and direction_id
- Chicago OTC serves as the central hub for all schedule calculations
- Times are formatted by removing seconds (`:XX` suffix)

### File Structure
- `metra-gtfs/`: Contains downloaded GTFS CSV files
- `upw_schedule.json`: Generated schedule data for frontend
- `upw_stations.json`: Station list for frontend
- `upw_inbound_filtered.html`: Inbound departures for specific station
- `upw_outbound_filtered.html`: Outbound departures for specific station