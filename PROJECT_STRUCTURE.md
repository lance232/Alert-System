# Project Structure Documentation

## Overview
This project has been refactored into a clean, modular structure with separate parser modules for PHIVOLCS and PAGASA data sources.

## Directory Structure

```
AlertSystemAPI/
├── AlertSystem.py              # Main application (simplified & clean)
├── PHIVOLCS/                   # PHIVOLCS earthquake parser module
│   ├── __init__.py            # Module exports
│   └── parser.py              # Earthquake data fetching & parsing
├── PAGASA/                     # PAGASA weather advisory parser module
│   ├── __init__.py            # Module exports
│   └── parser.py              # Weather advisory fetching & parsing
├── phivolcs-earthquake-api-main/  # Node.js API server
├── .env                        # Environment configuration
├── requirements.txt            # Python dependencies
└── state_phivolcs_pagasa.json # Runtime state file
```

## Module Descriptions

### AlertSystem.py (Main Application)
**Purpose**: Main entry point that orchestrates monitoring and alerting

**Responsibilities**:
- Configuration loading from environment variables
- Session management for HTTP requests
- State persistence (tracking seen events)
- Email alert formatting and sending
- Main monitoring loop
- Console output formatting
- Event filtering (age, freshness, deduplication)

**Key Functions**:
- `main()` - Main monitoring loop
- `sendAlertEmail()` - Email notification dispatcher
- `formatEarthquakeEmail()` - HTML email formatter for earthquakes
- `formatPagasaEmail()` - HTML email formatter for weather advisories
- `makeSession()` - Configured HTTP session factory
- `loadState()` / `saveState()` - State persistence
- `isNew()` / `withinMaxAge()` - Event filtering

### PHIVOLCS Module
**Location**: `PHIVOLCS/parser.py`

**Purpose**: Handle all PHIVOLCS earthquake data fetching and parsing

**Exports**:
- `FetchPhivolcs()` - Main function to fetch earthquake data from API
- `WithRefreshPath()` - URL helper to force refresh

**Features**:
- Fetches from local Node.js PHIVOLCS API
- Normalizes earthquake data into standardized format
- Creates unique earthquake IDs based on time + coordinates
- Handles API metadata (cached status, last updated time)
- Sorts events by recency

**Data Format**:
```python
{
    "source": "PHIVOLCS",
    "id": "2026-03-10T08:30:00|14.123|121.456",
    "time": "2026-03-10 08:30:00",
    "latitude": "14.123",
    "longitude": "121.456",
    "depth": "10 kilometers",
    "magnitude": "5.3",
    "location": "12 km NW of Cebu City",
    "_dt": datetime_object
}
```

### PAGASA Module
**Location**: `PAGASA/parser.py`

**Purpose**: Handle all PAGASA weather advisory fetching and parsing

**Exports**:
- `fetch_pagasa_visprsd()` - Fetches HTML from PAGASA Visayas PRSD page
- `parse_visprsd_cebu_advisories()` - Parses Cebu-specific advisories
- `ExtractHRWStatus()` - Extracts Heavy Rainfall Warning status text

**Features**:
- Multi-endpoint failover (tries backup URLs)
- Parses Thunderstorm Advisories mentioning Cebu
- Parses Heavy Rainfall Warnings for Cebu
- Extracts advisory numbers and issued times
- Identifies affected LGUs (Local Government Units) in Cebu
- BeautifulSoup HTML parsing with regex pattern matching

**Data Format**:
```python
{
    "source": "PAGASA",
    "type": "Thunderstorm Advisory",
    "number": "42",
    "issued": "2026-03-10T14:30:00",
    "mentions_cebu": True,
    "cebu_places": ["Cebu City", "Mandaue City", "Lapu-Lapu City"],
    "raw": "Full advisory text..."
}
```

## Benefits of This Structure

### 1. **Separation of Concerns**
- Main application focuses on orchestration and alerting
- Parsers encapsulate domain-specific logic
- Each module has a single, clear responsibility

### 2. **Maintainability**
- Parser logic isolated in dedicated modules
- Easier to locate and update parsing logic
- Changes to one parser don't affect the other

### 3. **Testability**
- Parsers can be tested independently
- Mock data can be easily injected
- Unit tests can focus on specific functionality

### 4. **Reusability**
- Parser modules can be imported by other scripts
- Functions can be reused for different use cases
- Clean API through `__init__.py` exports

### 5. **Readability**
- Main file is significantly shorter (~400 lines → shorter)
- Code organization matches logical structure
- Clear imports show module dependencies

### 6. **Documentation**
- Each module has comprehensive docstrings
- Type hints throughout for better IDE support
- Clearer separation makes documentation easier

## Usage Examples

### Import and Use PHIVOLCS Parser
```python
from PHIVOLCS import FetchPhivolcs

earthquakes, meta = FetchPhivolcs(
    apiURL="http://localhost:3001/api/earthquakes",
    force_refresh=False
)

for quake in earthquakes:
    print(f"M{quake['magnitude']} at {quake['location']}")
```

### Import and Use PAGASA Parser
```python
import requests
from PAGASA import fetch_pagasa_visprsd, parse_visprsd_cebu_advisories

session = requests.Session()
html = fetch_pagasa_visprsd(session)
advisories = parse_visprsd_cebu_advisories(html)

for advisory in advisories:
    print(f"{advisory['type']} #{advisory['number']}")
    print(f"  Affects: {', '.join(advisory['cebu_places'])}")
```

## Next Steps

### Recommended Enhancements:
1. **Add Unit Tests**: Create test files for each parser module
2. **Add Logging**: Replace print statements with proper logging
3. **Add More Parsers**: Create modules for other regions or alert types
4. **Configuration Module**: Move configuration logic to separate module
5. **Database Integration**: Add option to log events to database

### Future Module Ideas:
- `notifications/` - SMS, push notification handlers
- `filters/` - Configurable event filtering rules
- `formatters/` - Different output formats (Slack, Discord, etc.)
- `storage/` - Database or cloud storage integrations
