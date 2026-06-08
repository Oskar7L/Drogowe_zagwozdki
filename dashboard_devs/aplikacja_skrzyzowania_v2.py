"""
Druga wersja aplikacji okienkowej do przeglądania danych o skrzyżowaniach.

Najważniejsze zmiany względem v1:
- własny pasek zakładek zamiast domyślnego ttk.Notebook,
- stabilniejsza obsługa wyboru skrzyżowania,
- bufor ładowania z animacją,
- anulowanie oczekujących operacji przy szybkim klikaniu między skrzyżowaniami,
- uzupełniona zakładka Home,
- nadal działają: lista skrzyżowań, KPI, dane tabelaryczne, wykresy i interpretacje cech.

Wymagane pliki w tym samym folderze co skrypt, albo w podfolderze "data":
- wyczyszczone_dane.csv
- uzupelnione_natezenie.csv
- atrybuty skrzyzowan.csv
- OR_interpretacje.csv  (opcjonalnie)
- opis_*.md             (opcjonalnie, używane informacyjnie w Home)

Wymagane biblioteki:
    pip install pandas matplotlib

Uruchomienie:
    python aplikacja_skrzyzowania_v2.py
"""

from __future__ import annotations

import sys
import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path
from typing import Callable, Optional

import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


# KONFIGURACJA WYGLĄDU

