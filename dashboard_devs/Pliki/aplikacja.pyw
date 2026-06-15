"""
Finalna wersja, wszystko działa.

Wymagane biblioteki:
    pip install pandas matplotlib
"""

from __future__ import annotations

import sys
import re
import json
from urllib.parse import unquote
import tkinter as tk
import tkinter.font as tkfont
from tkinter import ttk, messagebox
from pathlib import Path
from typing import Callable, Optional

import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# KONFIGURACJA WYGLĄDU

LIGHT_COLORS = {
    "bg": "#f3f6f4",
    "panel": "#ffffff",
    "panel_alt": "#f8faf9",
    "primary": "#2f6f4e",
    "primary_dark": "#1f5138",
    "primary_soft": "#e7eee8",
    "accent": "#84a98c",
    "border": "#d8e2dc",
    "text": "#1f2933",
    "muted": "#64748b",
    "warning_bg": "#fff7d6",
    "warning_fg": "#795200",
    "danger": "#9f1239",
}

DARK_COLORS = {
    "bg": "#111827",
    "panel": "#1f2937",
    "panel_alt": "#253244",
    "primary": "#4ade80",
    "primary_dark": "#86efac",
    "primary_soft": "#173322",
    "accent": "#22c55e",
    "border": "#374151",
    "text": "#f3f4f6",
    "muted": "#cbd5e1",
    "warning_bg": "#3f2f09",
    "warning_fg": "#fde68a",
    "danger": "#fda4af",
}

COLORS = dict(LIGHT_COLORS)

FONT_TITLE = ("Segoe UI", 20, "bold")
FONT_H1 = ("Segoe UI", 24, "bold")
FONT_H2 = ("Segoe UI", 13, "bold")
FONT_NORMAL = ("Segoe UI", 10)
FONT_SMALL = ("Segoe UI", 9)
FONT_KPI_VALUE = ("Segoe UI", 18, "bold")
FONT_KPI_LABEL = ("Segoe UI", 9, "bold")

# POMOCNICZE FUNKCJE FORMATUJĄCE

def fmt_number(value) -> str:
    """Formatowanie liczby w polskim stylu: 49 441."""
    if value is None or pd.isna(value):
        return "brak danych"
    try:
        return f"{float(value):,.0f}".replace(",", " ")
    except Exception:
        return str(value)

def fmt_value(value) -> str:
    if value is None or pd.isna(value):
        return "brak danych"
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)

def fmt_bool_like(value) -> str:
    if value is None or pd.isna(value):
        return "brak danych"
    text = str(value).strip()
    low = text.lower()
    if low in {"1", "1.0", "true", "tak", "yes"}:
        return "tak"
    if low in {"0", "0.0", "false", "nie", "no"}:
        return "nie"
    return text

def fmt_presence_bool(value) -> str:
    """Format TAK/NIE dla cech, które czasem są 0/1, a czasem licznikami, np. rondo=8.0."""
    if value is None or pd.isna(value):
        return "brak danych"
    text = str(value).strip()
    low = text.lower()
    if low in {"true", "tak", "yes"}:
        return "tak"
    if low in {"false", "nie", "no"}:
        return "nie"
    try:
        number = float(text.replace(",", "."))
        return "tak" if number > 0 else "nie"
    except Exception:
        return fmt_bool_like(value)

def safe_mode(series: pd.Series) -> str:
    series = series.dropna()
    if series.empty:
        return "brak danych"
    return str(series.mode().iloc[0])

def normalize_text(value: str) -> str:
    return (
        str(value)
        .strip()
        .lower()
        .replace("ą", "a")
        .replace("ć", "c")
        .replace("ę", "e")
        .replace("ł", "l")
        .replace("ń", "n")
        .replace("ó", "o")
        .replace("ś", "s")
        .replace("ż", "z")
        .replace("ź", "z")
    )

def parse_gps(value) -> Optional[tuple[float, float]]:
    """Parsuje zapis GPS w formacie: '52.1046 21.0188'."""
    if value is None or pd.isna(value):
        return None
    parts = str(value).replace(",", ".").split()
    if len(parts) < 2:
        return None
    try:
        lat = float(parts[0])
        lon = float(parts[1])
        return lat, lon
    except ValueError:
        return None

def classify_by_threshold(value, median, q75) -> tuple[str, str]:
    """Zwraca etykietę i kolor dla kafelków KPI."""
    try:
        val = float(value)
    except Exception:
        return "brak porównania", COLORS["muted"]
    if pd.isna(val):
        return "brak porównania", COLORS["muted"]
    if q75 is not None and not pd.isna(q75) and val >= float(q75):
        return "wysoki poziom", COLORS["danger"]
    if median is not None and not pd.isna(median) and val >= float(median):
        return "powyżej mediany", "#b7791f"
    return "poniżej mediany", COLORS["primary_dark"]

def markdown_heading(path: Path) -> str:
    try:
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith("#"):
                return line.lstrip("#").strip()
    except Exception:
        pass
    return path.stem.replace("_", " ")

# TOOLTIP I SCROLLABLE FRAME

class ToolTip:
    def __init__(self, widget: tk.Widget, text: str):
        self.widget = widget
        self.text = text
        self.tipwindow: Optional[tk.Toplevel] = None
        widget.bind("<Enter>", self.show)
        widget.bind("<Leave>", self.hide)

    def show(self, _event=None):
        if self.tipwindow or not self.text:
            return
        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 5
        self.tipwindow = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        label = tk.Label(
            tw,
            text=self.text,
            justify="left",
            background="#ffffe0",
            relief="solid",
            borderwidth=1,
            font=FONT_SMALL,
            wraplength=460,
            padx=8,
            pady=6,
        )
        label.pack()

    def hide(self, _event=None):
        if self.tipwindow:
            self.tipwindow.destroy()
            self.tipwindow = None

