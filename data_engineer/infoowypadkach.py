import pandas as pd
import aiohttp
import asyncio
from bs4 import BeautifulSoup

INPUT_FILE = r"C:\Users\magda\Downloads\warszawa_wypadki_id_do_2025.csv"
OUTPUT_FILE = r"C:\Users\magda\Downloads\infowypadki.csv"

df = pd.read_csv(INPUT_FILE)

ID_COLUMN = df.columns[0]

headers = {
    "User-Agent": "Mozilla/5.0"
}

semaphore = asyncio.Semaphore(50)

FIELDS = {
    "Data:": "data",
    "Adres:": "adres",
    "Sygnalizacja świetlna:": "sygnalizacja",
    "Rodzaj zdarzenia": "rodzaj_zdarzenia",
    "Warunki oświetleniowe:": "warunki_oswietleniowe",
    "Warunki pogodowe:": "warunki_pogodowe",
    "Rodzaj drogi:": "rodzaj_drogi",
    "Ograniczenie prędkości:": "ograniczenie_predkosci",
    "Typ nawierzchni:": "typ_nawierzchni",
    "Stan nawierzchni:": "stan_nawierzchni",
    "Oznakowanie poziome:": "oznakowanie_poziome",
    "Rodzaj skrzyżowania:": "rodzaj_skrzyzowania",
    "Teren zabudowany:": "teren_zabudowany"
}


def extract_field(text, label):
    lines = text.split("\n")

    for i, line in enumerate(lines):
        line = line.strip()

        if label in line:
            # wartość w tej samej linii
            value = line.replace(label, "").strip()
            if value:
                return value

            # wartość w kolejnej linii
            for j in range(i + 1, len(lines)):
                next_line = lines[j].strip()

                if next_line:
                    return next_line

    return None


async def scrape_event(session, event_id):
    url = f"https://sewik.pl/zdarzenie/{event_id}"

    async with semaphore:
        try:
            async with session.get(url, timeout=15) as response:
                html = await response.text()

                soup = BeautifulSoup(html, "html.parser")
                text = soup.get_text("\n", strip=True)

                result = {"id": event_id}

                for label, column_name in FIELDS.items():
                    result[column_name] = extract_field(text, label)

                print(f"Gotowe: {event_id}")
                return result

        except Exception as e:
            print(f"Błąd {event_id}: {e}")
            return {"id": event_id}


async def main():
    connector = aiohttp.TCPConnector(limit=50)

    async with aiohttp.ClientSession(
        connector=connector,
        headers=headers
    ) as session:

        tasks = [
            scrape_event(session, event_id)
            for event_id in df[ID_COLUMN]
        ]

        results = await asyncio.gather(*tasks)

        result_df = pd.DataFrame(results)
        result_df.to_csv(OUTPUT_FILE, index=False)

        print(f"Gotowe! Zapisano do: {OUTPUT_FILE}")


asyncio.run(main())