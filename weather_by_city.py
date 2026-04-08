"""
requirements.txt style comment:
customtkinter>=5.2.0
Pillow>=10.0.0
python-dotenv>=1.0.0
geopy>=2.0.0
requests>=2.0.0
"""

import os
import threading
from datetime import datetime, timezone

import customtkinter as ctk
import requests
from dotenv import load_dotenv
from geopy.exc import GeocoderServiceError
from geopy.geocoders import Nominatim
from PIL import Image, ImageDraw, ImageFilter, ImageColor


# Load environment variables from .env so the app can read STORMGLASS_API_KEY.
load_dotenv()

# Use a placeholder fallback if the API key has not been configured yet.
STORMGLASS_API_KEY = os.getenv("STORMGLASS_API_KEY", "YOUR_STORMGLASS_API_KEY")

# Global visual configuration for a modern interface.
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

THEMES = {
    "dark": {
        "bg": "#070B12",
        "sidebar": "#0B1220",
        "panel": "#111B2D",
        "panel_alt": "#0E1626",
        "card_border": "#22314E",
        "accent": "#58C7FF",
        "accent_hover": "#77D6FF",
        "accent_2": "#8A5CFF",
        "text_primary": "#F5F8FF",
        "text_secondary": "#8EA3C7",
        "success": "#63E6A9",
        "warning": "#FFD36A",
        "error": "#FF7E7E",
        "glass": "#141F34",
    },
    "light": {
        "bg": "#F4F7FB",
        "sidebar": "#FFFFFF",
        "panel": "#FFFFFF",
        "panel_alt": "#EEF3FB",
        "card_border": "#D6E1F2",
        "accent": "#2A7BFF",
        "accent_hover": "#4190FF",
        "accent_2": "#8A5CFF",
        "text_primary": "#0C1220",
        "text_secondary": "#5D6F8E",
        "success": "#2BB673",
        "warning": "#D8A12B",
        "error": "#D64545",
        "glass": "#F8FAFF",
    },
}

DEFAULT_THEME = THEMES["dark"]
BG_COLOR = DEFAULT_THEME["bg"]
SIDEBAR_COLOR = DEFAULT_THEME["sidebar"]
PANEL_COLOR = DEFAULT_THEME["panel"]
PANEL_ALT_COLOR = DEFAULT_THEME["panel_alt"]
CARD_BORDER = DEFAULT_THEME["card_border"]
ACCENT_COLOR = DEFAULT_THEME["accent"]
ACCENT_HOVER = DEFAULT_THEME["accent_hover"]
ACCENT_2 = DEFAULT_THEME["accent_2"]
TEXT_PRIMARY = DEFAULT_THEME["text_primary"]
TEXT_SECONDARY = DEFAULT_THEME["text_secondary"]
SUCCESS_COLOR = DEFAULT_THEME["success"]
WARNING_COLOR = DEFAULT_THEME["warning"]
ERROR_COLOR = DEFAULT_THEME["error"]
GLASS_COLOR = DEFAULT_THEME["glass"]

FONT_DISPLAY = ("Segoe UI Semibold", 42)
FONT_TITLE = ("Segoe UI Semibold", 30)
FONT_SUBTITLE = ("Segoe UI", 14)
FONT_BODY = ("Segoe UI", 13)

DEFAULT_CITY_SUGGESTIONS = [
     "solapur"
     "Mumbai"
]


def geocode_city(city_name: str) -> tuple[float, float, str]:
    """Convert a city name into coordinates and a short display label."""
    try:
        geolocator = Nominatim(user_agent="weather_city_dashboard")
        location = geolocator.geocode(city_name, timeout=10, addressdetails=True)
    except GeocoderServiceError as exc:
        raise ConnectionError(f"Geocoding service error: {exc}") from exc
    except Exception as exc:
        raise ConnectionError(f"Unexpected geocoding error: {exc}") from exc

    if location is None:
        raise ValueError("City not found. Please enter a valid city name.")

    location_label = location.address.split(",")[0] if location.address else city_name
    return location.latitude, location.longitude, location_label