class ScrollableFrame(ttk.Frame):
    def __init__(self, parent, bg: str = COLORS["bg"]):
        super().__init__(parent)
        self.canvas = tk.Canvas(self, bg=bg, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.content = ttk.Frame(self.canvas)

        self.content.bind(
            "<Configure>",
            lambda _e: self.canvas.configure(scrollregion=self.canvas.bbox("all")),
        )
        self.window_id = self.canvas.create_window((0, 0), window=self.content, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")
        self.canvas.bind("<Configure>", self._on_canvas_configure)

        # Windows/macOS
        self.bind_all("<MouseWheel>", self._on_mousewheel, add="+")
        # Linux
        self.bind_all("<Button-4>", self._on_mousewheel, add="+")
        self.bind_all("<Button-5>", self._on_mousewheel, add="+")

    def _on_canvas_configure(self, event):
        self.canvas.itemconfig(self.window_id, width=event.width)

    def _is_pointer_inside(self) -> bool:
        try:
            x = self.winfo_pointerx()
            y = self.winfo_pointery()
            widget = self.winfo_containing(x, y)
        except Exception:
            return False

        while widget is not None:
            if widget is self or widget is self.canvas or widget is self.content:
                return True
            try:
                widget = widget.master
            except Exception:
                break
        return False

    def _on_mousewheel(self, event):
        if not self._is_pointer_inside():
            return
        try:
            if getattr(event, "num", None) == 4:
                self.canvas.yview_scroll(-3, "units")
            elif getattr(event, "num", None) == 5:
                self.canvas.yview_scroll(3, "units")
            else:
                delta = event.delta
                step = int(-1 * (delta / 120)) if delta else 0
                if step == 0:
                    step = -1 if delta > 0 else 1
                self.canvas.yview_scroll(step * 3, "units")
        except Exception:
            pass

    def scroll_to_top(self):
        self.canvas.yview_moveto(0)

# WARSTWA DANYCH

class DataStore:
    """Jedno miejsce odpowiedzialne za wczytanie i przygotowanie danych."""

    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        self.events = self._load_events()
        self.traffic = self._load_traffic()
        self.attributes = self._load_attributes()
        self.or_interpretations = self._load_or_interpretations()
        self.intersection_descriptions = self._load_intersection_descriptions()
        self.intersections = self._build_intersections()
        self.events_by_id = {
            int(k): v.copy()
            for k, v in self.events.dropna(subset=["id_skrzyzowania"]).groupby("id_skrzyzowania")
        }
        self.event_counts = pd.Series({k: len(v) for k, v in self.events_by_id.items()}, dtype="float")
        self.event_median = self.event_counts.median() if not self.event_counts.empty else None
        self.event_q75 = self.event_counts.quantile(0.75) if not self.event_counts.empty else None
        traffic_values = pd.to_numeric(self.traffic.get("srednie_dobowe"), errors="coerce").dropna()
        self.traffic_median = traffic_values.median() if not traffic_values.empty else None
        self.traffic_q75 = traffic_values.quantile(0.75) if not traffic_values.empty else None
        self.summary_cache: dict[int, dict] = {}
        self.md_files = self._find_markdown_files()
        self.statistics_md_path = self._find_optional_file("interpretacje.md")
        self.prediction_description_files = self._find_prediction_description_files()

    def _find_file(self, filename: str) -> Path:
        candidates = [
            self.base_dir / filename,
            self.base_dir / "data" / filename,
            self.base_dir / "Dane" / filename,
            self.base_dir / "Dane_wykresy" / filename,
            self.base_dir / "Opisy_wykresy" / filename,
            Path.cwd() / filename,
            Path.cwd() / "data" / filename,
            Path.cwd() / "Dane" / filename,
            Path.cwd() / "Dane_wykresy" / filename,
            Path.cwd() / "Opisy_wykresy" / filename,
        ]
        for path in candidates:
            if path.exists():
                return path
        raise FileNotFoundError(
            f"Nie znaleziono pliku: {filename}\n"
            f"Umieść go w folderze ze skryptem albo w podfolderze data."
        )

    def _find_optional_file(self, filename: str) -> Optional[Path]:
        try:
            return self._find_file(filename)
        except FileNotFoundError:
            return None

    def _load_events(self) -> pd.DataFrame:
        path = self._find_file("wyczyszczone_dane.csv")
        df = pd.read_csv(path, sep=",", encoding="utf-8-sig")
        df["data"] = pd.to_datetime(df["data"], errors="coerce")
        df["rok"] = df["data"].dt.year
        df["miesiac"] = df["data"].dt.month
        df["dzien_tygodnia"] = df["data"].dt.dayofweek
        df["id_skrzyzowania"] = pd.to_numeric(df["id_skrzyzowania"], errors="coerce").astype("Int64")
        return df

    def _load_traffic(self) -> pd.DataFrame:
        path = self._find_file("uzupelnione_natezenie.csv")
        df = pd.read_csv(path, sep=";", encoding="utf-8-sig")
        df = df.rename(
            columns={
                "Skrzyżowanie": "skrzyzowanie",
                "Ulica APR": "ulica_apr",
                "Odcinek APR": "odcinek_apr",
                "GPS (lat lon)": "gps",
                "Punkt APR": "punkt_apr",
                "Okres": "okres",
                "Max dobowe [poj./24h]": "max_dobowe",
                "Średnie dobowe [poj./24h]": "srednie_dobowe",
                "Suma z okresu [poj.]": "suma_z_okresu",
                "Uwaga": "uwaga",
            }
        )
        df["id_skrzyzowania"] = pd.to_numeric(df["id_skrzyzowania"], errors="coerce").astype("Int64")
        coords = df["gps"].apply(parse_gps) if "gps" in df.columns else pd.Series([None] * len(df))
        df["lat"] = coords.apply(lambda x: x[0] if x else pd.NA)
        df["lon"] = coords.apply(lambda x: x[1] if x else pd.NA)
        df["lat"] = pd.to_numeric(df["lat"], errors="coerce")
        df["lon"] = pd.to_numeric(df["lon"], errors="coerce")
        return df

    def _load_attributes(self) -> pd.DataFrame:
        path = self._find_file("atrybuty skrzyzowan.csv")
        df = pd.read_csv(path, sep=";", encoding="utf-8-sig")
        df = df.dropna(subset=["id_skrzyzowania"]).copy()
        df["id_skrzyzowania"] = pd.to_numeric(df["id_skrzyzowania"], errors="coerce").astype(int)
        return df

    def _load_or_interpretations(self) -> pd.DataFrame:
        path = self._find_optional_file("OR_interpretacje.csv")
        if path is None:
            return pd.DataFrame(columns=["Cecha", "Opis ekspercki", "Kategoria"])
        return pd.read_csv(path, sep=",", encoding="utf-8-sig")

    def _load_intersection_descriptions(self) -> dict[int, str]:
        """Wczytuje wyłącznie akapity „Wnioski analityczne” z pliku Opis-skrzyzowan.md."""
        path = self._find_optional_file("Opis-skrzyzowan.md")
        if path is None:
            return {}
        try:
            text = path.read_text(encoding="utf-8-sig")
        except Exception:
            return {}

        descriptions: dict[int, str] = {}
        current_id: Optional[int] = None
        collecting = False
        buffer: list[str] = []

        def clean_markdown(line: str) -> str:
            line = line.strip()
            if line.startswith(">"):
                line = line[1:].strip()
            replacements = {
                "**💡 Wnioski analityczne (ZDM):**": "",
                "**Wnioski analityczne (ZDM):**": "",
                "**💡 Wnioski analityczne:**": "",
                "**": "",
                "💡": "",
            }
            for old, new in replacements.items():
                line = line.replace(old, new)
            return line.strip()

        def save_current():
            nonlocal buffer, current_id
            if current_id is None:
                return
            content = " ".join(part for part in buffer if part).strip()
            if content:
                descriptions[current_id] = content

        for raw_line in text.splitlines():
            line = raw_line.strip()
            if line.startswith("###") and "📍" in line:
                save_current()
                buffer = []
                collecting = False
                current_id = None
                # Przykład: ### 📍 12. Aleja Wilanowska / Puławska
                try:
                    after_pin = line.split("📍", 1)[1].strip()
                    number = after_pin.split(".", 1)[0].strip()
                    current_id = int(number)
                except Exception:
                    current_id = None
                continue

            if current_id is None:
                continue

            if "Wnioski analityczne" in line:
                collecting = True
                cleaned = clean_markdown(line)
                if cleaned:
                    buffer.append(cleaned)
                continue

            if collecting:
                if not line:
                    collecting = False
                    continue
                if line.startswith("|") or line.startswith("###"):
                    collecting = False
                    continue
                cleaned = clean_markdown(line)
                if cleaned:
                    buffer.append(cleaned)

        save_current()
        return descriptions

    def get_intersection_description(self, intersection_id: int) -> str:
        return self.intersection_descriptions.get(
            int(intersection_id),
            "Brak opisu analitycznego dla tego skrzyżowania w pliku Opis-skrzyzowan.md.",
        )

    def _find_markdown_files(self) -> list[Path]:
        directories = [
            self.base_dir,
            self.base_dir / "data",
            self.base_dir / "opisy",
            self.base_dir / "Dane_opisy",
            Path.cwd(),
            Path.cwd() / "data",
            Path.cwd() / "opisy",
            Path.cwd() / "Dane_opisy",
        ]
        result: list[Path] = []
        seen: set[Path] = set()
        for directory in directories:
            if not directory.exists() or not directory.is_dir():
                continue
            for path in directory.glob("opis_*.md"):
                resolved = path.resolve()
                if resolved not in seen:
                    result.append(path)
                    seen.add(resolved)
        return sorted(result, key=lambda p: p.name.lower())


    def _find_prediction_description_files(self) -> list[Path]:
        """Pliki opisujące wykresy sekcji predykcji/modelowania NB."""
        filenames = [
            "opis_macierz_korelacji_NB.md",
            "opis_profile_klastry_NB.md",
            "opis_rozklad_klastry_NB.md",
            "opis_rzeczywiste_i_predykcje_NB.md",
            "opis_wplyw_czynnikow_NB.md",
        ]
        files: list[Path] = []
        for filename in filenames:
            path = self._find_optional_file(filename)
            if path is None:
                stem = Path(filename).stem
                candidates: list[Path] = []
                for directory in [
                    self.base_dir / "Opisy_wykresy",
                    self.base_dir,
                    self.base_dir / "data",
                    Path.cwd() / "Opisy_wykresy",
                    Path.cwd(),
                    Path.cwd() / "data",
                ]:
                    if directory.exists():
                        candidates.extend(sorted(directory.glob(f"{stem}*.md")))
                path = candidates[0] if candidates else None
            if path is not None:
                files.append(path)
        return files

    def get_home_overview(self) -> dict:
        """Podstawowe podsumowanie zbioru danych używane na stronie Home."""
        df = self.events.copy()
        years = df["rok"].dropna().astype(int) if "rok" in df else pd.Series(dtype=int)
        year_range = "brak danych" if years.empty else f"{years.min()}–{years.max()}"
        top_violation = safe_mode(df["wykroczenie"]) if "wykroczenie" in df else "brak danych"
        top_intersection = safe_mode(df["skrzyzowanie"]) if "skrzyzowanie" in df else "brak danych"
        return {
            "events_count": len(df),
            "intersection_count": int(df["id_skrzyzowania"].nunique()) if "id_skrzyzowania" in df else 0,
            "year_range": year_range,
            "top_violation": top_violation,
            "top_intersection": top_intersection,
        }

    def _build_intersections(self) -> pd.DataFrame:
        base = self.traffic[["id_skrzyzowania", "skrzyzowanie"]].drop_duplicates().copy()
        base = base.dropna(subset=["id_skrzyzowania"])
        base["id_skrzyzowania"] = base["id_skrzyzowania"].astype(int)
        base = base.sort_values("skrzyzowanie")
        return base.reset_index(drop=True)

    def get_intersections(self) -> list[tuple[int, str]]:
        return [
            (int(row["id_skrzyzowania"]), str(row["skrzyzowanie"]))
            for _, row in self.intersections.iterrows()
        ]

    def get_events(self, intersection_id: int) -> pd.DataFrame:
        return self.events_by_id.get(int(intersection_id), pd.DataFrame()).copy()

    def get_traffic_row(self, intersection_id: int) -> Optional[pd.Series]:
        rows = self.traffic[self.traffic["id_skrzyzowania"] == intersection_id]
        return None if rows.empty else rows.iloc[0]

    def get_attributes_row(self, intersection_id: int) -> Optional[pd.Series]:
        rows = self.attributes[self.attributes["id_skrzyzowania"] == intersection_id]
        return None if rows.empty else rows.iloc[0]

    def get_intersection_name(self, intersection_id: int) -> str:
        row = self.get_traffic_row(intersection_id)
        if row is not None and pd.notna(row.get("skrzyzowanie")):
            return str(row.get("skrzyzowanie"))
        events = self.get_events(intersection_id)
        if not events.empty:
            return str(events["skrzyzowanie"].iloc[0])
        return f"Skrzyżowanie {intersection_id}"

    def get_summary(self, intersection_id: int) -> dict:
        intersection_id = int(intersection_id)
        if intersection_id in self.summary_cache:
            return self.summary_cache[intersection_id]

        events = self.get_events(intersection_id)
        traffic = self.get_traffic_row(intersection_id)
        years = events["rok"].dropna().astype(int) if not events.empty and "rok" in events else pd.Series(dtype=int)
        year_range = "brak danych"
        if not years.empty:
            year_range = f"{years.min()}–{years.max()}"
        avg_daily = None if traffic is None else traffic.get("srednie_dobowe")
        events_level, events_color = classify_by_threshold(len(events), self.event_median, self.event_q75)
        traffic_level, traffic_color = classify_by_threshold(avg_daily, self.traffic_median, self.traffic_q75)
        summary = {
            "events_count": len(events),
            "year_range": year_range,
            "avg_daily": avg_daily,
            "max_daily": None if traffic is None else traffic.get("max_dobowe"),
            "top_event_type": safe_mode(events["rodzaj_zdarzenia"]) if not events.empty else "brak danych",
            "top_violation": safe_mode(events["wykroczenie"]) if not events.empty else "brak danych",
            "warning": "" if traffic is None or pd.isna(traffic.get("uwaga")) else str(traffic.get("uwaga")),
            "events_level": events_level,
            "events_color": events_color,
            "traffic_level": traffic_level,
            "traffic_color": traffic_color,
        }
        self.summary_cache[intersection_id] = summary
        return summary

    def get_geo(self, intersection_id: int) -> Optional[tuple[float, float]]:
        row = self.get_traffic_row(intersection_id)
        if row is None:
            return None
        lat, lon = row.get("lat"), row.get("lon")
        if pd.isna(lat) or pd.isna(lon):
            return None
        return float(lat), float(lon)

    def get_all_geo_points(self) -> list[tuple[int, str, float, float]]:
        points: list[tuple[int, str, float, float]] = []
        for _, row in self.traffic.dropna(subset=["id_skrzyzowania", "lat", "lon"]).iterrows():
            points.append((int(row["id_skrzyzowania"]), str(row.get("skrzyzowanie", "")), float(row["lat"]), float(row["lon"])))
        return points


    def get_interpretation(self, feature_key: str) -> str:
        if self.or_interpretations.empty:
            return "Brak pliku OR_interpretacje.csv."
        rows = self.or_interpretations[self.or_interpretations["Cecha"] == feature_key]
        if rows.empty:
            return "Brak interpretacji dla tej cechy."
        parts = []
        for _, row in rows.iterrows():
            kat = row.get("Kategoria", "")
            opis = row.get("Opis ekspercki", "")
            parts.append(f"{kat}: {opis}")
        return "\n\n".join(parts)

# WYKRESY DLA WYBRANEGO SKRZYŻOWANIA

class IntersectionPlots:
    def __init__(self, data: DataStore):
        self.data = data

    def _empty_figure(self, message: str = "Brak danych") -> Figure:
        fig, ax = plt.subplots(figsize=(6, 3.5))
        ax.text(0.5, 0.5, message, ha="center", va="center", fontsize=12)
        ax.axis("off")
        fig.tight_layout()
        return fig

    def events_by_year(self, intersection_id: int) -> Figure:
        df = self.data.get_events(intersection_id)
        if df.empty or df["rok"].dropna().empty:
            return self._empty_figure()
        counts = df.groupby("rok").size().sort_index()
        fig, ax = plt.subplots(figsize=(6, 3.5))
        ax.plot(counts.index.astype(int), counts.values, marker="o", color=COLORS["primary"])
        ax.set_title("Liczba zdarzeń według lat", fontweight="bold")
        ax.set_xlabel("Rok")
        ax.set_ylabel("Liczba zdarzeń")
        ax.grid(True, alpha=0.25)
        fig.tight_layout()
        return fig

    def events_by_month(self, intersection_id: int) -> Figure:
        df = self.data.get_events(intersection_id)
        if df.empty or df["miesiac"].dropna().empty:
            return self._empty_figure()
        counts = df.groupby("miesiac").size().reindex(range(1, 13), fill_value=0)
        labels = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "XI", "XII"]
        fig, ax = plt.subplots(figsize=(6, 3.5))
        ax.bar(labels, counts.values, color=COLORS["primary"])
        ax.set_title("Zdarzenia według miesięcy", fontweight="bold")
        ax.set_xlabel("Miesiąc")
        ax.set_ylabel("Liczba zdarzeń")
        ax.grid(axis="y", alpha=0.25)
        fig.tight_layout()
        return fig

    def event_types(self, intersection_id: int) -> Figure:
        return self._count_plot(intersection_id, "rodzaj_zdarzenia", "Najczęstsze rodzaje zdarzeń", top=8)

    def violations(self, intersection_id: int) -> Figure:
        return self._count_plot(intersection_id, "wykroczenie", "Najczęstsze wykroczenia", top=8, height=4.2)

    def signalling(self, intersection_id: int) -> Figure:
        return self._count_plot(intersection_id, "sygnalizacja", "Zdarzenia a sygnalizacja", top=8)

    def weather(self, intersection_id: int) -> Figure:
        return self._count_plot(intersection_id, "warunki_pogodowe", "Warunki pogodowe")

    def lighting(self, intersection_id: int) -> Figure:
        return self._count_plot(intersection_id, "warunki_oswietleniowe", "Warunki oświetleniowe")

    def surface(self, intersection_id: int) -> Figure:
        return self._count_plot(intersection_id, "stan_nawierzchni", "Stan nawierzchni")

    def _count_plot(self, intersection_id: int, column: str, title: str, top: int = 8, height: float = 3.8) -> Figure:
        df = self.data.get_events(intersection_id)
        if df.empty or column not in df.columns:
            return self._empty_figure()
        counts = df[column].dropna().astype(str).value_counts().head(top).sort_values()
        if counts.empty:
            return self._empty_figure()
        fig, ax = plt.subplots(figsize=(6, height))
        ax.barh(counts.index, counts.values, color=COLORS["primary"])
        ax.set_title(title, fontweight="bold")
        ax.set_xlabel("Liczba zdarzeń")
        ax.grid(axis="x", alpha=0.25)
        fig.tight_layout()
        return fig

    def traffic_comparison(self, intersection_id: int) -> Figure:
        df = self.data.traffic.dropna(subset=["srednie_dobowe"]).copy()
        if df.empty:
            return self._empty_figure()
        df = df.sort_values("srednie_dobowe", ascending=True)
        labels = df["skrzyzowanie"].astype(str)
        values = df["srednie_dobowe"]
        colors = [COLORS["accent"] if int(i) == intersection_id else "#cbd5d1" for i in df["id_skrzyzowania"]]
        fig, ax = plt.subplots(figsize=(6, 5.5))
        ax.barh(labels, values, color=colors)
        ax.set_title("Średnie dobowe natężenie na tle innych skrzyżowań", fontweight="bold")
        ax.set_xlabel("Pojazdy / 24h")
        ax.grid(axis="x", alpha=0.25)
        ax.tick_params(axis="y", labelsize=7)
        fig.tight_layout()
        return fig

    def attributes_summary(self, intersection_id: int) -> Figure:
        row = self.data.get_attributes_row(intersection_id)
        if row is None:
            return self._empty_figure()
        fields = ["pdp", "up", "mp", "nj", "tramwaje_znak", "inne", "kdzp", "zw", "stop", "zakaz s/z", "rondo"]
        vals = {f: row.get(f) for f in fields if f in row.index and pd.notna(row.get(f))}
        if not vals:
            return self._empty_figure()
        s = pd.Series(vals).astype(float).sort_values()
        fig, ax = plt.subplots(figsize=(6, 4.2))
        ax.barh(s.index, s.values, color=COLORS["primary"])
        ax.set_title("Podsumowanie atrybutów infrastrukturalnych", fontweight="bold")
        ax.set_xlabel("Liczba / wartość")
        ax.grid(axis="x", alpha=0.25)
        fig.tight_layout()
        return fig

    def groups(self) -> dict[str, list[tuple[str, Callable[[int], Figure]]]]:
        return {
            "Ogólne zdarzenia": [
                ("Zdarzenia według lat", self.events_by_year),
                ("Zdarzenia według miesięcy", self.events_by_month),
                ("Rodzaje zdarzeń", self.event_types),
            ],
            "Przyczyny i wykroczenia": [
                ("Najczęstsze wykroczenia", self.violations),
                ("Zdarzenia a sygnalizacja", self.signalling),
                ("Rodzaje zdarzeń", self.event_types),
            ],
            "Warunki zdarzeń": [
                ("Warunki pogodowe", self.weather),
                ("Warunki oświetleniowe", self.lighting),
                ("Stan nawierzchni", self.surface),
            ],
            "Infrastruktura i porównania": [
                ("Natężenie na tle innych", self.traffic_comparison),
                ("Atrybuty infrastruktury", self.attributes_summary),
            ],
        }

# APLIKACJA TKINTER

class IntersectionApp(tk.Tk):
    def __init__(self, data: Optional[DataStore] = None, base_dir: Optional[Path] = None):
        super().__init__()
        self._closing = False

        # Podstawowe ustawienia okna tworzymy od razu, żeby użytkownik widział,
        # że aplikacja rzeczywiście się uruchamia.
        self.title("Dashboard skrzyżowań drogowych")
        self.geometry("1450x900")
        self.minsize(1150, 720)

        self._settings_path = Path(__file__).resolve().parent / "app_settings.json"
        saved_settings = self._load_user_settings()
        self.font_size_level = tk.IntVar(value=int(saved_settings.get("font_size_level", 0)))
        self.dark_mode_enabled = tk.BooleanVar(value=bool(saved_settings.get("dark_mode", False)))
        self._apply_color_palette(self.dark_mode_enabled.get())
        self.configure(bg=COLORS["bg"])

        self.current_id: Optional[int] = None
        self.current_plot_canvases: list[FigureCanvasTkAgg] = []
        self._stats_images: list[tk.PhotoImage] = []
        self._active_tab = "Home"
        self._tab_buttons: dict[str, tk.Button] = {}
        self._tab_frames: dict[str, tk.Frame] = {}
        self._font_base_specs: dict[tk.Widget, tuple[str, int, str, str]] = {}
        self._settings_window: Optional[tk.Toplevel] = None
        self._main_shell: Optional[tk.Frame] = None
        self._load_token = 0
        self._spinner_index = 0
        self._loading_after_id: Optional[str] = None
        self._pending_after_ids: list[str] = []
        self.chart_category = tk.StringVar(value="Ogólne zdarzenia")
        self._active_chart_area: Optional[tk.Frame] = None
        self._active_chart_token = 0

        self._set_app_icon()
        self._setup_style()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        loading_screen = self._build_startup_loading_screen()
        try:
            self.update_idletasks()
            self.update()
        except Exception:
            pass

        try:
            if data is None:
                data = DataStore(base_dir or Path(__file__).resolve().parent)
            self.data_store = data
            self.plotter = IntersectionPlots(data)
            self.all_intersections = self.data_store.get_intersections()

            try:
                loading_screen.destroy()
            except Exception:
                pass

            self._build_layout()
        except Exception as exc:
            try:
                loading_screen.destroy()
            except Exception:
                pass
            try:
                messagebox.showerror("Błąd wczytywania danych", str(exc), parent=self)
            except Exception:
                pass
            try:
                self.destroy()
            except Exception:
                pass
            raise SystemExit(1)

    def _build_startup_loading_screen(self) -> tk.Frame:
        frame = tk.Frame(self, bg=COLORS["bg"])
        frame.pack(fill="both", expand=True)

        card = tk.Frame(
            frame,
            bg=COLORS["panel"],
            highlightthickness=1,
            highlightbackground=COLORS["border"],
        )
        card.place(relx=0.5, rely=0.5, anchor="center", width=520, height=230)

        tk.Label(
            card,
            text="Ładowanie dashboardu",
            bg=COLORS["panel"],
            fg=COLORS["primary_dark"],
            font=("Segoe UI", 20, "bold"),
        ).pack(pady=(42, 10))
        tk.Label(
            card,
            text="Trwa wczytywanie danych, opisów i widoków aplikacji.\nTo może potrwać kilka sekund.",
            bg=COLORS["panel"],
            fg=COLORS["text"],
            font=("Segoe UI", 11),
            justify="center",
        ).pack(pady=(0, 20))

        dots = tk.Label(
            card,
            text="Proszę czekać...",
            bg=COLORS["panel"],
            fg=COLORS["muted"],
            font=FONT_NORMAL,
        )
        dots.pack()
        return frame

    def _load_user_settings(self) -> dict:
        try:
            if self._settings_path.exists():
                return json.loads(self._settings_path.read_text(encoding="utf-8"))
        except Exception:
            pass
        return {}

    def _save_user_settings(self):
        try:
            payload = {
                "font_size_level": int(self.font_size_level.get()),
                "dark_mode": bool(self.dark_mode_enabled.get()),
            }
            self._settings_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception:
            pass

    def _apply_color_palette(self, dark: bool):
        COLORS.clear()
        COLORS.update(DARK_COLORS if dark else LIGHT_COLORS)

    def _rebuild_interface_for_theme(self):
        self._load_token += 1
        self._active_chart_token += 1
        self._cancel_pending_jobs()
        self._destroy_plot_canvases()
        self._font_base_specs.clear()
        current_tab = self._active_tab
        current_id = self.current_id
        for child in list(self.winfo_children()):
            try:
                child.destroy()
            except Exception:
                pass
        self.configure(bg=COLORS["bg"])
        self._tab_buttons.clear()
        self._tab_frames.clear()
        self._stats_images = []
        self._setup_style()
        self._build_layout()
        if current_tab in self._tab_frames:
            self.show_tab(current_tab)
        if current_id is not None:
            self.current_id = current_id
            if self._active_tab == "Skrzyżowania":
                self._request_intersection_load(current_id)
        self._apply_font_settings()

    def _on_dark_mode_changed(self):
        old_colors = dict(COLORS)
        self._apply_color_palette(self.dark_mode_enabled.get())
        self._save_user_settings()
        self._apply_theme_without_full_rebuild(old_colors)

    def _apply_theme_without_full_rebuild(self, old_colors: dict):
        self.configure(bg=COLORS["bg"])
        self._setup_style()
        mapping = {value: COLORS[key] for key, value in old_colors.items() if key in COLORS}
        self._recolor_widget_tree(self, mapping)
        try:
            self.show_tab(self._active_tab)
        except Exception:
            pass
        if hasattr(self, "_modeling_buttons") and hasattr(self, "modeling_section"):
            try:
                self._show_modeling_section(self.modeling_section.get())
            except Exception:
                pass
        self._apply_font_settings()

    def _recolor_widget_tree(self, widget: tk.Widget, mapping: dict):
        self._recolor_single_widget(widget, mapping)
        for child in widget.winfo_children():
            self._recolor_widget_tree(child, mapping)

    def _recolor_single_widget(self, widget: tk.Widget, mapping: dict):
        option_names = (
            "bg", "background", "fg", "foreground", "activebackground", "activeforeground",
            "highlightbackground", "highlightcolor", "insertbackground", "selectbackground",
            "selectforeground", "disabledforeground",
        )
        for option in option_names:
            try:
                current = widget.cget(option)
            except Exception:
                continue
            if current in mapping:
                try:
                    widget.configure(**{option: mapping[current]})
                except Exception:
                    pass
        if isinstance(widget, tk.Text):
            try:
                widget.configure(bg=COLORS["panel"], fg=COLORS["text"], insertbackground=COLORS["text"])
            except Exception:
                pass
            self._refresh_text_widget_fonts(widget, self._font_offset())

    def _set_app_icon(self):
        """Ustawia ikonę aplikacji z pliku app_icon.png obok skryptu, jeśli plik istnieje."""
        icon_path = Path(__file__).resolve().parent / "app_icon.png"
        if not icon_path.exists():
            return
        try:
            self._icon_image = tk.PhotoImage(file=str(icon_path))
            self.iconphoto(True, self._icon_image)
        except Exception:
            pass

    def _setup_style(self):
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("TFrame", background=COLORS["bg"])
        style.configure("Panel.TFrame", background=COLORS["panel"], relief="flat")
        style.configure("TLabel", background=COLORS["bg"], foreground=COLORS["text"], font=FONT_NORMAL)
        style.configure("TCombobox", padding=5)

    def _build_layout(self):
        shell = tk.Frame(self, bg=COLORS["bg"])
        self._main_shell = shell
        shell.pack(fill="both", expand=True, padx=12, pady=12)

        self._build_top_nav(shell)

        self.content_container = tk.Frame(shell, bg=COLORS["bg"])
        self.content_container.pack(fill="both", expand=True, pady=(10, 0))

        for tab_name in ["Home", "Skrzyżowania", "Modelowanie"]:
            frame = tk.Frame(self.content_container, bg=COLORS["bg"])
            frame.grid(row=0, column=0, sticky="nsew")
            self._tab_frames[tab_name] = frame
        self.content_container.grid_rowconfigure(0, weight=1)
        self.content_container.grid_columnconfigure(0, weight=1)

        self._build_home_tab(self._tab_frames["Home"])
        self._build_intersections_tab(self._tab_frames["Skrzyżowania"])
        self._build_modeling_tab(self._tab_frames["Modelowanie"])

        self.show_tab("Home")

    def _build_top_nav(self, parent):
        nav = tk.Frame(parent, bg=COLORS["panel"], highlightthickness=1, highlightbackground=COLORS["border"])
        nav.pack(fill="x")

        title = tk.Label(
            nav,
            text="Dashboard bezpieczeństwa skrzyżowań",
            bg=COLORS["panel"],
            fg=COLORS["primary_dark"],
            font=("Segoe UI", 13, "bold"),
        )
        title.pack(side="left", padx=16, pady=10)

        btn_frame = tk.Frame(nav, bg=COLORS["panel"])
        btn_frame.pack(side="right", padx=10, pady=8)

        settings_btn = tk.Button(
            btn_frame,
            text="⚙",
            width=4,
            relief="flat",
            bd=0,
            cursor="hand2",
            bg=COLORS["primary_soft"],
            fg=COLORS["primary_dark"],
            activebackground=COLORS["border"],
            activeforeground=COLORS["primary_dark"],
            font=("Segoe UI", 12, "bold"),
            command=self._open_settings,
        )
        settings_btn.pack(side="left", padx=(0, 8), ipady=4)
        self.settings_button = settings_btn
        ToolTip(settings_btn, "Opcje aplikacji")

        for tab_name in ["Home", "Skrzyżowania", "Modelowanie"]:
            btn = tk.Button(
                btn_frame,
                text=tab_name,
                width=16,
                relief="flat",
                bd=0,
                cursor="hand2",
                font=("Segoe UI", 10),
                command=lambda name=tab_name: self.show_tab(name),
            )
            btn.pack(side="left", padx=3, ipady=6)
            self._tab_buttons[tab_name] = btn

    def show_tab(self, tab_name: str):
        self._active_tab = tab_name
        self._tab_frames[tab_name].tkraise()
        for name, btn in self._tab_buttons.items():
            self._font_base_specs.pop(btn, None)
            if name == tab_name:
                btn.configure(
                    bg=COLORS["primary"],
                    fg="white",
                    activebackground=COLORS["primary_dark"],
                    activeforeground="white",
                    font=("Segoe UI", 10, "bold"),
                )
            else:
                btn.configure(
                    bg=COLORS["primary_soft"],
                    fg=COLORS["text"],
                    activebackground=COLORS["border"],
                    activeforeground=COLORS["text"],
                    font=("Segoe UI", 10),
                )
        self._apply_font_settings()

    # USTAWIENIA WYGLĄDU

    def _font_offset(self) -> int:
        return {0: 0, 1: 2, 2: 4}.get(int(self.font_size_level.get()), 0)

    def _open_settings(self):
        if self._settings_window is not None and self._settings_window.winfo_exists():
            self._settings_window.lift()
            return

        win = tk.Toplevel(self)
        self._settings_window = win
        win.title("Opcje")
        win.geometry("460x320")
        win.configure(bg=COLORS["bg"])
        win.transient(self)

        card = self._card(win)
        card.pack(fill="both", expand=True, padx=16, pady=16)
        tk.Label(
            card,
            text="Ustawienia widoku",
            bg=COLORS["panel"],
            fg=COLORS["primary_dark"],
            font=FONT_H2,
        ).pack(anchor="w", padx=18, pady=(16, 8))

        tk.Label(
            card,
            text="Rozmiar czcionki",
            bg=COLORS["panel"],
            fg=COLORS["muted"],
            font=FONT_NORMAL,
        ).pack(anchor="w", padx=18, pady=(4, 4))

        scale = tk.Scale(
            card,
            from_=0,
            to=2,
            orient="horizontal",
            showvalue=False,
            resolution=1,
            variable=self.font_size_level,
            bg=COLORS["panel"],
            fg=COLORS["text"],
            activebackground=COLORS["primary"],
            highlightthickness=0,
            troughcolor=COLORS["primary_soft"],
            command=lambda _value: (self._apply_font_settings(), self._save_user_settings()),
        )
        scale.pack(fill="x", padx=18, pady=(0, 2))

        labels = tk.Frame(card, bg=COLORS["panel"])
        labels.pack(fill="x", padx=18, pady=(0, 16))
        label_specs = [("Normalne", "w"), ("Duże", ""), ("Ogromne", "e")]
        for i, (label, sticky) in enumerate(label_specs):
            labels.grid_columnconfigure(i, weight=1)
            tk.Label(
                labels,
                text=label,
                bg=COLORS["panel"],
                fg=COLORS["muted"],
                font=FONT_SMALL,
            ).grid(row=0, column=i, sticky=sticky)

        sep = tk.Frame(card, bg=COLORS["border"], height=1)
        sep.pack(fill="x", padx=18, pady=(0, 14))

        dark_row = tk.Frame(card, bg=COLORS["panel"])
        dark_row.pack(fill="x", padx=18, pady=(0, 8))
        tk.Label(
            dark_row,
            text="Tryb ciemny",
            bg=COLORS["panel"],
            fg=COLORS["text"],
            font=FONT_NORMAL,
        ).pack(side="left")
        check = tk.Checkbutton(
            dark_row,
            variable=self.dark_mode_enabled,
            command=self._on_dark_mode_changed,
            bg=COLORS["panel"],
            fg=COLORS["text"],
            activebackground=COLORS["panel"],
            activeforeground=COLORS["text"],
            selectcolor=COLORS["panel_alt"],
        )
        check.pack(side="right")

        tk.Label(
            card,
            text=(
                "Ustawienia są zapisywane w pliku app_settings.json obok aplikacji. "
                "Rozmiar tekstu wpływa na aktualnie widoczne elementy; wykresy zachowują własny rozmiar."
            ),
            bg=COLORS["panel"],
            fg=COLORS["muted"],
            font=FONT_SMALL,
            wraplength=390,
            justify="left",
        ).pack(anchor="w", padx=18, pady=(8, 10))

        self._apply_font_settings()

    def _apply_font_settings(self):
        """Skaluje czcionki wszystkich aktualnie istniejących tekstów bez przebudowy widoku."""
        offset = self._font_offset()
        self._apply_font_recursive(self, offset)
        self._refresh_text_widget_fonts(self, offset)
        try:
            style = ttk.Style(self)
            style.configure("TLabel", font=("Segoe UI", 10 + offset))
            style.configure("TCombobox", font=("Segoe UI", 10 + offset))
            style.configure("TEntry", font=("Segoe UI", 10 + offset))
        except Exception:
            pass

    def _apply_font_recursive(self, widget: tk.Widget, offset: int):
        self._apply_font_to_widget(widget, offset)
        try:
            children = widget.winfo_children()
        except Exception:
            children = []
        for child in children:
            self._apply_font_recursive(child, offset)

    def _apply_font_to_widget(self, widget: tk.Widget, offset: int):
        try:
            current_font = widget.cget("font")
        except Exception:
            return
        if not current_font:
            return

        try:
            if widget not in self._font_base_specs:
                f = tkfont.Font(font=current_font)
                family = f.actual("family") or "Segoe UI"
                size = int(f.actual("size") or 10)
                if size < 0:
                    size = abs(size)
                weight = f.actual("weight") or "normal"
                slant = f.actual("slant") or "roman"
                self._font_base_specs[widget] = (family, size, weight, slant)
            family, size, weight, slant = self._font_base_specs[widget]
            new_size = max(7, size + offset)
            spec = (family, new_size)
            if weight == "bold" and slant == "italic":
                spec = (family, new_size, "bold", "italic")
            elif weight == "bold":
                spec = (family, new_size, "bold")
            elif slant == "italic":
                spec = (family, new_size, "italic")
            widget.configure(font=spec)
        except Exception:
            pass

    def _refresh_text_widget_fonts(self, widget: tk.Widget, offset: int):
        """Aktualizuje tagi i czcionki w widgetach Text, które nie reagują dobrze na samą zmianę opcji font."""
        try:
            if isinstance(widget, tk.Text):
                base = 10 + offset
                widget.configure(font=("Segoe UI", base))
                # Tagi używane przez renderer Markdown w zakładce Statystyki.
                widget.tag_configure("h2", font=("Segoe UI", 18 + offset, "bold"), foreground=COLORS["primary_dark"], spacing1=18, spacing3=8)
                widget.tag_configure("h3", font=("Segoe UI", 13 + offset, "bold"), foreground=COLORS["primary_dark"], spacing1=14, spacing3=6)
                widget.tag_configure("h4", font=("Segoe UI", 11 + offset, "bold"), foreground=COLORS["primary_dark"], spacing1=10, spacing3=4)
                widget.tag_configure("paragraph", font=("Segoe UI", 10 + offset), foreground=COLORS["text"], spacing3=8, lmargin1=0, lmargin2=0)
                widget.tag_configure("bullet", font=("Segoe UI", 10 + offset), foreground=COLORS["text"], spacing3=4, lmargin1=20, lmargin2=38)
                widget.tag_configure("caption", font=("Segoe UI", 9 + offset), foreground=COLORS["muted"], spacing1=6, spacing3=4)
                widget.tag_configure("separator", font=("Segoe UI", 6 + offset), foreground=COLORS["border"], spacing1=10, spacing3=10)
                widget.tag_configure("error", font=("Segoe UI", 10 + offset, "bold"), foreground=COLORS["danger"], spacing3=8)
        except Exception:
            pass

        try:
            children = widget.winfo_children()
        except Exception:
            children = []
        for child in children:
            self._refresh_text_widget_fonts(child, offset)

    def _build_placeholder(self, parent, title: str, subtitle: str):
        card = self._card(parent)
        card.pack(fill="both", expand=True, padx=24, pady=24)
        tk.Label(card, text=title, bg=COLORS["panel"], fg=COLORS["primary_dark"], font=FONT_TITLE).pack(pady=(80, 10))
        tk.Label(card, text=subtitle, bg=COLORS["panel"], fg=COLORS["muted"], font=("Segoe UI", 12)).pack()

    # HOME
    def _build_home_tab(self, parent):
        scroll = ScrollableFrame(parent)
        scroll.pack(fill="both", expand=True)
        root = scroll.content

        hero = self._card(root)
        hero.pack(fill="x", padx=24, pady=(24, 14))
        tk.Label(
            hero,
            text="Dashboard bezpieczeństwa skrzyżowań w Warszawie",
            bg=COLORS["panel"],
            fg=COLORS["primary_dark"],
            font=FONT_H1,
            wraplength=1100,
            justify="left",
        ).pack(anchor="w", padx=24, pady=(22, 8))
        tk.Label(
            hero,
            text=(
                "Aplikacja łączy dane o zdarzeniach drogowych, natężeniu ruchu oraz cechach infrastrukturalnych "
                "wybranych warszawskich skrzyżowań. Jej celem jest szybkie porównanie miejsc, wskazanie potencjalnych "
                "czynników ryzyka oraz udostępnienie wyników modelowania w czytelnej formie dashboardu."
            ),
            bg=COLORS["panel"],
            fg=COLORS["text"],
            font=("Segoe UI", 11),
            wraplength=1120,
            justify="left",
        ).pack(anchor="w", padx=24, pady=(0, 18))

        overview = self.data_store.get_home_overview()
        kpi = tk.Frame(hero, bg=COLORS["panel"])
        kpi.pack(fill="x", padx=22, pady=(0, 22))
        items = [
            ("Liczba zdarzeń", fmt_number(overview["events_count"]), "pełny zbiór danych"),
            ("Liczba skrzyżowań", fmt_number(overview["intersection_count"]), "unikalne ID"),
            ("Zakres lat", overview["year_range"], "okres zdarzeń"),
            ("Najczęstsze wykroczenie", overview["top_violation"], "dominanta w zbiorze"),
            ("Najwięcej zdarzeń", overview["top_intersection"], "skrzyżowanie z największą liczbą wpisów"),
        ]
        for i, (label, value, hint) in enumerate(items):
            card = self._kpi_card(kpi, label, value, hint, COLORS["primary_dark"])
            card.grid(row=0, column=i, sticky="nsew", padx=(0 if i == 0 else 7, 0))
            kpi.grid_columnconfigure(i, weight=1)

        grid = tk.Frame(root, bg=COLORS["bg"])
        grid.pack(fill="x", padx=24, pady=(0, 14))
        grid.grid_columnconfigure(0, weight=1)
        grid.grid_columnconfigure(1, weight=1)

        self._home_card(
            grid,
            "Co można sprawdzić?",
            [
                "pełną listę analizowanych skrzyżowań z wyszukiwaniem po nazwie,",
                "profil pojedynczego skrzyżowania: KPI, natężenie ruchu, infrastrukturę i opis analityczny,",
                "wykresy zdarzeń dla wybranego miejsca, pogrupowane według typu analizy,",
                "wyniki modelowania i klasyfikacji zdarzeń drogowych w zakładce „Modelowanie”,",
                "interpretacje modeli wraz z grafikami.",
            ],
            row=0,
            col=0,
        )
        self._home_card(
            grid,
            "Instrukcja obsługi",
            [
                "przejdź do zakładki „Skrzyżowania”, aby wybrać konkretne miejsce z listy,",
                "po kliknięciu poczekaj na załadowanie szczegółów,",
                "zmieniaj typ wykresów z listy rozwijanej po prawej stronie widoku,",
                "przejdź do „Modelowania”, aby przeczytać pełne interpretacje wyników statystycznych,",
                "użyj zębatki w prawym górnym rogu, aby zmienić ustawienia aplikacji.",
            ],
            row=0,
            col=1,
        )

        grid2 = tk.Frame(root, bg=COLORS["bg"])
        grid2.pack(fill="x", padx=24, pady=(0, 14))
        grid2.grid_columnconfigure(0, weight=1)
        grid2.grid_columnconfigure(1, weight=1)
        self._home_card(
            grid2,
            "Jak czytać kafelki KPI?",
            [
                "kolor czerwony oznacza wartość wysoką na tle pozostałych skrzyżowań,",
                "kolor żółty oznacza wartość powyżej mediany,",
                "kolor zielony oznacza wartość poniżej mediany lub brak sygnału podwyższonego poziomu,",
                "kafelki są skrótem informacyjnym — szczegółowa interpretacja wymaga sprawdzenia wykresów i tabel.",
            ],
            row=0,
            col=0,
        )
        self._home_card(
            grid2,
            "Zakres i ograniczenia",
            [
                "dane o zdarzeniach i dane o natężeniu ruchu mogą pochodzić z różnych okresów pomiarowych,",
                "natężenie ruchu stanowi kontekst interpretacyjny, a nie automatyczne wyjaśnienie liczby zdarzeń,",
                "dla części skrzyżowań mogą pojawiać się uwagi o jakości lub odległości punktu pomiarowego APR,",
                "modele wskazują asocjacje i wzorce w danych, które nie zawsze oznaczają bezpośrednią przyczynowość.",
            ],
            row=0,
            col=1,
        )

        streamlit_card = self._card(root)
        streamlit_card.pack(fill="x", padx=24, pady=(0, 24))
        tk.Label(
            streamlit_card,
            text="Przegląd ogólny całego zbioru danych",
            bg=COLORS["panel"],
            fg=COLORS["primary_dark"],
            font=FONT_H2,
        ).pack(anchor="w", padx=18, pady=(16, 8))
        tk.Label(
            streamlit_card,
            text=(
                "Ogólny przegląd danych pozwala spojrzeć na problem bezpieczeństwa ruchu nie przez pryzmat pojedynczego miejsca, "
                "ale całego zbioru zdarzeń. Analiza obejmuje zmienność liczby zdarzeń w czasie, wskazanie najbardziej obciążonych "
                "skrzyżowań, dominujące typy wykroczeń i zdarzeń oraz cykliczność tygodniową i sezonową. Dzięki temu można odróżnić "
                "miejsca stale problematyczne od takich, w których liczba zdarzeń jest bardziej incydentalna lub zależna od warunków."
            ),
            bg=COLORS["panel"],
            fg=COLORS["text"],
            font=FONT_NORMAL,
            wraplength=1120,
            justify="left",
        ).pack(anchor="w", padx=22, pady=(0, 8))
        streamlit_points = [
            "trend roczny pokazuje, czy problem bezpieczeństwa narasta, stabilizuje się, czy słabnie w kolejnych latach,",
            "ranking skrzyżowań pomaga szybko wskazać miejsca wymagające najpilniejszej uwagi lub dalszego audytu,",
            "struktura wykroczeń i typów zdarzeń mówi, jakie zachowania kierowców najczęściej prowadzą do kolizji,",
            "rozkład według dni tygodnia i miesięcy pozwala wychwycić powtarzalność związaną z ruchem dojazdowym, sezonowością lub warunkami pogodowymi,",
            "warunki oświetleniowe, pogodowe i stan sygnalizacji pomagają ocenić, czy zdarzenia częściej wynikają z infrastruktury, zachowań uczestników ruchu czy otoczenia,",
            "wnioski z tej części należy traktować jako tło dla analizy pojedynczego skrzyżowania oraz dla wyników modelowania.",
        ]
        for bullet in streamlit_points:
            tk.Label(
                streamlit_card,
                text=f"• {bullet}",
                bg=COLORS["panel"],
                fg=COLORS["text"],
                font=FONT_NORMAL,
                wraplength=1080,
                justify="left",
            ).pack(anchor="w", padx=28, pady=2)
        tk.Frame(streamlit_card, bg=COLORS["panel"], height=14).pack()

        self._render_home_overview_charts(root)

    def _render_home_overview_charts(self, parent):
        """Dodaje pionowy zestaw lekkich wykresów ogólnych na stronie Home."""
        try:
            df = self.data_store.events.copy()
            if df.empty:
                return

            charts_card = self._card(parent)
            charts_card.pack(fill="x", padx=24, pady=(0, 24))
            tk.Label(
                charts_card,
                text="Podgląd ogólnych wzorców w danych",
                bg=COLORS["panel"],
                fg=COLORS["primary_dark"],
                font=FONT_H2,
            ).pack(anchor="w", padx=18, pady=(16, 4))
            chart_specs = [
                ("Trend roczny", self._make_home_year_trend_figure(df)),
                ("Najbardziej obciążone skrzyżowania", self._make_home_top_intersections_figure(df, top_n=10)),
                ("Najczęstsze rodzaje zdarzeń", self._make_home_event_types_figure(df, top_n=8)),
                ("Zdarzenia według dnia tygodnia", self._make_home_weekday_figure(df)),
                ("Sezonowość miesięczna", self._make_home_month_figure(df)),
            ]

            if not hasattr(self, "_home_figures"):
                self._home_figures = []

            for title, fig in chart_specs:
                try:
                    chart_frame = tk.Frame(
                        charts_card,
                        bg=COLORS["panel_alt"],
                        highlightthickness=1,
                        highlightbackground=COLORS["border"],
                    )
                    chart_frame.pack(fill="x", padx=16, pady=(0, 18))
                    chart_frame.pack_propagate(True)

                    tk.Label(
                        chart_frame,
                        text=title,
                        bg=COLORS["panel_alt"],
                        fg=COLORS["primary_dark"],
                        font=FONT_H2,
                    ).pack(anchor="w", padx=12, pady=(10, 2))

                    self._home_figures.append(fig)
                    self._embed_home_figure(chart_frame, fig)
                    tk.Frame(chart_frame, bg=COLORS["panel_alt"], height=8).pack(fill="x")
                except Exception:
                    # Zostawiamy puste pole w razie wyskoczenia błędu. (nie zdarza się)
                    spacer = tk.Frame(charts_card, bg=COLORS["panel"], height=8)
                    spacer.pack(fill="x", padx=16, pady=(0, 8))
                    continue
        except Exception:
            return

    def _make_home_year_trend_figure(self, df: pd.DataFrame) -> Figure:
        if "rok" not in df.columns:
            values = pd.Series(dtype=int)
        else:
            values = df.dropna(subset=["rok"]).groupby("rok").size().sort_index()
        fig, ax = plt.subplots(figsize=(10.5, 3.8))
        if not values.empty:
            x = values.index.astype(int)
            y = values.values
            ax.plot(x, y, marker="o", linewidth=2.2)
            ax.fill_between(x, y, alpha=0.12)
            for xi, yi in zip(x, y):
                ax.text(xi, yi, f"{int(yi)}", ha="center", va="bottom", fontsize=8)
            ax.set_xticks(list(x))
        ax.set_title("Liczba zdarzeń w kolejnych latach", fontweight="bold")
        ax.set_xlabel("Rok")
        ax.set_ylabel("Liczba zdarzeń")
        ax.spines["right"].set_visible(False)
        ax.spines["top"].set_visible(False)
        fig.tight_layout()
        return fig

    def _make_home_top_intersections_figure(self, df: pd.DataFrame, top_n: int = 10) -> Figure:
        if "skrzyzowanie" not in df.columns:
            values = pd.Series(dtype=int)
        else:
            values = df["skrzyzowanie"].value_counts().head(top_n).sort_values()
        fig, ax = plt.subplots(figsize=(10.5, 5.2))
        if not values.empty:
            labels = [str(x)[:42] + ("..." if len(str(x)) > 42 else "") for x in values.index]
            bars = ax.barh(labels, values.values)
            ax.bar_label(bars, padding=4, fontsize=8)
        ax.set_title(f"Skrzyżowania z największą liczbą zdarzeń — Top {top_n}", fontweight="bold")
        ax.set_xlabel("Liczba zdarzeń")
        ax.spines["right"].set_visible(False)
        ax.spines["top"].set_visible(False)
        fig.tight_layout()
        return fig

    def _make_home_event_types_figure(self, df: pd.DataFrame, top_n: int = 8) -> Figure:
        if "rodzaj_zdarzenia" not in df.columns:
            values = pd.Series(dtype=int)
        else:
            values = df["rodzaj_zdarzenia"].value_counts().head(top_n).sort_values()
        fig, ax = plt.subplots(figsize=(10.5, 4.8))
        if not values.empty:
            labels = [str(x)[:52] + ("..." if len(str(x)) > 52 else "") for x in values.index]
            bars = ax.barh(labels, values.values)
            ax.bar_label(bars, padding=4, fontsize=8)
        ax.set_title("Najczęstsze rodzaje zdarzeń", fontweight="bold")
        ax.set_xlabel("Liczba zdarzeń")
        ax.spines["right"].set_visible(False)
        ax.spines["top"].set_visible(False)
        fig.tight_layout()
        return fig

    def _make_home_weekday_figure(self, df: pd.DataFrame) -> Figure:
        labels = ["Pon", "Wt", "Śr", "Czw", "Pt", "Sob", "Nd"]
        if "dzien_tygodnia" not in df.columns:
            values = pd.Series([0] * 7, index=range(7))
        else:
            values = df["dzien_tygodnia"].value_counts().reindex(range(7), fill_value=0).sort_index()
        fig, ax = plt.subplots(figsize=(6.0, 3.4))
        bars = ax.bar(labels, values.values)
        ax.bar_label(bars, padding=3, fontsize=8)
        ax.set_title("Zdarzenia według dnia tygodnia", fontweight="bold")
        ax.set_ylabel("Liczba zdarzeń")
        ax.spines["right"].set_visible(False)
        ax.spines["top"].set_visible(False)
        fig.tight_layout()
        return fig

    def _make_home_month_figure(self, df: pd.DataFrame) -> Figure:
        labels = ["Sty", "Lut", "Mar", "Kwi", "Maj", "Cze", "Lip", "Sie", "Wrz", "Paź", "Lis", "Gru"]
        values = df["miesiac"].value_counts().reindex(range(1, 13), fill_value=0).sort_index() if "miesiac" in df.columns else pd.Series([0] * 12)
        fig, ax = plt.subplots(figsize=(6.0, 3.4))
        bars = ax.bar(labels, values.values)
        ax.bar_label(bars, padding=3, fontsize=7)
        ax.set_title("Sezonowość według miesięcy", fontweight="bold")
        ax.set_ylabel("Liczba zdarzeń")
        ax.spines["right"].set_visible(False)
        ax.spines["top"].set_visible(False)
        fig.tight_layout()
        return fig

    def _embed_home_figure(self, parent, fig: Figure):
        canvas = FigureCanvasTkAgg(fig, master=parent)
        canvas.draw()
        widget = canvas.get_tk_widget()
        widget.configure(bg=COLORS["panel_alt"], highlightthickness=0)
        try:
            width = max(780, int(fig.get_figwidth() * 105))
            height = max(330, int(fig.get_figheight() * 105))
            widget.configure(width=width, height=height)
        except Exception:
            pass
        widget.pack(fill="x", expand=False, padx=8, pady=(4, 10))
        self._bind_mousewheel_recursive(widget)
        self._plot_canvases.append(canvas)

    def _home_card(self, parent, title: str, bullets: list[str], row: int, col: int):
        card = self._card(parent)
        card.grid(row=row, column=col, sticky="nsew", padx=(0 if col == 0 else 8, 8 if col == 0 else 0), pady=0)
        tk.Label(card, text=title, bg=COLORS["panel"], fg=COLORS["primary_dark"], font=FONT_H2).pack(anchor="w", padx=18, pady=(16, 8))
        for bullet in bullets:
            tk.Label(
                card,
                text=f"• {bullet}",
                bg=COLORS["panel"],
                fg=COLORS["text"],
                font=FONT_NORMAL,
                wraplength=520,
                justify="left",
            ).pack(anchor="w", padx=22, pady=3)
        tk.Frame(card, bg=COLORS["panel"], height=10).pack()

    # MODELOWANIE

    def _build_modeling_tab(self, parent):
        """Zakładka Modelowanie z dwoma podsekcjami.

        Obie podsekcje używają natywnych widgetów Text z osadzonymi grafikami,
        ponieważ taki układ przewija się płynniej niż długi Canvas z setkami ramek.
        """
        outer = tk.Frame(parent, bg=COLORS["bg"])
        outer.pack(fill="both", expand=True, padx=24, pady=24)

        container = self._card(outer)
        container.pack(fill="both", expand=True)

        top = tk.Frame(container, bg=COLORS["panel"])
        top.pack(fill="x", padx=16, pady=(14, 8))
        tk.Label(
            top,
            text="Modelowanie",
            bg=COLORS["panel"],
            fg=COLORS["primary_dark"],
            font=FONT_H2,
        ).pack(side="left")

        self.modeling_section = tk.StringVar(value="Predykcja")
        btns = tk.Frame(top, bg=COLORS["panel"])
        btns.pack(side="right")
        self._modeling_buttons: dict[str, tk.Button] = {}
        sections = [
            ("Predykcja", "Predykcja skrzyżowań"),
            ("Klasyfikacja", "Klasyfikacja zdarzeń"),
        ]
        for key, label in sections:
            btn = tk.Button(
                btns,
                text=label,
                relief="flat",
                bd=0,
                cursor="hand2",
                font=("Segoe UI", 10),
                command=lambda k=key: self._show_modeling_section(k),
                width=24,
            )
            btn.pack(side="left", padx=3, ipady=5)
            self._modeling_buttons[key] = btn

        self.modeling_container = tk.Frame(container, bg=COLORS["panel"])
        self.modeling_container.pack(fill="both", expand=True, padx=16, pady=(0, 16))
        self._modeling_frames: dict[str, tk.Frame] = {}
        for key, _label in sections:
            frame = tk.Frame(self.modeling_container, bg=COLORS["panel"])
            frame.grid(row=0, column=0, sticky="nsew")
            self._modeling_frames[key] = frame
        self.modeling_container.grid_rowconfigure(0, weight=1)
        self.modeling_container.grid_columnconfigure(0, weight=1)

        self._build_prediction_modeling_section(self._modeling_frames["Predykcja"])
        self._build_classification_modeling_section(self._modeling_frames["Klasyfikacja"])
        self._show_modeling_section("Predykcja")

    def _show_modeling_section(self, key: str):
        self.modeling_section.set(key)
        self._modeling_frames[key].tkraise()
        for name, btn in self._modeling_buttons.items():
            self._font_base_specs.pop(btn, None)
            if name == key:
                btn.configure(bg=COLORS["primary"], fg="white", activebackground=COLORS["primary_dark"], activeforeground="white", font=("Segoe UI", 10, "bold"))
            else:
                btn.configure(bg=COLORS["primary_soft"], fg=COLORS["text"], activebackground=COLORS["border"], activeforeground=COLORS["text"], font=("Segoe UI", 10))
        self._apply_font_settings()

    def _build_prediction_modeling_section(self, parent):
        text_widget = self._create_markdown_text_view(parent)
        self._prediction_text = text_widget
        self._prediction_images: list[tk.PhotoImage] = []

        text_widget.configure(state="normal")
        # Zabezpieczenie, w razie czego jeśli wykresów nie ma. Czyli brak folderu.
        if not self.data_store.prediction_description_files:
            text_widget.insert("end", "Nie znaleziono plików opis_..._NB.md.\n\n", "error")
            text_widget.insert(
                "end",
                "Umieść pliki opis_macierz_korelacji_NB.md, opis_profile_klastry_NB.md, opis_rozklad_klastry_NB.md, opis_rzeczywiste_i_predykcje_NB.md oraz opis_wplyw_czynnikow_NB.md w folderze Opisy_wykresy obok aplikacji.",
                "paragraph",
            )
        else:
            intro = (
                "Ta sekcja prezentuje analizę i predykcję liczby zdarzeń drogowych na poziomie skrzyżowań. "
                "Zestawia korelacje, profile klastrów, rozkład liczby wypadków, porównanie wartości rzeczywistych z predykcją oraz wpływ czynników infrastrukturalnych.\n\n"
            )
            text_widget.insert("end", intro, "paragraph")
            for path in self.data_store.prediction_description_files:
                self._render_prediction_description(text_widget, path)
        text_widget.configure(state="disabled")
        self._apply_font_settings()

    def _build_classification_modeling_section(self, parent):
        text_widget = self._create_markdown_text_view(parent)
        self._classification_text = text_widget
        self._stats_images.clear()
        text_widget.configure(state="normal")
        if self.data_store.statistics_md_path is None:
            text_widget.insert("end", "Nie znaleziono pliku interpretacje.md.\n\n", "error")
            text_widget.insert(
                "end",
                "Umieść plik interpretacje.md w tym samym folderze co aplikacja albo w folderze data.",
                "paragraph",
            )
        else:
            self._render_markdown_file(text_widget, self.data_store.statistics_md_path)
        text_widget.configure(state="disabled")
        self._apply_font_settings()

    def _create_markdown_text_view(self, parent) -> tk.Text:
        frame = tk.Frame(parent, bg=COLORS["panel"])
        frame.pack(fill="both", expand=True)
        y_scroll = ttk.Scrollbar(frame, orient="vertical")
        y_scroll.pack(side="right", fill="y")
        text_widget = tk.Text(
            frame,
            wrap="word",
            bg=COLORS["panel"],
            fg=COLORS["text"],
            relief="flat",
            borderwidth=0,
            highlightthickness=0,
            padx=12,
            pady=12,
            font=FONT_NORMAL,
            yscrollcommand=y_scroll.set,
            spacing1=2,
            spacing2=1,
            spacing3=4,
        )
        text_widget.pack(side="left", fill="both", expand=True)
        y_scroll.configure(command=text_widget.yview)
        self._configure_modeling_text_tags(text_widget)
        text_widget.bind("<MouseWheel>", lambda e: self._text_mousewheel(text_widget, e), add="+")
        text_widget.bind("<Button-4>", lambda e: self._text_mousewheel(text_widget, e), add="+")
        text_widget.bind("<Button-5>", lambda e: self._text_mousewheel(text_widget, e), add="+")
        return text_widget

    def _configure_modeling_text_tags(self, text_widget: tk.Text):
        self._refresh_text_widget_fonts(text_widget, self._font_offset())

    def _text_mousewheel(self, text_widget: tk.Text, event):
        try:
            if getattr(event, "num", None) == 4:
                text_widget.yview_scroll(-3, "units")
                return "break"
            if getattr(event, "num", None) == 5:
                text_widget.yview_scroll(3, "units")
                return "break"
            delta = getattr(event, "delta", 0)
            step = int(-1 * (delta / 120)) if delta else 0
            if step == 0:
                step = -1 if delta > 0 else 1
            text_widget.yview_scroll(step * 3, "units")
            return "break"
        except Exception:
            return None

    def _try_generate_prediction_images(self):
        if getattr(self, "_prediction_generation_attempted", False):
            return
        self._prediction_generation_attempted = True

        base = self.data_store.base_dir
        required_files = [base / "DATA.csv", base / "DATA2.csv", base / "DATA3.csv"]
        if not all(path.exists() for path in required_files):
            return
        if not (base / "charts_visual.py").exists():
            return
        if not (base / "data_processing.py").exists():
            return
        if not (base / "clustering_model.py").exists() or not (base / "regression_model.py").exists():
            return

        output_dir = base / "Wygenerowane_wykresy"
        output_dir.mkdir(exist_ok=True)

        expected = {
            "opis_macierz_korelacji_nb": output_dir / "plot_correlation_matrix.png",
            "opis_rozklad_klastry_nb": output_dir / "plot_cluster_boxplot.png",
            "opis_profile_klastry_nb": output_dir / "plot_cluster_profiles_heatmap.png",
            "opis_wplyw_czynnikow_nb": output_dir / "plot_feature_importance.png",
            "opis_rzeczywiste_i_predykcje_nb": output_dir / "plot_actual_vs_predicted.png",
        }
        if all(path.exists() for path in expected.values()):
            return

        old_path = list(sys.path)
        old_show = plt.show
        try:
            if str(base) not in sys.path:
                sys.path.insert(0, str(base))

            from data_processing import load_and_clean_data
            from clustering_model import perform_clustering
            from regression_model import estimate_count_models
            import charts_visual as visual

            manual_data = load_and_clean_data(str(base / "DATA.csv"), str(base / "DATA2.csv"), str(base / "DATA3.csv"))
            data_with_clusters = perform_clustering(manual_data, n_clusters=2)
            y_manual = manual_data["ilosc_wypadkow"]
            X_manual = manual_data.drop(columns=["ilosc_wypadkow"])
            fitted_model = estimate_count_models(X_manual, y_manual, label="SELEKCJA RĘCZNA")

            def capture_to(filename: Path, call: Callable[[], None]):
                if filename.exists():
                    return
                try:
                    plt.close("all")
                    call()
                    fig = plt.gcf()
                    if fig is not None:
                        fig.savefig(filename, dpi=150, bbox_inches="tight")
                    plt.close("all")
                except Exception:
                    plt.close("all")

            plt.show = lambda *args, **kwargs: None
            capture_to(expected["opis_macierz_korelacji_nb"], lambda: visual.plot_correlation_matrix(manual_data, title="Pełna macierz korelacji cech"))
            capture_to(expected["opis_rozklad_klastry_nb"], lambda: visual.plot_cluster_boxplot(data_with_clusters))
            capture_to(expected["opis_profile_klastry_nb"], lambda: visual.plot_cluster_profiles_heatmap(data_with_clusters))
            if fitted_model is not None:
                capture_to(expected["opis_wplyw_czynnikow_nb"], lambda: visual.plot_feature_importance(fitted_model))
                capture_to(expected["opis_rzeczywiste_i_predykcje_nb"], lambda: visual.plot_actual_vs_predicted(data_with_clusters, fitted_model))
        except Exception:
            # Brak któregoś modułu/modelu albo błąd dopasowania nie może blokować GUI.
            return
        finally:
            plt.show = old_show
            sys.path = old_path

    def _render_prediction_description(self, text_widget: tk.Text, path: Path):
        # Najpierw próbujemy znaleźć grafikę o nazwie zgodnej z opisem, a dopiero potem wczytujemy tekst.
        image_path = self._resolve_prediction_image(path)
        if image_path is not None:
            self._render_image_into_text(text_widget, image_path, caption=path.stem.replace("_", " "), image_store=self._prediction_images)
        # Jeśli grafika nie została odnaleziona, nie pokazujemy komunikatu technicznego.
        # Pozostaje sam opis wykresu, a użytkownik nie widzi pustych ostrzeżeń.

        self._render_markdown_file(text_widget, path)
        text_widget.insert("end", "────────────────────────────────────────\n", "separator")

    def _resolve_prediction_image(self, description_path: Path) -> Optional[Path]:
        normalized_stem = normalize_text(description_path.stem)

        image_by_description = {
            "opis_macierz_korelacji_nb": "macierz_korelacji.png",
            "opis_profile_klastry_nb": "profile_klastrow.png",
            "opis_rozklad_klastry_nb": "rozklad_wypadkow_w_klastrach.png",
            "opis_rzeczywiste_i_predykcje_nb": "rzeczywiste_vs_predykcje.png",
            "opis_wplyw_czynnikow_nb": "wplyw_czynnikow.png",
        }

        selected_filename = None
        for key, filename in image_by_description.items():
            if key in normalized_stem:
                selected_filename = filename
                break

        if selected_filename is None:
            return None

        directories = [
            self.data_store.base_dir / "Modelowanie_wykresy",
            Path.cwd() / "Modelowanie_wykresy",
            description_path.parent / "Modelowanie_wykresy",
            self.data_store.base_dir / "Opisy_wykresy" / "Modelowanie_wykresy",
            Path.cwd() / "Opisy_wykresy" / "Modelowanie_wykresy",
        ]

        seen: set[str] = set()
        for directory in directories:
            key = str(directory.resolve()) if directory.exists() else str(directory)
            if key in seen:
                continue
            seen.add(key)
            candidate = directory / selected_filename
            if candidate.exists():
                return candidate

        return None

    def _image_search_directories(self, md_path: Path) -> list[Path]:
        directories = [
            md_path.parent / "Wygenerowane_wykresy",
            md_path.parent / "Gotowe_Wykresy",
            md_path.parent / "Wykresy",
            md_path.parent,
            self.data_store.base_dir / "Opisy_wykresy" / "Wygenerowane_wykresy",
            self.data_store.base_dir / "Opisy_wykresy" / "Gotowe_Wykresy",
            self.data_store.base_dir / "Wygenerowane_wykresy",
            self.data_store.base_dir / "Gotowe_Wykresy",
            self.data_store.base_dir / "Wykresy",
            self.data_store.base_dir,
            Path.cwd() / "Opisy_wykresy" / "Wygenerowane_wykresy",
            Path.cwd() / "Opisy_wykresy" / "Gotowe_Wykresy",
            Path.cwd() / "Wygenerowane_wykresy",
            Path.cwd() / "Gotowe_Wykresy",
            Path.cwd() / "Wykresy",
            Path.cwd(),
        ]
        # Zachowujemy kolejność, ale usuwamy duplikaty.
        unique: list[Path] = []
        seen = set()
        for directory in directories:
            key = str(directory.resolve()) if directory.exists() else str(directory)
            if key not in seen:
                unique.append(directory)
                seen.add(key)
        return unique

    def _render_markdown_file(self, text_widget: tk.Text, path: Path):
        try:
            lines = path.read_text(encoding="utf-8-sig").splitlines()
        except Exception as exc:
            text_widget.insert("end", f"Nie udało się wczytać pliku: {exc}\n", "error")
            return

        paragraph: list[str] = []
        image_re = re.compile(r"!\[(.*?)\]\((.*?)\)")

        def flush_paragraph():
            nonlocal paragraph
            if not paragraph:
                return
            text = " ".join(part.strip() for part in paragraph if part.strip()).strip()
            paragraph = []
            if not text:
                return
            text = self._clean_inline_markdown(text)
            text_widget.insert("end", text + "\n\n", "paragraph")

        for raw_line in lines:
            line = raw_line.rstrip()
            stripped = line.strip()

            if not stripped:
                flush_paragraph()
                continue

            match = image_re.match(stripped)
            if match:
                flush_paragraph()
                alt_text = match.group(1).strip()
                img_ref = match.group(2).strip()
                self._render_markdown_image(text_widget, path, img_ref, alt_text)
                continue

            if stripped == "---":
                flush_paragraph()
                text_widget.insert("end", "────────────────────────────────────────\n", "separator")
                continue

            if stripped.startswith("#"):
                flush_paragraph()
                level = len(stripped) - len(stripped.lstrip("#"))
                title = self._clean_inline_markdown(stripped.lstrip("#").strip())
                tag = "h2" if level <= 2 else ("h3" if level == 3 else "h4")
                text_widget.insert("end", title + "\n", tag)
                continue

            if stripped.startswith("*") or stripped.startswith("-"):
                flush_paragraph()
                bullet = stripped.lstrip("*- ").strip()
                bullet = self._clean_inline_markdown(bullet)
                text_widget.insert("end", f"• {bullet}\n", "bullet")
                continue

            paragraph.append(stripped)

        flush_paragraph()

    def _clean_inline_markdown(self, text: str) -> str:
        text = text.replace("**", "")
        text = text.replace("__", "")
        text = text.replace("`", "")
        return text.strip()

    def _resolve_markdown_image(self, md_path: Path, img_ref: str) -> Optional[Path]:
        decoded = unquote(img_ref).replace("\\", "/")
        ref_path = Path(decoded)
        filename = ref_path.name
        search_paths = [
            md_path.parent / "Wygenerowane_wykresy" / filename,
            md_path.parent / ref_path,
            md_path.parent / "Gotowe_Wykresy" / filename,
            md_path.parent / "Wykresy" / filename,
            md_path.parent / filename,
            self.data_store.base_dir / "Wygenerowane_wykresy" / filename,
            self.data_store.base_dir / "Gotowe_Wykresy" / filename,
            self.data_store.base_dir / "Wykresy" / filename,
            self.data_store.base_dir / filename,
            Path.cwd() / "Wygenerowane_wykresy" / filename,
            Path.cwd() / "Gotowe_Wykresy" / filename,
            Path.cwd() / "Wykresy" / filename,
            Path.cwd() / filename,
        ]
        for candidate in search_paths:
            if candidate.exists():
                return candidate
        # Jeśli ścieżka z markdowna zawiera inny podfolder, szukamy po samej nazwie pliku.
        for root in [md_path.parent, self.data_store.base_dir, Path.cwd()]:
            if not root.exists():
                continue
            try:
                matches = list(root.rglob(filename))
            except Exception:
                matches = []
            if matches:
                return matches[0]
        return None

    def _render_markdown_image(self, text_widget: tk.Text, md_path: Path, img_ref: str, alt_text: str):
        image_path = self._resolve_markdown_image(md_path, img_ref)
        if image_path is None:
            text_widget.insert("end", f"Brak grafiki: {img_ref}\nOczekiwany folder: Wygenerowane_wykresy\n\n", "error")
            return
        self._render_image_into_text(text_widget, image_path, caption=alt_text, image_store=self._stats_images)

    def _render_image_into_text(self, text_widget: tk.Text, image_path: Path, caption: str = "", image_store: Optional[list[tk.PhotoImage]] = None):
        try:
            img = tk.PhotoImage(file=str(image_path))
            max_width = 900
            if img.width() > max_width:
                factor = max(1, int((img.width() + max_width - 1) // max_width))
                img = img.subsample(factor, factor)
            if image_store is None:
                image_store = self._stats_images
            image_store.append(img)
            if caption:
                text_widget.insert("end", caption + "\n", "caption")
            text_widget.image_create("end", image=img, padx=8, pady=8)
            text_widget.insert("end", "\n\n", "paragraph")
        except Exception as exc:
            text_widget.insert("end", f"Nie udało się wyświetlić grafiki {image_path.name}: {exc}\n\n", "error")

    # ZAKŁADKA SKRZYŻOWANIA

    def _build_intersections_tab(self, parent):
        paned = ttk.PanedWindow(parent, orient="horizontal")
        paned.pack(fill="both", expand=True)

        left = tk.Frame(paned, bg=COLORS["panel"], highlightthickness=1, highlightbackground=COLORS["border"])
        paned.add(left, weight=1)

        tk.Label(left, text="Lista skrzyżowań", bg=COLORS["panel"], fg=COLORS["primary_dark"], font=FONT_H2).pack(anchor="w", padx=16, pady=(16, 4))
        tk.Label(left, text="Wybierz skrzyżowanie, aby zobaczyć szczegóły.", bg=COLORS["panel"], fg=COLORS["muted"], font=FONT_SMALL).pack(anchor="w", padx=16, pady=(0, 10))

        search_frame = tk.Frame(left, bg=COLORS["panel"])
        search_frame.pack(fill="x", padx=16, pady=(0, 10))
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *_: self._refresh_intersection_list())
        search = ttk.Entry(search_frame, textvariable=self.search_var)
        search.pack(fill="x")
        ToolTip(search, "Wpisz fragment nazwy skrzyżowania, aby przefiltrować listę.")

        list_frame = tk.Frame(left, bg=COLORS["panel"])
        list_frame.pack(fill="both", expand=True, padx=16, pady=(0, 16))
        self.listbox = tk.Listbox(
            list_frame,
            activestyle="none",
            font=("Segoe UI", 10),
            bg=COLORS["panel_alt"],
            fg=COLORS["text"],
            selectbackground=COLORS["primary"],
            selectforeground="white",
            relief="flat",
            highlightthickness=1,
            highlightbackground=COLORS["border"],
            exportselection=False,
        )
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.listbox.yview)
        self.listbox.configure(yscrollcommand=scrollbar.set)
        self.listbox.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        self.listbox.bind("<<ListboxSelect>>", self._on_intersection_selected)
        self._listbox_ids: list[int] = []
        self._refresh_intersection_list()

        right_outer = ttk.Frame(paned)
        paned.add(right_outer, weight=4)

        self.details_scroll = ScrollableFrame(right_outer)
        self.details_scroll.pack(fill="both", expand=True, padx=(12, 0))
        self.details = self.details_scroll.content

        self._show_empty_details()

    def _refresh_intersection_list(self):
        query = normalize_text(self.search_var.get())
        old_id = self.current_id
        self.listbox.delete(0, "end")
        self._listbox_ids.clear()
        selected_index: Optional[int] = None
        for intersection_id, name in self.all_intersections:
            label = f"{intersection_id:02d}  {name}"
            if query and query not in normalize_text(label):
                continue
            self.listbox.insert("end", label)
            if old_id == intersection_id:
                selected_index = len(self._listbox_ids)
            self._listbox_ids.append(intersection_id)
        if selected_index is not None:
            self.listbox.selection_set(selected_index)
            self.listbox.see(selected_index)

    def _on_intersection_selected(self, _event=None):
        selection = self.listbox.curselection()
        if not selection:
            return
        index = selection[0]
        if index >= len(self._listbox_ids):
            return
        intersection_id = self._listbox_ids[index]
        self._request_intersection_load(intersection_id)

    def _request_intersection_load(self, intersection_id: int):
        intersection_id = int(intersection_id)
        self.current_id = intersection_id
        self._load_token += 1
        token = self._load_token
        self._active_chart_token += 1
        self._cancel_pending_jobs()
        self._render_intersection_shell(intersection_id, token)
        # Krótka zwłoka działa jak debounce: szybkie kliknięcia nie uruchamiają kilku renderów po kolei.
        self._schedule(lambda: self._render_intersection_body_if_current(intersection_id, token), delay=180)

    def _cancel_pending_jobs(self):
        for after_id in self._pending_after_ids:
            try:
                self.after_cancel(after_id)
            except Exception:
                pass
        self._pending_after_ids.clear()
        if self._loading_after_id:
            try:
                self.after_cancel(self._loading_after_id)
            except Exception:
                pass
            self._loading_after_id = None

    def _schedule(self, callback: Callable, delay: int = 1):
        after_id = self.after(delay, callback)
        self._pending_after_ids.append(after_id)
        return after_id

    def _is_current_token(self, token: int) -> bool:
        return token == self._load_token

    def _clear_details(self):
        self._destroy_plot_canvases()
        for child in self.details.winfo_children():
            child.destroy()

    def _destroy_plot_canvases(self):
        for canvas in self.current_plot_canvases:
            try:
                fig = canvas.figure
                canvas.get_tk_widget().destroy()
                plt.close(fig)
            except Exception:
                pass
        self.current_plot_canvases.clear()

    def _show_empty_details(self):
        self._clear_details()
        card = self._card(self.details)
        card.pack(fill="both", expand=True, padx=16, pady=16)
        tk.Label(card, text="Wybierz skrzyżowanie z listy", bg=COLORS["panel"], fg=COLORS["primary_dark"], font=FONT_TITLE).pack(pady=(120, 8))
        tk.Label(card, text="Po wyborze pojawią się kluczowe statystyki, informacje tabelaryczne i wykresy.", bg=COLORS["panel"], fg=COLORS["muted"], font=("Segoe UI", 11)).pack()

    def _show_loading(self, intersection_id: int, token: int):
        self._clear_details()
        self.details_scroll.scroll_to_top()
        name = self.data_store.get_intersection_name(intersection_id)
        card = self._card(self.details)
        card.pack(fill="both", expand=True, padx=16, pady=16)
        tk.Label(card, text="Wczytywanie danych", bg=COLORS["panel"], fg=COLORS["primary_dark"], font=FONT_TITLE).pack(pady=(110, 8))
        tk.Label(card, text=name, bg=COLORS["panel"], fg=COLORS["muted"], font=("Segoe UI", 12, "bold")).pack(pady=(0, 8))
        self.loading_label = tk.Label(card, text="", bg=COLORS["panel"], fg=COLORS["primary"], font=("Segoe UI", 18, "bold"))
        self.loading_label.pack(pady=(8, 4))
        tk.Label(
            card,
            text="Możesz od razu wybrać inne skrzyżowanie — poprzednie wczytywanie zostanie pominięte.",
            bg=COLORS["panel"],
            fg=COLORS["muted"],
            font=FONT_SMALL,
        ).pack()
        self._spinner_index = 0
        self._animate_loading(token)

    def _animate_loading(self, token: int):
        if not self._is_current_token(token):
            return
        frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        try:
            self.loading_label.configure(text=frames[self._spinner_index % len(frames)])
        except Exception:
            return
        self._spinner_index += 1
        self._loading_after_id = self.after(90, lambda: self._animate_loading(token))

    def _render_intersection_shell(self, intersection_id: int, token: int):
        """Pokazuje od razu nagłówek i KPI, a resztę ładuje jako jeden blok."""
        if not self._is_current_token(token):
            return
        self._clear_details()
        self.details_scroll.scroll_to_top()
        name = self.data_store.get_intersection_name(intersection_id)
        summary = self.data_store.get_summary(intersection_id)

        header = self._card(self.details)
        header.pack(fill="x", padx=16, pady=(16, 10))
        top_row = tk.Frame(header, bg=COLORS["panel"])
        top_row.pack(fill="x", padx=18, pady=16)
        tk.Label(top_row, text=name, bg=COLORS["panel"], fg=COLORS["primary_dark"], font=FONT_TITLE).pack(side="left", anchor="w")
        tk.Label(top_row, text=f"ID: {intersection_id}", bg=COLORS["panel"], fg=COLORS["muted"], font=("Segoe UI", 11, "bold")).pack(side="right", anchor="e")

        if summary["warning"]:
            warning = tk.Frame(self.details, bg=COLORS["warning_bg"], highlightthickness=1, highlightbackground="#f1d48a")
            warning.pack(fill="x", padx=16, pady=(0, 10))
            tk.Label(
                warning,
                text="⚠ Dane natężenia ruchu wymagają ostrożnej interpretacji.",
                bg=COLORS["warning_bg"],
                fg=COLORS["warning_fg"],
                font=("Segoe UI", 10, "bold"),
            ).pack(anchor="w", padx=14, pady=(8, 0))
            tk.Label(
                warning,
                text=summary["warning"],
                bg=COLORS["warning_bg"],
                fg=COLORS["warning_fg"],
                font=FONT_SMALL,
                wraplength=950,
                justify="left",
            ).pack(anchor="w", padx=14, pady=(2, 8))

        kpi_frame = tk.Frame(self.details, bg=COLORS["bg"])
        kpi_frame.pack(fill="x", padx=16, pady=(0, 10))
        kpis = [
            ("Liczba zdarzeń", fmt_number(summary["events_count"]), f"{summary['events_level']} • zakres: {summary['year_range']}", summary["events_color"]),
            ("Śr. dobowe natężenie", f"{fmt_number(summary['avg_daily'])}", f"{summary['traffic_level']} • poj./24h", summary["traffic_color"]),
            ("Najczęstszy typ", summary["top_event_type"], "dominujący rodzaj zdarzenia", COLORS["primary_dark"]),
            ("Najczęstsze wykroczenie", summary["top_violation"], "najczęstsza przyczyna formalna", COLORS["primary_dark"]),
        ]
        for i, (label, value, hint, accent) in enumerate(kpis):
            card = self._kpi_card(kpi_frame, label, value, hint, accent)
            card.grid(row=0, column=i, sticky="nsew", padx=(0 if i == 0 else 8, 0))
            kpi_frame.grid_columnconfigure(i, weight=1)

        self.details_body = tk.Frame(self.details, bg=COLORS["bg"])
        self.details_body.pack(fill="both", expand=True, padx=16, pady=(0, 18))
        loading = self._card(self.details_body)
        loading.pack(fill="both", expand=True)
        tk.Label(
            loading,
            text="Wczytywanie szczegółów...",
            bg=COLORS["panel"],
            fg=COLORS["primary_dark"],
            font=("Segoe UI", 14, "bold"),
        ).pack(anchor="center", expand=True, padx=20, pady=70)
        self._apply_font_settings()

    def _render_intersection_body_if_current(self, intersection_id: int, token: int):
        if not self._is_current_token(token):
            return
        body = getattr(self, "details_body", None)
        if body is None or not body.winfo_exists():
            return

        # Przygotowujemy wykresy przed podmianą całej sekcji, aby użytkownik nie widział ich pojawiania się po kolei.
        group_name = self.chart_category.get()
        plot_specs = self.plotter.groups().get(group_name, [])
        prepared: list[Figure] = []
        for _title, func in plot_specs:
            try:
                prepared.append(func(intersection_id))
            except Exception as exc:
                prepared.append(self.plotter._empty_figure(f"Nie udało się utworzyć wykresu:\n{exc}"))

        if not self._is_current_token(token):
            for fig in prepared:
                plt.close(fig)
            return

        for child in body.winfo_children():
            child.destroy()

        body.grid_columnconfigure(0, weight=1, minsize=390)
        body.grid_columnconfigure(1, weight=2)

        info_col = tk.Frame(body, bg=COLORS["bg"])
        info_col.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        chart_col = tk.Frame(body, bg=COLORS["bg"])
        chart_col.grid(row=0, column=1, sticky="nsew")

        self._render_info_column(info_col, intersection_id)
        self._render_chart_column_ready(chart_col, intersection_id, prepared)
        self._apply_font_settings()

    def _render_intersection_if_current(self, intersection_id: int, token: int):
        if not self._is_current_token(token):
            return
        if self._loading_after_id:
            try:
                self.after_cancel(self._loading_after_id)
            except Exception:
                pass
            self._loading_after_id = None
        self._render_intersection(intersection_id, token)

    def _render_intersection(self, intersection_id: int, token: int):
        if not self._is_current_token(token):
            return
        self._clear_details()
        self.details_scroll.scroll_to_top()
        name = self.data_store.get_intersection_name(intersection_id)
        summary = self.data_store.get_summary(intersection_id)

        header = self._card(self.details)
        header.pack(fill="x", padx=16, pady=(16, 10))
        top_row = tk.Frame(header, bg=COLORS["panel"])
        top_row.pack(fill="x", padx=18, pady=16)
        tk.Label(top_row, text=name, bg=COLORS["panel"], fg=COLORS["primary_dark"], font=FONT_TITLE).pack(side="left", anchor="w")
        tk.Label(top_row, text=f"ID: {intersection_id}", bg=COLORS["panel"], fg=COLORS["muted"], font=("Segoe UI", 11, "bold")).pack(side="right", anchor="e")

        if summary["warning"]:
            warning = tk.Frame(self.details, bg=COLORS["warning_bg"], highlightthickness=1, highlightbackground="#f1d48a")
            warning.pack(fill="x", padx=16, pady=(0, 10))
            tk.Label(
                warning,
                text="⚠ Dane natężenia ruchu wymagają ostrożnej interpretacji.",
                bg=COLORS["warning_bg"],
                fg=COLORS["warning_fg"],
                font=("Segoe UI", 10, "bold"),
            ).pack(anchor="w", padx=14, pady=(8, 0))
            tk.Label(
                warning,
                text=summary["warning"],
                bg=COLORS["warning_bg"],
                fg=COLORS["warning_fg"],
                font=FONT_SMALL,
                wraplength=950,
                justify="left",
            ).pack(anchor="w", padx=14, pady=(2, 8))

        kpi_frame = tk.Frame(self.details, bg=COLORS["bg"])
        kpi_frame.pack(fill="x", padx=16, pady=(0, 10))
        kpis = [
            ("Liczba zdarzeń", fmt_number(summary["events_count"]), f"{summary['events_level']} • zakres: {summary['year_range']}", summary["events_color"]),
            ("Śr. dobowe natężenie", f"{fmt_number(summary['avg_daily'])}", f"{summary['traffic_level']} • poj./24h", summary["traffic_color"]),
            ("Najczęstszy typ", summary["top_event_type"], "dominujący rodzaj zdarzenia", COLORS["primary_dark"]),
            ("Najczęstsze wykroczenie", summary["top_violation"], "najczęstsza przyczyna formalna", COLORS["primary_dark"]),
        ]
        for i, (label, value, hint, accent) in enumerate(kpis):
            card = self._kpi_card(kpi_frame, label, value, hint, accent)
            card.grid(row=0, column=i, sticky="nsew", padx=(0 if i == 0 else 8, 0))
            kpi_frame.grid_columnconfigure(i, weight=1)

        body = tk.Frame(self.details, bg=COLORS["bg"])
        body.pack(fill="both", expand=True, padx=16, pady=(0, 18))
        body.grid_columnconfigure(0, weight=1, minsize=390)
        body.grid_columnconfigure(1, weight=2)

        info_col = tk.Frame(body, bg=COLORS["bg"])
        info_col.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        chart_col = tk.Frame(body, bg=COLORS["bg"])
        chart_col.grid(row=0, column=1, sticky="nsew")

        self._render_info_column(info_col, intersection_id)
        self._render_chart_column(chart_col, intersection_id, token)

    def _render_info_column(self, parent, intersection_id: int):
        traffic = self.data_store.get_traffic_row(intersection_id)
        attrs = self.data_store.get_attributes_row(intersection_id)

        basic_rows = []
        if attrs is not None:
            basic_rows = [
                ("Odległość od centrum", f"{fmt_value(attrs.get('odległość od centrum [km]'))} km"),
            ]
        if traffic is not None:
            basic_rows.append(("GPS", fmt_value(traffic.get("gps"))))
        self._info_card(parent, "Dane podstawowe", basic_rows or [("Status", "Brak danych podstawowych")], add_info_buttons=True)

        self._boolean_features_card(parent, attrs)
        self._description_card(parent, intersection_id)

        traffic_rows = []
        if traffic is not None:
            traffic_rows = [
                ("Ulica APR", fmt_value(traffic.get("ulica_apr"))),
                ("Odcinek APR", fmt_value(traffic.get("odcinek_apr"))),
                ("Punkt APR", fmt_value(traffic.get("punkt_apr"))),
                ("Okres", fmt_value(traffic.get("okres"))),
                ("Maksymalne dobowe", f"{fmt_number(traffic.get('max_dobowe'))} poj./24h"),
                ("Średnie dobowe", f"{fmt_number(traffic.get('srednie_dobowe'))} poj./24h"),
                ("Suma z okresu", f"{fmt_number(traffic.get('suma_z_okresu'))} poj."),
            ]
        self._info_card(parent, "Natężenie ruchu", traffic_rows or [("Status", "Brak danych o natężeniu")])

        infra_rows = []
        if attrs is not None:
            infra_rows = [
                ("Przejścia dla pieszych / pdp", fmt_value(attrs.get("pdp"))),
                ("Ustąp pierwszeństwa / up", fmt_value(attrs.get("up"))),
                ("Masz pierwszeństwo / mp", fmt_value(attrs.get("mp"))),
                ("Nakazy jazdy / nj", fmt_value(attrs.get("nj"))),
                ("Znaki tramwajowe", fmt_value(attrs.get("tramwaje_znak"))),
                ("Inne znaki", fmt_value(attrs.get("inne"))),
                ("STOP", fmt_value(attrs.get("stop"))),
                ("Zakaz skrętu/zawracania", fmt_value(attrs.get("zakaz s/z"))),
            ]
        self._info_card(parent, "Infrastruktura i oznakowanie", infra_rows or [("Status", "Brak danych infrastrukturalnych")], add_info_buttons=True)

    def _boolean_features_card(self, parent, attrs: Optional[pd.Series]):
        card = self._card(parent)
        card.pack(fill="x", pady=(0, 10))
        tk.Label(card, text="Szybka klasyfikacja", bg=COLORS["panel"], fg=COLORS["primary_dark"], font=FONT_H2).pack(anchor="w", padx=14, pady=(12, 6))
        body = tk.Frame(card, bg=COLORS["panel"])
        body.pack(fill="x", padx=12, pady=(0, 12))

        if attrs is None:
            tk.Label(body, text="Brak danych atrybutowych", bg=COLORS["panel"], fg=COLORS["muted"], font=FONT_SMALL).pack(anchor="w")
            return

        items = [
            ("Ścieżka rowerowa", attrs.get("ścieżka rowerowa"), "sciezka_rowerowa"),
            ("Tramwaj", attrs.get("tramwaj"), "tramwaje_lz"),
            ("Rondo", attrs.get("rondo"), "rondo_lz"),
        ]
        for label, raw_value, feature_key in items:
            value = fmt_presence_bool(raw_value)
            low = value.lower()
            if low == "tak":
                pill_bg, pill_fg = "#e8f5e9", COLORS["primary_dark"]
            elif low == "nie":
                pill_bg, pill_fg = "#fdecec", COLORS["danger"]
            else:
                pill_bg, pill_fg = COLORS["panel_alt"], COLORS["muted"]

            row = tk.Frame(body, bg=COLORS["panel_alt"], highlightthickness=1, highlightbackground=COLORS["border"])
            row.pack(fill="x", pady=3)
            tk.Label(row, text=label, bg=COLORS["panel_alt"], fg=COLORS["text"], font=FONT_SMALL).pack(side="left", fill="x", expand=True, anchor="w", padx=(10, 6), pady=7)
            value_box = tk.Label(row, text=value.upper(), bg=pill_bg, fg=pill_fg, font=("Segoe UI", 9, "bold"), padx=10, pady=3)
            value_box.pack(side="right", padx=(4, 8))
            btn = tk.Button(row, text="ⓘ", bg=COLORS["panel_alt"], fg=COLORS["primary_dark"], relief="flat", cursor="hand2", command=lambda f=feature_key, k=label: self._show_feature_interpretation(k, f))
            btn.pack(side="right", padx=(0, 4))
            ToolTip(btn, "Pokaż interpretację modelową tej cechy")

    def _description_card(self, parent, intersection_id: int):
        card = self._card(parent)
        card.pack(fill="x", pady=(0, 10))
        tk.Label(card, text="Opis analityczny", bg=COLORS["panel"], fg=COLORS["primary_dark"], font=FONT_H2).pack(anchor="w", padx=14, pady=(12, 6))
        text = self.data_store.get_intersection_description(intersection_id)
        tk.Label(
            card,
            text=text,
            bg=COLORS["panel"],
            fg=COLORS["text"],
            font=FONT_NORMAL,
            wraplength=360,
            justify="left",
        ).pack(anchor="w", fill="x", padx=14, pady=(0, 14))

    def _render_chart_column_ready(self, parent, intersection_id: int, prepared_figures: list[Figure]):
        card = self._card(parent)
        card.pack(fill="both", expand=True)

        top = tk.Frame(card, bg=COLORS["panel"])
        top.pack(fill="x", padx=16, pady=(14, 8))
        tk.Label(top, text="Wykresy", bg=COLORS["panel"], fg=COLORS["primary_dark"], font=FONT_H2).pack(side="left")

        groups = self.plotter.groups()
        if self.chart_category.get() not in groups:
            self.chart_category.set("Ogólne zdarzenia")
        combo = ttk.Combobox(top, textvariable=self.chart_category, values=list(groups.keys()), state="readonly", width=30)
        combo.pack(side="right")
        combo.bind("<<ComboboxSelected>>", lambda _e: self._request_chart_update(intersection_id))
        ToolTip(combo, "Wybierz kategorię wykresów. Ładowane są tylko wykresy z wybranej kategorii.")

        chart_area = tk.Frame(card, bg=COLORS["panel"])
        chart_area.pack(fill="both", expand=True, padx=12, pady=(0, 12))
        self._active_chart_area = chart_area
        self._destroy_plot_canvases()
        self._place_prepared_charts(chart_area, prepared_figures)
        self._apply_font_settings()

    def _place_prepared_charts(self, chart_area: tk.Frame, prepared_figures: list[Figure]):
        for child in chart_area.winfo_children():
            child.destroy()
        if not prepared_figures:
            empty = tk.Frame(chart_area, bg=COLORS["panel_alt"], highlightthickness=1, highlightbackground=COLORS["border"])
            empty.pack(fill="both", expand=True, padx=4, pady=6)
            tk.Label(empty, text="Brak wykresów dla tej kategorii.", bg=COLORS["panel_alt"], fg=COLORS["muted"], font=FONT_NORMAL).pack(padx=14, pady=20)
            return
        for fig in prepared_figures:
            plot_frame = tk.Frame(chart_area, bg=COLORS["panel_alt"], highlightthickness=1, highlightbackground=COLORS["border"])
            plot_frame.pack(fill="both", expand=True, padx=4, pady=6)
            canvas = FigureCanvasTkAgg(fig, master=plot_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(fill="both", expand=True, padx=6, pady=6)
            self.current_plot_canvases.append(canvas)

    def _render_chart_column(self, parent, intersection_id: int, token: int):
        card = self._card(parent)
        card.pack(fill="both", expand=True)

        top = tk.Frame(card, bg=COLORS["panel"])
        top.pack(fill="x", padx=16, pady=(14, 8))
        tk.Label(top, text="Wykresy", bg=COLORS["panel"], fg=COLORS["primary_dark"], font=FONT_H2).pack(side="left")

        groups = self.plotter.groups()
        if self.chart_category.get() not in groups:
            self.chart_category.set("Ogólne zdarzenia")
        combo = ttk.Combobox(top, textvariable=self.chart_category, values=list(groups.keys()), state="readonly", width=30)
        combo.pack(side="right")
        combo.bind("<<ComboboxSelected>>", lambda _e: self._request_chart_update(intersection_id))
        ToolTip(combo, "Wybierz kategorię wykresów. Ładowane są tylko wykresy z wybranej kategorii.")

        chart_area = tk.Frame(card, bg=COLORS["panel"])
        chart_area.pack(fill="both", expand=True, padx=12, pady=(0, 12))
        self._active_chart_area = chart_area
        self._active_chart_token += 1
        chart_token = self._active_chart_token
        self._start_chart_loading(chart_area, intersection_id, token, chart_token)

    def _request_chart_update(self, intersection_id: int):
        if self._active_chart_area is None:
            return
        self._active_chart_token += 1
        self._cancel_chart_jobs_only()
        chart_token = self._active_chart_token
        self._start_chart_loading(self._active_chart_area, intersection_id, self._load_token, chart_token)

    def _cancel_chart_jobs_only(self):
        for after_id in self._pending_after_ids:
            try:
                self.after_cancel(after_id)
            except Exception:
                pass
        self._pending_after_ids.clear()

    def _start_chart_loading(self, chart_area: tk.Frame, intersection_id: int, selection_token: int, chart_token: int):
        if not self._is_current_token(selection_token) or chart_token != self._active_chart_token:
            return
        for child in chart_area.winfo_children():
            child.destroy()
        self._destroy_plot_canvases()

        loading = tk.Frame(chart_area, bg=COLORS["panel_alt"], highlightthickness=1, highlightbackground=COLORS["border"])
        loading.pack(fill="both", expand=True, padx=4, pady=6)
        tk.Label(
            loading,
            text="Wczytywanie wykresów...",
            bg=COLORS["panel_alt"],
            fg=COLORS["primary_dark"],
            font=("Segoe UI", 12, "bold"),
        ).pack(anchor="center", expand=True, padx=14, pady=40)

        group_name = self.chart_category.get()
        plot_specs = self.plotter.groups().get(group_name, [])
        self._schedule(lambda: self._render_all_charts(chart_area, intersection_id, plot_specs, selection_token, chart_token), delay=40)

    def _render_all_charts(
        self,
        chart_area: tk.Frame,
        intersection_id: int,
        plot_specs: list[tuple[str, Callable[[int], Figure]]],
        selection_token: int,
        chart_token: int,
    ):
        """Renderuje komplet wykresów w pamięci, a dopiero potem podmienia cały obszar wykresów."""
        if not self._is_current_token(selection_token) or chart_token != self._active_chart_token:
            return

        prepared: list[Figure] = []
        for _title, func in plot_specs:
            try:
                fig = func(intersection_id)
            except Exception as exc:
                fig = self.plotter._empty_figure(f"Nie udało się utworzyć wykresu:\n{exc}")
            prepared.append(fig)

        if not self._is_current_token(selection_token) or chart_token != self._active_chart_token:
            for fig in prepared:
                plt.close(fig)
            return

        for child in chart_area.winfo_children():
            child.destroy()
        self._destroy_plot_canvases()

        if not prepared:
            empty = tk.Frame(chart_area, bg=COLORS["panel_alt"], highlightthickness=1, highlightbackground=COLORS["border"])
            empty.pack(fill="both", expand=True, padx=4, pady=6)
            tk.Label(empty, text="Brak wykresów dla tej kategorii.", bg=COLORS["panel_alt"], fg=COLORS["muted"], font=FONT_NORMAL).pack(padx=14, pady=20)
            return

        for fig in prepared:
            if not self._is_current_token(selection_token) or chart_token != self._active_chart_token:
                plt.close(fig)
                continue
            plot_frame = tk.Frame(chart_area, bg=COLORS["panel_alt"], highlightthickness=1, highlightbackground=COLORS["border"])
            plot_frame.pack(fill="both", expand=True, padx=4, pady=6)
            canvas = FigureCanvasTkAgg(fig, master=plot_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(fill="both", expand=True, padx=6, pady=6)
            self.current_plot_canvases.append(canvas)
        self._apply_font_settings()

    # KARTY I TABELKI

    def _card(self, parent) -> tk.Frame:
        return tk.Frame(parent, bg=COLORS["panel"], highlightthickness=1, highlightbackground=COLORS["border"])

    def _kpi_card(self, parent, label: str, value: str, hint: str, accent: str = COLORS["primary_dark"]) -> tk.Frame:
        card = tk.Frame(parent, bg=COLORS["panel"], highlightthickness=1, highlightbackground=COLORS["border"], padx=0, pady=0)
        accent_bar = tk.Frame(card, bg=accent, width=6)
        accent_bar.pack(side="left", fill="y")
        inner = tk.Frame(card, bg=COLORS["panel"], padx=12, pady=10)
        inner.pack(side="left", fill="both", expand=True)
        tk.Label(inner, text=label, bg=COLORS["panel"], fg=COLORS["muted"], font=FONT_KPI_LABEL).pack(anchor="w")
        tk.Label(inner, text=value, bg=COLORS["panel"], fg=accent, font=FONT_KPI_VALUE, wraplength=245, justify="left").pack(anchor="w", pady=(4, 2))
        tk.Label(inner, text=hint, bg=COLORS["panel"], fg=COLORS["muted"], font=FONT_SMALL, wraplength=245, justify="left").pack(anchor="w")
        return card

    def _info_card(self, parent, title: str, rows: list[tuple[str, str]], add_info_buttons: bool = False):
        card = self._card(parent)
        card.pack(fill="x", pady=(0, 10))
        tk.Label(card, text=title, bg=COLORS["panel"], fg=COLORS["primary_dark"], font=FONT_H2).pack(anchor="w", padx=14, pady=(12, 6))

        table = tk.Frame(card, bg=COLORS["panel"])
        table.pack(fill="x", padx=12, pady=(0, 12))

        feature_map = {
            "Ścieżka rowerowa": "sciezka_rowerowa",
            "Rondo": "rondo_lz",
            "STOP": "stop_lz",
            "Zakaz skrętu/zawracania": "zakaz_skretu/zawracania_lz",
            "Znaki tramwajowe": "tramwaje_lz",
            "Przejścia dla pieszych / pdp": "przejscie_dla_pieszych_lz",
            "Odległość od centrum": "odległosc_od_centrum [km]",
        }

        for i, (key, value) in enumerate(rows):
            bg = COLORS["panel"] if i % 2 == 0 else COLORS["panel_alt"]
            row = tk.Frame(table, bg=bg)
            row.pack(fill="x")
            left = tk.Label(row, text=key, bg=bg, fg=COLORS["muted"], font=FONT_SMALL, anchor="w", width=28)
            left.pack(side="left", fill="x", padx=(8, 4), pady=5)
            right = tk.Label(row, text=value, bg=bg, fg=COLORS["text"], font=FONT_SMALL, anchor="w", justify="left", wraplength=290)
            right.pack(side="left", fill="x", expand=True, padx=(4, 8), pady=5)

            if add_info_buttons and key in feature_map:
                btn = tk.Button(
                    row,
                    text="ⓘ",
                    bg=bg,
                    fg=COLORS["primary_dark"],
                    relief="flat",
                    cursor="hand2",
                    command=lambda f=feature_map[key], k=key: self._show_feature_interpretation(k, f),
                )
                btn.pack(side="right", padx=(0, 8))
                ToolTip(btn, "Pokaż interpretację modelową tej cechy")

    def _show_feature_interpretation(self, display_name: str, feature_key: str):
        text = self.data_store.get_interpretation(feature_key)
        win = tk.Toplevel(self)
        win.title(f"Interpretacja: {display_name}")
        win.geometry("720x480")
        win.configure(bg=COLORS["bg"])
        tk.Label(win, text=display_name, bg=COLORS["bg"], fg=COLORS["primary_dark"], font=FONT_H2).pack(anchor="w", padx=18, pady=(16, 8))
        text_widget = tk.Text(win, wrap="word", font=FONT_NORMAL, bg=COLORS["panel"], fg=COLORS["text"], relief="flat", padx=12, pady=12)
        text_widget.pack(fill="both", expand=True, padx=18, pady=(0, 18))
        text_widget.insert("1.0", text)
        text_widget.configure(state="disabled")

    def _cancel_all_after_callbacks(self):
        """Anuluje zaplanowane callbacki Tkintera przed zamknięciem aplikacji."""
        try:
            after_ids = self.tk.call("after", "info")
        except Exception:
            return
        for after_id in after_ids:
            try:
                self.after_cancel(after_id)
            except Exception:
                pass

    def _on_close(self):
        """Zamyka aplikację tak, aby proces Pythona nie blokował dalej konsoli."""
        """To był głupi błąd, który wyskoczył dopiero po jakimś czasie. Teraz działa elegancko"""
        if getattr(self, "_closing", False):
            return
        self._closing = True

        try:
            self._save_user_settings()
        except Exception:
            pass

        try:
            self._load_token += 1
            self._active_chart_token += 1
        except Exception:
            pass

        try:
            self._cancel_pending_jobs()
        except Exception:
            pass
        try:
            self._cancel_all_after_callbacks()
        except Exception:
            pass
        try:
            self._destroy_plot_canvases()
        except Exception:
            pass
        try:
            plt.close("all")
        except Exception:
            pass

        try:
            for child in list(self.winfo_children()):
                try:
                    child.destroy()
                except Exception:
                    pass
        except Exception:
            pass

        try:
            self.quit()
        except Exception:
            pass
        try:
            self.destroy()
        except Exception:
            pass

# START APLIKACJI
def main():
    script_dir = Path(__file__).resolve().parent
    app = IntersectionApp(base_dir=script_dir)
    app.mainloop()

if __name__ == "__main__":
    main()