# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Metra timetable generator that processes GTFS (General Transit Feed Specification) data to create HTML timetables for Chicago's Metra train system. The project fetches real-time schedule data and generates filtered timetables for specific stations across multiple train lines.

## Available Applications

### 1. Multi-Line Version (Recommended)
- **Frontend**: `index.html` - Supports all 11 Metra lines with line selection dropdown
- **Data Generator**: `render-all-lines.py` - Processes all available Metra routes
- **Data Files**: `metra_all_schedule_data.json`, `metra_routes.json`

### 2. UP-W Specific Version (Legacy)
- **Frontend**: `upw_schedule_interactive.html` - UP-W line only interface
- **Data Generator**: `render-multi.py` - UP-W focused data processing
- **Data Files**: `upw_schedule_data.json`

## Key Components

- **bootstrap.sh / bootstrap.bat**: Automated setup scripts that create virtual environment and install dependencies (Linux/Mac and Windows)
- **get-schedule.sh**: Downloads and extracts the latest GTFS schedule data from Metra's API
- **render-all-lines.py**: Generates JSON schedule data for all Metra lines (recommended)
- **render-multi.py**: Legacy UP-W specific data generator
- **requirements.txt**: Python dependencies (jinja2, pandas)

## Common Commands

### Quick Setup (Recommended)
```bash
# Linux/Mac
./bootstrap.sh

# Windows
bootstrap.bat
```

### Manual Setup Environment
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

# Generate JSON schedule data for all lines (recommended)
python render-all-lines.py

# OR generate UP-W specific data (legacy)
python render-multi.py

# Start development web server (try ports 8000, 8001, 8002, etc. until one works)
python -m http.server 8000
```

## Architecture

The project follows a data pipeline approach:

1. **Data Acquisition**: `get-schedule.sh` fetches GTFS data from Metra and extracts it to `metra-gtfs/`
2. **Data Processing**: Python scripts read GTFS CSV files (routes.txt, trips.txt, stop_times.txt, stops.txt, calendar.txt) using pandas
3. **Schedule Filtering**: Scripts filter for weekday services and specific direction/station combinations
4. **Output Generation**: Creates JSON data files for frontend consumption

### Key Data Flow
- Scripts identify active weekday services based on current date
- Route trips are filtered by service_id and direction_id
- Central hubs are identified (Chicago OTC for UP lines, Chicago Union Station for others)
- Train numbers are parsed using route-specific patterns
- Times are formatted by removing seconds (`:XX` suffix)

### File Structure
- `metra-gtfs/`: Contains downloaded GTFS CSV files
- Multi-line version:
  - `metra_all_schedule_data.json`: Schedule data for all Metra lines
  - `metra_routes.json`: Route information with colors and names
- UP-W specific version (legacy):
  - `upw_schedule_data.json`: UP-W schedule data only

### Features
Both versions include:
- Real-time countdown to next departure
- Train number badges with smaller font styling
- Departure status tracking (departed trains grayed out)
- Persistent user preferences via localStorage
- Responsive design with sticky header