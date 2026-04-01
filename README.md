# Weather Info Dashboard

A modern, desktop weather dashboard built with CustomTkinter. Enter a city name to fetch
current temperature, humidity, and wind speed using the StormGlass API. The interface
features a polished sidebar, gradient background, and responsive layout.

## Features
- City search with geocoding (Nominatim)
- Current weather metrics from StormGlass
- Clean, modern CustomTkinter UI with light/dark modes
- Threaded API calls to keep the UI responsive

## Tech Stack
- Python 3
- CustomTkinter
- Pillow
- Requests
- python-dotenv
- geopy

## Detailed Tech Stack (Why Each Is Used)
- Python 3: Provides a fast iteration loop, cross-platform support, and strong GUI/library ecosystem for desktop apps.
- CustomTkinter: Supplies modern, themed widgets on top of Tkinter for a polished UI without building a custom UI toolkit.
- Pillow: Creates custom icons and the gradient/glow background assets at runtime for a premium visual experience.
- Requests: Simplifies HTTP calls to the StormGlass API with clear, reliable networking primitives.
- python-dotenv: Loads `STORMGLASS_API_KEY` from `.env` so secrets stay out of source control.
- geopy: Converts city names to latitude/longitude using Nominatim, enabling API queries by human-friendly location input.

## Setup
1. Install dependencies:
```bash
pip install customtkinter Pillow requests python-dotenv geopy
```

2. Create a `.env` file in the project folder:
```
STORMGLASS_API_KEY=your_api_key_here
```

3. Run the app:
```bash
python weather_by_city.py
```

## Notes
- The app opens a GUI window and keeps running until you close it.
- If you see `Add STORMGLASS_API_KEY to your .env file.` in the status bar, the API key
  has not been configured.

## Project Structure
- `weather_by_city.py` — main application entry point
- `.env` — environment variables (not committed)
- `__pycache__/` — Python bytecode cache