def fetch_weather(latitude: float, longitude: float) -> dict:
    """Fetch current weather data from the StormGlass point API."""
    url = "https://api.stormglass.io/v2/weather/point"
    params = {
        "lat": latitude,
        "lng": longitude,
        "params": "airTemperature,windSpeed,humidity",
    }
    headers = {
        "Authorization": STORMGLASS_API_KEY,
    }

    try:
        response = requests.get(url, params=params, headers=headers, timeout=15)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as exc:
        raise ConnectionError(f"Weather API request failed: {exc}") from exc
    except ValueError as exc:
        raise ValueError(f"Failed to parse JSON response: {exc}") from exc


def extract_current_hour_data(weather_data: dict) -> dict:
    """Extract the current hour values from the StormGlass 'sg' source."""
    hours = weather_data.get("hours")
    if not hours:
        raise KeyError("No hourly weather data was returned by the API.")

    current_hour_utc = datetime.now(timezone.utc).replace(
        minute=0, second=0, microsecond=0
    )

    for hour_entry in hours:
        time_str = hour_entry.get("time")
        if not time_str:
            continue

        try:
            entry_time = datetime.fromisoformat(time_str.replace("Z", "+00:00"))
        except ValueError:
            continue

        if entry_time == current_hour_utc:
            try:
                return {
                    "temperature": hour_entry["airTemperature"]["sg"],
                    "wind_speed": hour_entry["windSpeed"]["sg"],
                    "humidity": hour_entry["humidity"]["sg"],
                }
            except KeyError as exc:
                raise KeyError(
                    "Missing expected weather values from the 'sg' source."
                ) from exc

    raise KeyError("Could not find weather data for the current hour.")


def create_weather_icon(size: int = 132) -> ctk.CTkImage:
    """Create a glowing weather icon placeholder using PIL."""
    image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)

    draw.ellipse((10, 10, size - 10, size - 10), fill=(88, 199, 255, 55))
    draw.ellipse((22, 22, size - 22, size - 22), fill=(88, 199, 255, 150))
    draw.ellipse((36, 36, size - 36, size - 36), fill=(255, 224, 135, 255))
    draw.rounded_rectangle(
        (22, size - 56, size - 22, size - 24),
        radius=16,
        fill=(230, 242, 255, 230),
    )
    draw.rounded_rectangle(
        (10, size - 66, size - 52, size - 30),
        radius=16,
        fill=(230, 242, 255, 210),
    )

    return ctk.CTkImage(light_image=image, dark_image=image, size=(size, size))


def create_background_image(width: int, height: int, theme: dict) -> ctk.CTkImage:
    """Create a premium gradient background with soft color blooms."""
    width = max(width, 800)
    height = max(height, 600)
    base = Image.new("RGB", (width, height), theme["bg"])
    draw = ImageDraw.Draw(base)

    for y in range(height):
        blend = y / max(height - 1, 1)
        r1, g1, b1 = ImageColor.getrgb(theme["bg"])
        r2, g2, b2 = ImageColor.getrgb(theme["panel_alt"])
        r = int(r1 + (r2 - r1) * blend)
        g = int(g1 + (g2 - g1) * blend)
        b = int(b1 + (b2 - b1) * blend)
        draw.line([(0, y), (width, y)], fill=(r, g, b))

    glow = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow)
    glow_draw.ellipse(
        (width * 0.55, -height * 0.2, width * 1.1, height * 0.55),
        fill=(*ImageColor.getrgb(theme["accent"]), 90),
    )
    glow_draw.ellipse(
        (-width * 0.2, height * 0.35, width * 0.45, height * 1.05),
        fill=(*ImageColor.getrgb(theme["accent_2"]), 70),
    )
    glow = glow.filter(ImageFilter.GaussianBlur(radius=120))
    combined = Image.alpha_composite(base.convert("RGBA"), glow)

    return ctk.CTkImage(light_image=combined, dark_image=combined, size=(width, height))


