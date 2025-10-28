# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Metra timetable generator that processes GTFS (General Transit Feed Specification) data to create HTML timetables for Chicago's Metra train system. The project fetches real-time schedule data and generates filtered timetables for specific stations across multiple train lines.

## Available Applications

### 1. Multi-Line Version (Recommended)
- **Frontend**: `index.html` - Supports all 11 Metra lines with line selection dropdown
- **Data Generator**: `render-all-lines.py` - Processes all available Metra routes
- **Data Files**: `metra_all_schedule_data.json`, `metra_routes.json`, `metra_metadata.json`

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
  - `metra_metadata.json`: Metadata about data generation and schedule validity dates
- UP-W specific version (legacy):
  - `upw_schedule_data.json`: UP-W schedule data only

### Features
Both versions include:
- Real-time countdown to next departure
- Train number badges with smaller font styling
- Departure status tracking (departed trains grayed out)
- Persistent user preferences via localStorage
- Responsive design with sticky header

## Future Features (Planned)

### 1. Real-Time Delay Information
**Goal**: Display live delay/status information from Metra's real-time API

**Design philosophy**: Minimal and unobtrusive
- Only show real-time info for imminent trains (e.g., next 1-2 hours)
- Real-time data far in the future is not useful or reliable
- Simple notation in the timetable cell (e.g., "+5 min", "On time", "Delayed")

**Implementation considerations**:
- API endpoint discovery: Research Metra's real-time API (likely GTFS-RT feed)
  - TO DO: Google search for Metra GTFS-RT or real-time API
- Polling strategy: Refresh every 30-60 seconds for upcoming trains only
- UI integration (minimal approach):
  - Small text notation in timetable cell for trains departing soon
  - Only display for trains within ~60-90 minutes of current time
  - Examples: "On time", "+3 min", "Delayed 15 min", "Cancelled"
  - Optional: Subtle color coding (green=on-time, yellow=minor delay, red=major delay)
- Data matching: Map real-time trip IDs to static schedule trip IDs
- Error handling: Graceful degradation when API unavailable (just hide real-time info)
- Performance: Only fetch/process real-time data for currently displayed route/station

**Technical approach**:
- Frontend polling mechanism using setInterval (every 60s)
- Only fetch real-time data when page is visible (use Page Visibility API)
- CORS considerations (may need proxy if API doesn't allow direct browser access)
- Filter real-time updates to only upcoming trains (ignore far-future predictions)
- Cache API responses to reduce redundant calls

**Research needed**:
- Metra real-time API endpoint (GTFS-RT feed location)
- Authentication requirements (API key?)
- Data format (GTFS-RT protobuf vs JSON)
- Rate limits and usage terms

### 2. Weekend Schedule Support
**Goal**: Allow users to view Saturday and Sunday schedules in addition to weekdays

**Implementation considerations**:
- Schedule selection UI:
  - Option A: Radio buttons (Weekday/Saturday/Sunday) in header
  - Option B: Dropdown selector
  - Option C: Auto-detect based on current day with manual override
- Data processing changes:
  - Modify `render-all-lines.py` to process multiple service types
  - Current code filters for services where monday-friday=1, saturday/sunday=0
  - Need to create separate datasets or include service_type field
  - calendar.txt has service patterns: A2 (Sat+Sun), A3 (Sat only), A4 (Sun only)
- JSON structure options:
  - Option A: Separate files (metra_weekday.json, metra_saturday.json, metra_sunday.json)
  - Option B: Single file with service_type field, filter in frontend
  - Option C: Hybrid - metadata indicates available services, lazy-load each
- UI considerations:
  - Weekend schedules often have fewer trains - may result in sparser tables
  - Some routes may not operate on weekends (need to handle gracefully)
  - Persistence: Remember user's schedule preference via localStorage
- Countdown timer adjustments:
  - Should work correctly when viewing non-current day schedules
  - May need to disable/modify countdown when viewing "future" schedules

**Technical approach**:
1. Update `render-all-lines.py` to accept service type parameter
2. Create three separate JSON outputs or one unified format
3. Add UI controls in header for schedule selection
4. Modify loadData() to fetch appropriate schedule
5. Update updateTable() to filter/display correct service type
6. Consider showing "viewing Saturday schedule" indicator when not current day

**Open questions**:
- Preferred UI for schedule selection?
- Should app auto-select current day or always default to weekday?
- Single unified JSON vs separate files per service type?
- How to handle routes with no weekend service?