COLORS = {
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
        self._mouse_inside = False

        self.content.bind(
            "<Configure>",
            lambda _e: self.canvas.configure(scrollregion=self.canvas.bbox("all")),
        )
        self.window_id = self.canvas.create_window((0, 0), window=self.content, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")
        self.canvas.bind("<Configure>", self._on_canvas_configure)
        self.canvas.bind("<Enter>", lambda _e: setattr(self, "_mouse_inside", True))
        self.canvas.bind("<Leave>", lambda _e: setattr(self, "_mouse_inside", False))
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

    def _on_canvas_configure(self, event):
        self.canvas.itemconfig(self.window_id, width=event.width)

    def _on_mousewheel(self, event):
        if not self._mouse_inside:
            return
        try:
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
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
        self.intersections = self._build_intersections()
        self.events_by_id = {
            int(k): v.copy()
            for k, v in self.events.dropna(subset=["id_skrzyzowania"]).groupby("id_skrzyzowania")
        }
        self.summary_cache: dict[int, dict] = {}
        self.md_files = self._find_markdown_files()

    def _find_file(self, filename: str) -> Path:
        candidates = [
            self.base_dir / filename,
            self.base_dir / "data" / filename,
            self.base_dir / "Dane" / filename,
            self.base_dir / "Dane_wykresy" / filename,
            Path.cwd() / filename,
            Path.cwd() / "data" / filename,
            Path.cwd() / "Dane" / filename,
            Path.cwd() / "Dane_wykresy" / filename,
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
        summary = {
            "events_count": len(events),
            "year_range": year_range,
            "avg_daily": None if traffic is None else traffic.get("srednie_dobowe"),
            "max_daily": None if traffic is None else traffic.get("max_dobowe"),
            "top_event_type": safe_mode(events["rodzaj_zdarzenia"]) if not events.empty else "brak danych",
            "top_violation": safe_mode(events["wykroczenie"]) if not events.empty else "brak danych",
            "warning": "" if traffic is None or pd.isna(traffic.get("uwaga")) else str(traffic.get("uwaga")),
        }
        self.summary_cache[intersection_id] = summary
        return summary

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
    def __init__(self, data: DataStore):
        super().__init__()
        self.data_store = data
        self.plotter = IntersectionPlots(data)
        self.current_id: Optional[int] = None
        self.current_plot_canvases: list[FigureCanvasTkAgg] = []
        self.all_intersections = self.data_store.get_intersections()

        self._active_tab = "Home"
        self._tab_buttons: dict[str, tk.Button] = {}
        self._tab_frames: dict[str, tk.Frame] = {}

        self._load_token = 0
        self._spinner_index = 0
        self._loading_after_id: Optional[str] = None
        self._pending_after_ids: list[str] = []
        self.chart_category = tk.StringVar(value="Ogólne zdarzenia")
        self._active_chart_area: Optional[tk.Frame] = None
        self._active_chart_token = 0

        self.title("Dashboard skrzyżowań drogowych")
        self.geometry("1450x900")
        self.minsize(1150, 720)
        self.configure(bg=COLORS["bg"])

        self._setup_style()
        self._build_layout()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

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
        shell.pack(fill="both", expand=True, padx=12, pady=12)

        self._build_top_nav(shell)

        self.content_container = tk.Frame(shell, bg=COLORS["bg"])
        self.content_container.pack(fill="both", expand=True, pady=(10, 0))

        for tab_name in ["Home", "Skrzyżowania", "Statystyki"]:
            frame = tk.Frame(self.content_container, bg=COLORS["bg"])
            frame.grid(row=0, column=0, sticky="nsew")
            self._tab_frames[tab_name] = frame
        self.content_container.grid_rowconfigure(0, weight=1)
        self.content_container.grid_columnconfigure(0, weight=1)

        self._build_home_tab(self._tab_frames["Home"])
        self._build_intersections_tab(self._tab_frames["Skrzyżowania"])
        self._build_placeholder(
            self._tab_frames["Statystyki"],
            "Statystyki",
            "Sekcja statystyk i opisów wykresów zostanie uzupełniona w kolejnej wersji aplikacji.",
        )

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

        for tab_name in ["Home", "Skrzyżowania", "Statystyki"]:
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
                    activebackground="#dce8df",
                    activeforeground=COLORS["text"],
                    font=("Segoe UI", 10),
                )

    def _build_placeholder(self, parent, title: str, subtitle: str):
        card = self._card(parent)
        card.pack(fill="both", expand=True, padx=24, pady=24)
        tk.Label(card, text=title, bg=COLORS["panel"], fg=COLORS["primary_dark"], font=FONT_TITLE).pack(pady=(80, 10))
        tk.Label(card, text=subtitle, bg=COLORS["panel"], fg=COLORS["muted"], font=("Segoe UI", 12)).pack()

    # -------------------------------------------------------------------------
    # HOME
    # -------------------------------------------------------------------------

    def _build_home_tab(self, parent):
        scroll = ScrollableFrame(parent)
        scroll.pack(fill="both", expand=True)
        root = scroll.content

        hero = self._card(root)
        hero.pack(fill="x", padx=24, pady=(24, 14))
        tk.Label(
            hero,
            text="Aplikacja do przeglądania i interpretacji danych o skrzyżowaniach",
            bg=COLORS["panel"],
            fg=COLORS["primary_dark"],
            font=FONT_H1,
            wraplength=1050,
            justify="left",
        ).pack(anchor="w", padx=24, pady=(22, 8))
        tk.Label(
            hero,
            text=(
                "Projekt integruje dane o zdarzeniach drogowych, natężeniu ruchu oraz cechach infrastrukturalnych "
                "skrzyżowań. Celem aplikacji jest szybkie porównywanie skrzyżowań, przeglądanie ich profilu "
                "i przygotowanie podstawy pod dalszą analizę statystyczną."
            ),
            bg=COLORS["panel"],
            fg=COLORS["text"],
            font=("Segoe UI", 11),
            wraplength=1100,
            justify="left",
        ).pack(anchor="w", padx=24, pady=(0, 22))

        grid = tk.Frame(root, bg=COLORS["bg"])
        grid.pack(fill="x", padx=24, pady=(0, 14))
        grid.grid_columnconfigure(0, weight=1)
        grid.grid_columnconfigure(1, weight=1)

        self._home_card(
            grid,
            "Jak korzystać z aplikacji?",
            [
                "Przejdź do zakładki „Skrzyżowania” i wybierz pozycję z listy po lewej stronie.",
                "Po kliknięciu aplikacja wczyta profil skrzyżowania: KPI, dane tabelaryczne i wykresy.",
                "Kategorie wykresów można zmieniać z listy rozwijanej po prawej stronie.",
                "Przy wybranych atrybutach infrastrukturalnych dostępna jest ikona ⓘ z interpretacją modelową.",
            ],
            row=0,
            col=0,
        )
        self._home_card(
            grid,
            "Zakres danych",
            [
                "Zdarzenia drogowe: pełna lista zdarzeń przypisana do ID skrzyżowania.",
                "Natężenie ruchu: wartości średnie, maksymalne i suma z okresu pomiarowego.",
                "Atrybuty skrzyżowań: cechy infrastruktury, oznakowania i odległość od centrum.",
                "Interpretacje OR: eksperckie objaśnienia wybranych cech używane jako pomoc kontekstowa.",
            ],
            row=0,
            col=1,
        )

        explanations = self._card(root)
        explanations.pack(fill="x", padx=24, pady=(0, 24))
        tk.Label(
            explanations,
            text="Wyjaśnienia wykresów i interpretacje",
            bg=COLORS["panel"],
            fg=COLORS["primary_dark"],
            font=FONT_H2,
        ).pack(anchor="w", padx=18, pady=(16, 6))

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

    # -------------------------------------------------------------------------
    # ZAKŁADKA SKRZYŻOWANIA
    # -------------------------------------------------------------------------

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
            bg="#fbfdfc",
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
        self._show_loading(intersection_id, token)
        # Krótka zwłoka działa jak debounce: szybkie kliknięcia nie uruchamiają kilku renderów po kolei.
        self._schedule(lambda: self._render_intersection_if_current(intersection_id, token), delay=180)

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
            ("Liczba zdarzeń", fmt_number(summary["events_count"]), f"Zakres danych: {summary['year_range']}"),
            ("Śr. dobowe natężenie", f"{fmt_number(summary['avg_daily'])}", "pojazdów / 24h"),
            ("Najczęstszy typ", summary["top_event_type"], "rodzaj zdarzenia"),
            ("Najczęstsze wykroczenie", summary["top_violation"], "wg liczby zdarzeń"),
        ]
        for i, (label, value, hint) in enumerate(kpis):
            card = self._kpi_card(kpi_frame, label, value, hint)
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
                ("Ścieżka rowerowa", fmt_bool_like(attrs.get("ścieżka rowerowa"))),
                ("Tramwaj", fmt_bool_like(attrs.get("tramwaj"))),
                ("Rondo", fmt_bool_like(attrs.get("rondo"))),
            ]
        self._info_card(parent, "Dane podstawowe", basic_rows or [("Status", "Brak danych atrybutowych")], add_info_buttons=True)

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
                ("GPS", fmt_value(traffic.get("gps"))),
            ]
        self._info_card(parent, "Natężenie ruchu", traffic_rows or [("Status", "Brak danych o natężeniu")])

        infra_rows = []
        if attrs is not None:
            infra_rows = [
                ("Suma atrybutów", fmt_value(attrs.get("suma"))),
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
        loading.pack(fill="x", padx=4, pady=6)
        tk.Label(
            loading,
            text="Przygotowywanie wykresów...",
            bg=COLORS["panel_alt"],
            fg=COLORS["muted"],
            font=FONT_NORMAL,
        ).pack(anchor="w", padx=14, pady=14)

        group_name = self.chart_category.get()
        plot_specs = self.plotter.groups().get(group_name, [])
        self._schedule(lambda: self._render_next_chart(chart_area, intersection_id, plot_specs, 0, selection_token, chart_token), delay=40)

    def _render_next_chart(
        self,
        chart_area: tk.Frame,
        intersection_id: int,
        plot_specs: list[tuple[str, Callable[[int], Figure]]],
        index: int,
        selection_token: int,
        chart_token: int,
    ):
        if not self._is_current_token(selection_token) or chart_token != self._active_chart_token:
            return
        if index == 0:
            for child in chart_area.winfo_children():
                child.destroy()
        if index >= len(plot_specs):
            return

        _title, func = plot_specs[index]
        plot_frame = tk.Frame(chart_area, bg=COLORS["panel_alt"], highlightthickness=1, highlightbackground=COLORS["border"])
        plot_frame.pack(fill="both", expand=True, padx=4, pady=6)
        try:
            fig = func(intersection_id)
        except Exception as exc:
            fig = self.plotter._empty_figure(f"Nie udało się utworzyć wykresu:\n{exc}")
        if not self._is_current_token(selection_token) or chart_token != self._active_chart_token:
            plt.close(fig)
            return
        canvas = FigureCanvasTkAgg(fig, master=plot_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=6, pady=6)
        self.current_plot_canvases.append(canvas)

        self._schedule(
            lambda: self._render_next_chart(chart_area, intersection_id, plot_specs, index + 1, selection_token, chart_token),
            delay=20,
        )

    # -------------------------------------------------------------------------
    # KARTY I TABELKI
    # -------------------------------------------------------------------------

    def _card(self, parent) -> tk.Frame:
        return tk.Frame(parent, bg=COLORS["panel"], highlightthickness=1, highlightbackground=COLORS["border"])

    def _kpi_card(self, parent, label: str, value: str, hint: str) -> tk.Frame:
        card = tk.Frame(parent, bg=COLORS["panel"], highlightthickness=1, highlightbackground=COLORS["border"], padx=12, pady=10)
        tk.Label(card, text=label, bg=COLORS["panel"], fg=COLORS["muted"], font=FONT_KPI_LABEL).pack(anchor="w")
        tk.Label(card, text=value, bg=COLORS["panel"], fg=COLORS["primary_dark"], font=FONT_KPI_VALUE, wraplength=245, justify="left").pack(anchor="w", pady=(4, 2))
        tk.Label(card, text=hint, bg=COLORS["panel"], fg=COLORS["muted"], font=FONT_SMALL, wraplength=245, justify="left").pack(anchor="w")
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

    def _on_close(self):
        self._load_token += 1
        self._active_chart_token += 1
        self._cancel_pending_jobs()
        self._destroy_plot_canvases()
        self.destroy()



# START APLIKACJI



def main():
    script_dir = Path(__file__).resolve().parent
    try:
        data = DataStore(script_dir)
    except Exception as exc:
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("Błąd wczytywania danych", str(exc))
        root.destroy()
        sys.exit(1)

    app = IntersectionApp(data)
    app.mainloop()


if __name__ == "__main__":
    main()