class WeatherApp(ctk.CTk):
    """Modern CustomTkinter weather dashboard."""

    def __init__(self) -> None:
        super().__init__()

        self.title("Weather Dashboard")
        self.geometry("1280x760")
        self.minsize(1080, 680)
        self.current_theme = "dark"
        self.configure(fg_color=THEMES[self.current_theme]["bg"])

        self.weather_icon = create_weather_icon()
        self.is_fetching = False
        self._bg_image = None
        self._bg_pending = False

        # Let the window resize cleanly while keeping panels centered and balanced.
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.background_label = ctk.CTkLabel(self, text="")
        self.background_label.place(relx=0, rely=0, relwidth=1, relheight=1)
        self.background_label.lower()

        self._build_sidebar()
        self._build_dashboard()
        self._apply_theme()
        self.bind("<Configure>", self._schedule_background_redraw)

    def _build_sidebar(self) -> None:
        """Build the left navigation panel."""
        self.sidebar = ctk.CTkFrame(
            self,
            width=250,
            corner_radius=24,
            fg_color=GLASS_COLOR,
            border_width=1,
            border_color=CARD_BORDER,
        )
        self.sidebar.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        self.sidebar.grid_propagate(False)
        self.sidebar.grid_rowconfigure(7, weight=1)

        self.logo_label = ctk.CTkLabel(
            self.sidebar,
            text="Aether Weather",
            font=ctk.CTkFont(family=FONT_TITLE[0], size=28, weight="bold"),
            text_color=TEXT_PRIMARY,
        )
        self.logo_label.grid(row=0, column=0, padx=24, pady=(28, 8), sticky="w")

        self.tagline_label = ctk.CTkLabel(
            self.sidebar,
            text="Mood-first weather intelligence with a premium visual layer.",
            justify="left",
            wraplength=190,
            font=ctk.CTkFont(family=FONT_BODY[0], size=13),
            text_color=TEXT_SECONDARY,
        )
        self.tagline_label.grid(row=1, column=0, padx=24, pady=(0, 24), sticky="w")

        self.search_button = ctk.CTkButton(
            self.sidebar,
            text="Search",
            height=46,
            corner_radius=18,
            fg_color=ACCENT_COLOR,
            hover_color=ACCENT_HOVER,
            text_color=TEXT_PRIMARY,
            font=ctk.CTkFont(family=FONT_BODY[0], size=15, weight="bold"),
        )
        self.search_button.grid(row=2, column=0, padx=24, pady=8, sticky="ew")

        self.settings_button = ctk.CTkButton(
            self.sidebar,
            text="Settings",
            height=46,
            corner_radius=18,
            fg_color=PANEL_COLOR,
            hover_color=PANEL_ALT_COLOR,
            border_width=1,
            border_color=CARD_BORDER,
            text_color=TEXT_PRIMARY,
            font=ctk.CTkFont(family=FONT_BODY[0], size=15, weight="bold"),
        )
        self.settings_button.grid(row=3, column=0, padx=24, pady=8, sticky="ew")

        self.mode_label = ctk.CTkLabel(
            self.sidebar,
            text="Appearance",
            font=ctk.CTkFont(family=FONT_BODY[0], size=13, weight="bold"),
            text_color=TEXT_SECONDARY,
        )
        self.mode_label.grid(row=4, column=0, padx=28, pady=(32, 6), sticky="w")

        self.mode_menu = ctk.CTkOptionMenu(
            self.sidebar,
            values=["dark", "light", "system"],
            command=self._change_appearance_mode,
            fg_color=PANEL_COLOR,
            button_color=ACCENT_COLOR,
            button_hover_color=ACCENT_HOVER,
            dropdown_fg_color=SIDEBAR_COLOR,
            corner_radius=12,
        )
        self.mode_menu.set("dark")
        self.mode_menu.grid(row=5, column=0, padx=24, pady=6, sticky="ew")

        self.api_hint = ctk.CTkLabel(
            self.sidebar,
            text="Set STORMGLASS_API_KEY in .env",
            font=ctk.CTkFont(family=FONT_BODY[0], size=12),
            text_color=TEXT_SECONDARY,
        )
        self.api_hint.grid(row=8, column=0, padx=28, pady=(0, 28), sticky="sw")

    def _build_dashboard(self) -> None:
        """Build the main content area with search and metric cards."""
        self.dashboard = ctk.CTkFrame(self, fg_color="transparent", corner_radius=0)
        self.dashboard.grid(row=0, column=1, sticky="nsew", padx=(0, 20), pady=20)
        self.dashboard.grid_columnconfigure(0, weight=1)
        self.dashboard.grid_rowconfigure(1, weight=1)

        self.topbar = ctk.CTkFrame(self.dashboard, fg_color="transparent")
        self.topbar.grid(row=0, column=0, sticky="ew", padx=32, pady=(28, 16))
        self.topbar.grid_columnconfigure(0, weight=1)

        self.title_label = ctk.CTkLabel(
            self.topbar,
            text="Weather Dashboard",
            font=ctk.CTkFont(family=FONT_TITLE[0], size=30, weight="bold"),
            text_color=TEXT_PRIMARY,
        )
        self.title_label.grid(row=0, column=0, sticky="w")

        self.status_label = ctk.CTkLabel(
            self.topbar,
            text="Ready",
            font=ctk.CTkFont(family=FONT_BODY[0], size=14, weight="bold"),
            text_color=SUCCESS_COLOR,
        )
        self.status_label.grid(row=0, column=1, sticky="e", padx=(16, 0))

        self.content = ctk.CTkFrame(self.dashboard, fg_color="transparent")
        self.content.grid(row=1, column=0, sticky="nsew", padx=32, pady=(0, 28))
        self.content.grid_columnconfigure(0, weight=1)
        self.content.grid_rowconfigure(1, weight=1)

        self.search_panel = ctk.CTkFrame(
            self.content,
            fg_color=GLASS_COLOR,
            corner_radius=28,
            border_width=1,
            border_color=CARD_BORDER,
        )
        self.search_panel.grid(row=0, column=0, sticky="ew", pady=(0, 24))
        self.search_panel.grid_columnconfigure(0, weight=1)

        self.search_label = ctk.CTkLabel(
            self.search_panel,
            text="Search by city",
            font=ctk.CTkFont(family=FONT_BODY[0], size=16, weight="bold"),
            text_color=TEXT_PRIMARY,
        )
        self.search_label.grid(row=0, column=0, padx=24, pady=(18, 8), sticky="w")

        self.search_row = ctk.CTkFrame(self.search_panel, fg_color="transparent")
        self.search_row.grid(row=1, column=0, sticky="ew", padx=22, pady=(0, 22))
        self.search_row.grid_columnconfigure(0, weight=1)

        self.city_entry = ctk.CTkEntry(
            self.search_row,
            height=54,
            corner_radius=20,
            placeholder_text="Enter a city name...",
            fg_color=PANEL_ALT_COLOR,
            border_width=1,
            border_color=CARD_BORDER,
            text_color=TEXT_PRIMARY,
            placeholder_text_color=TEXT_SECONDARY,
            font=ctk.CTkFont(family=FONT_BODY[0], size=16),
        )
        self.city_entry.grid(row=0, column=0, sticky="ew", padx=(0, 14))
        self.city_entry.bind("<Return>", self.start_fetch)
        self.city_entry.bind("<FocusIn>", self._on_city_focus)
        self.city_entry.bind("<KeyRelease>", self._on_city_input)

        self.suggestions_frame = ctk.CTkFrame(
            self.search_panel,
            fg_color="transparent",
        )
        self.suggestions_frame.grid(row=2, column=0, sticky="ew", padx=24, pady=(0, 12))
        self.suggestions_frame.grid_columnconfigure(0, weight=1)
        self.suggestion_buttons = []
        self._suggestion_after_id = None

        self.fetch_button = ctk.CTkButton(
            self.search_row,
            text="Get Weather",
            width=170,
            height=54,
            corner_radius=20,
            fg_color=ACCENT_COLOR,
            hover_color=ACCENT_HOVER,
            text_color=TEXT_PRIMARY,
            font=ctk.CTkFont(family=FONT_BODY[0], size=15, weight="bold"),
            command=self.start_fetch,
        )
        self.fetch_button.grid(row=0, column=1, sticky="e")

        self.cards_container = ctk.CTkFrame(self.content, fg_color="transparent")
        self.cards_container.grid(row=1, column=0, sticky="nsew")
        self.cards_container.grid_columnconfigure(0, weight=2)
        self.cards_container.grid_columnconfigure(1, weight=1)
        self.cards_container.grid_rowconfigure(0, weight=1)
        self.cards_container.grid_rowconfigure(1, weight=1)

        self.temperature_card = ctk.CTkFrame(
            self.cards_container,
            fg_color=GLASS_COLOR,
            corner_radius=34,
            border_width=1,
            border_color=CARD_BORDER,
        )
        self.temperature_card.grid(
            row=0, column=0, rowspan=2, sticky="nsew", padx=(0, 18)
        )
        self.temperature_card.grid_columnconfigure(0, weight=1)

        self.temperature_icon_label = ctk.CTkLabel(
            self.temperature_card,
            text="",
            image=self.weather_icon,
        )
        self.temperature_icon_label.grid(row=0, column=0, pady=(32, 12), sticky="n")

        self.location_label = ctk.CTkLabel(
            self.temperature_card,
            text="Awaiting search",
            font=ctk.CTkFont(family=FONT_BODY[0], size=16, weight="bold"),
            text_color=TEXT_SECONDARY,
        )
        self.location_label.grid(row=1, column=0, padx=26, pady=(0, 8))

        self.temperature_value = ctk.CTkLabel(
            self.temperature_card,
            text="-- ℃",
            font=ctk.CTkFont(family=FONT_DISPLAY[0], size=64, weight="bold"),
            text_color=TEXT_PRIMARY,
        )
        self.temperature_value.grid(row=2, column=0, padx=26, pady=(0, 10))

        self.temperature_caption = ctk.CTkLabel(
            self.temperature_card,
            text="Current air temperature from StormGlass",
            font=ctk.CTkFont(family=FONT_BODY[0], size=14),
            text_color=TEXT_SECONDARY,
        )
        self.temperature_caption.grid(row=3, column=0, padx=26, pady=(0, 30))

        self.humidity_card = self._create_metric_card(
            row=0,
            title="Humidity",
            value="--%",
            subtitle="Moisture in the air",
        )

        self.wind_card = self._create_metric_card(
            row=1,
            title="Wind Speed",
            value="-- m/s",
            subtitle="Surface wind conditions",
        )

    def _create_metric_card(self, row: int, title: str, value: str, subtitle: str) -> ctk.CTkFrame:
        """Create a smaller card for humidity and wind speed."""
        card = ctk.CTkFrame(
            self.cards_container,
            fg_color=GLASS_COLOR,
            corner_radius=28,
            border_width=1,
            border_color=CARD_BORDER,
        )
        card.grid(row=row, column=1, sticky="nsew", pady=(0, 18) if row == 0 else 0)
        card.grid_columnconfigure(0, weight=1)
        card.grid_rowconfigure(2, weight=1)

        title_label = ctk.CTkLabel(
            card,
            text=title,
            font=ctk.CTkFont(family=FONT_BODY[0], size=16, weight="bold"),
            text_color=TEXT_PRIMARY,
        )
        title_label.grid(row=0, column=0, padx=22, pady=(24, 10), sticky="w")

        value_label = ctk.CTkLabel(
            card,
            text=value,
            font=ctk.CTkFont(family=FONT_TITLE[0], size=28, weight="bold"),
            text_color=ACCENT_COLOR,
        )
        value_label.grid(row=1, column=0, padx=22, pady=(0, 8), sticky="w")

        subtitle_label = ctk.CTkLabel(
            card,
            text=subtitle,
            font=ctk.CTkFont(family=FONT_BODY[0], size=12),
            text_color=TEXT_SECONDARY,
        )
        subtitle_label.grid(row=2, column=0, padx=22, pady=(0, 22), sticky="sw")

        card.value_label = value_label
        card.title_label = title_label
        card.subtitle_label = subtitle_label
        return card

    def start_fetch(self, _event=None) -> None:
        """Start a threaded weather lookup so the interface remains responsive."""
        city_name = self.city_entry.get().strip()

        if self.is_fetching:
            return

        if not city_name:
            self._set_status("Please enter a city name.", self.theme["error"])
            return

        if STORMGLASS_API_KEY == "YOUR_STORMGLASS_API_KEY":
            self._set_status(
                "Add STORMGLASS_API_KEY to your .env file.", self.theme["warning"]
            )
            return

        self.is_fetching = True
        self.fetch_button.configure(state="disabled", text="Fetching...")
        self._set_status("Fetching weather data...", self.theme["warning"])

        worker = threading.Thread(
            target=self._fetch_weather_worker,
            args=(city_name,),
            daemon=True,
        )
        worker.start()

    def _fetch_weather_worker(self, city_name: str) -> None:
        """Perform geocoding and the API request on a background thread."""
        try:
            latitude, longitude, location_label = geocode_city(city_name)
            weather_data = fetch_weather(latitude, longitude)
            current_weather = extract_current_hour_data(weather_data)
            self.after(
                0,
                lambda: self._update_weather_ui(location_label, current_weather),
            )
        except ValueError as exc:
            self.after(0, lambda exc=exc: self._handle_error(f"Input error: {exc}"))
        except ConnectionError as exc:
            self.after(0, lambda exc=exc: self._handle_error(f"Connection error: {exc}"))
        except KeyError as exc:
            self.after(0, lambda exc=exc: self._handle_error(f"Data error: {exc}"))
        except Exception as exc:
            self.after(0, lambda exc=exc: self._handle_error(f"Unexpected error: {exc}"))

    def _on_city_input(self, _event=None) -> None:
        query = self.city_entry.get().strip()
        if self._suggestion_after_id is not None:
            self.after_cancel(self._suggestion_after_id)
            self._suggestion_after_id = None

        if not query:
            self._update_city_suggestions(DEFAULT_CITY_SUGGESTIONS)
            return

        if len(query) < 2:
            self._update_city_suggestions(
                [city for city in DEFAULT_CITY_SUGGESTIONS if city.lower().startswith(query.lower())]
            )
            return

        self._suggestion_after_id = self.after(250, lambda q=query: self._fetch_city_suggestions(q))

    def _on_city_focus(self, _event=None) -> None:
        query = self.city_entry.get().strip()
        if not query:
            self._update_city_suggestions(DEFAULT_CITY_SUGGESTIONS)

    def _fetch_city_suggestions(self, query: str) -> None:
        def worker() -> None:
            try:
                geolocator = Nominatim(user_agent="weather_city_dashboard_suggestions")
                results = geolocator.geocode(
                    query,
                    exactly_one=False,
                    limit=6,
                    addressdetails=True,
                    timeout=10,
                )
                suggestions = []
                if results:
                    for location in results:
                        if location and location.address:
                            display = location.address.split(",")[0]
                            if display not in suggestions:
                                suggestions.append(display)
                                if len(suggestions) >= 5:
                                    break
                self.after(0, lambda: self._update_city_suggestions(suggestions))
            except Exception:
                self.after(0, self._clear_city_suggestions)

        threading.Thread(target=worker, daemon=True).start()

    def _update_city_suggestions(self, suggestions: list[str]) -> None:
        self._clear_city_suggestions()
        if not suggestions:
            return

        for index, city_name in enumerate(suggestions):
            button = ctk.CTkButton(
                self.suggestions_frame,
                text=city_name,
                height=36,
                fg_color=PANEL_ALT_COLOR,
                hover_color=ACCENT_HOVER,
                text_color=TEXT_PRIMARY,
                font=ctk.CTkFont(family=FONT_BODY[0], size=14),
                corner_radius=14,
                command=lambda value=city_name: self._on_city_suggestion_selected(value),
            )
            button.grid(row=index, column=0, sticky="ew", pady=(0, 6))
            self.suggestion_buttons.append(button)

    def _clear_city_suggestions(self) -> None:
        for button in self.suggestion_buttons:
            button.destroy()
        self.suggestion_buttons = []

    def _on_city_suggestion_selected(self, city_name: str) -> None:
        self.city_entry.delete(0, "end")
        self.city_entry.insert(0, city_name)
        self._clear_city_suggestions()

    def _update_weather_ui(self, location_label: str, current_weather: dict) -> None:
        """Update dashboard values after a successful weather lookup."""
        self.location_label.configure(text=location_label)
        self.temperature_value.configure(
            text=f"{round(current_weather['temperature'])} ℃"
        )
        self.humidity_card.value_label.configure(
            text=f"{round(current_weather['humidity'])}%"
        )
        self.wind_card.value_label.configure(
            text=f"{current_weather['wind_speed']:.1f} m/s"
        )
        self._set_status("Success", self.theme["success"])
        self._finish_fetch()

    def _handle_error(self, message: str) -> None:
        """Display a user-friendly error in the status area."""
        self._set_status(message, self.theme["error"])
        self._finish_fetch()

    def _finish_fetch(self) -> None:
        """Restore the button state after the request finishes."""
        self.is_fetching = False
        self.fetch_button.configure(state="normal", text="Get Weather")

    def _set_status(self, text: str, color: str) -> None:
        """Update the status label with a message and matching color."""
        self.status_label.configure(text=text, text_color=color)

    @property
    def theme(self) -> dict:
        return THEMES[self.current_theme]

    def _change_appearance_mode(self, mode: str) -> None:
        """Switch between light/dark/system mode and repaint widgets."""
        normalized = mode.lower()
        ctk.set_appearance_mode(mode)

        if normalized == "system":
            detected = ctk.get_appearance_mode().lower()
            self.current_theme = detected if detected in THEMES else "dark"
        else:
            self.current_theme = normalized if normalized in THEMES else "dark"

        self._apply_theme()

    def _apply_theme(self) -> None:
        """Apply the active theme colors to all widgets."""
        theme = self.theme

        self.configure(fg_color=theme["bg"])
        self.dashboard.configure(fg_color="transparent")
        self.sidebar.configure(
            fg_color=theme["glass"],
            border_color=theme["card_border"],
        )

        self.logo_label.configure(text_color=theme["text_primary"])
        self.tagline_label.configure(text_color=theme["text_secondary"])
        self.mode_label.configure(text_color=theme["text_secondary"])
        self.api_hint.configure(text_color=theme["text_secondary"])

        self.search_button.configure(
            fg_color=theme["accent"],
            hover_color=theme["accent_hover"],
            text_color=theme["text_primary"],
        )
        self.settings_button.configure(
            fg_color=theme["panel"],
            hover_color=theme["panel_alt"],
            border_color=theme["card_border"],
            text_color=theme["text_primary"],
        )
        self.mode_menu.configure(
            fg_color=theme["panel"],
            button_color=theme["accent"],
            button_hover_color=theme["accent_hover"],
            dropdown_fg_color=theme["sidebar"],
        )

        self.title_label.configure(text_color=theme["text_primary"])
        if self.status_label.cget("text") == "Ready":
            self.status_label.configure(text_color=theme["success"])

        self.search_panel.configure(
            fg_color=theme["glass"],
            border_color=theme["card_border"],
        )
        self.search_label.configure(text_color=theme["text_primary"])
        self.city_entry.configure(
            fg_color=theme["panel_alt"],
            border_color=theme["card_border"],
            text_color=theme["text_primary"],
            placeholder_text_color=theme["text_secondary"],
        )
        self.fetch_button.configure(
            fg_color=theme["accent"],
            hover_color=theme["accent_hover"],
            text_color=theme["text_primary"],
        )

        self.temperature_card.configure(
            fg_color=theme["glass"],
            border_color=theme["card_border"],
        )
        self.location_label.configure(text_color=theme["text_secondary"])
        self.temperature_value.configure(text_color=theme["text_primary"])
        self.temperature_caption.configure(text_color=theme["text_secondary"])

        for card in (self.humidity_card, self.wind_card):
            card.configure(
                fg_color=theme["glass"],
                border_color=theme["card_border"],
            )
            card.title_label.configure(text_color=theme["text_primary"])
            card.value_label.configure(text_color=theme["accent"])
            card.subtitle_label.configure(text_color=theme["text_secondary"])

        self._refresh_background()

    def _schedule_background_redraw(self, _event=None) -> None:
        if self._bg_pending:
            return
        self._bg_pending = True
        self.after(120, self._refresh_background)

    def _refresh_background(self) -> None:
        self._bg_pending = False
        width = max(self.winfo_width(), 800)
        height = max(self.winfo_height(), 600)
        self._bg_image = create_background_image(width, height, self.theme)
        self.background_label.configure(image=self._bg_image)


def main() -> None:
    """Launch the weather dashboard window."""
    app = WeatherApp()
    app.mainloop()


if __name__ == "__main__":
    main()
