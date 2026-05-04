import requests
import time

url_mapy = "https://sewik.pl/api/hybrid-map"
wszystkie_id = set()

START_LAT = 52.08
STOP_LAT = 52.36
START_LON = 20.80
STOP_LON = 21.32
KROK = 0.04

filtry = {
    "fromDate": "2025-01-01", 
    "ilePojazdow[]": "co-najmniej-jeden",
    "rodzajSkrzyzowania": "dowolne",  # <--- TO JEST TA DOPISANA LINIA
    "miejscowosc": "Warszawa"         # Możesz też dodać miejscowość, jeśli chcesz zawęzić skan
}

headers_api = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Firefox/150.0",
    "Accept": "*/*",
    "Referer": "https://sewik.pl/szukaj",
    "Origin": "https://sewik.pl"
}

# --- NOWE USTAWIENIA DLA MECHANIZMU PONAWIANIA ---
MAKSYMALNA_LICZBA_PROB = 3  # Ile razy skrypt ma próbować, zanim się podda
CZAS_CZEKANIA_PO_BLEDZIE = 3 # Ile sekund czekać przed kolejną próbą (warto dać serwerowi chwilę na oddech)

print("🗺️ Rozpoczynam skanowanie aglomeracji z systemem automatycznego ponawiania...")
start_time = time.time()

aktualny_min_lat = START_LAT
licznik_kwadratow = 1

while aktualny_min_lat < STOP_LAT:
    aktualny_max_lat = aktualny_min_lat + KROK
    aktualny_min_lon = START_LON
    
    while aktualny_min_lon < STOP_LON:
        aktualny_max_lon = aktualny_min_lon + KROK
        
        parametry = {
            "minLat": str(aktualny_min_lat),
            "maxLat": str(aktualny_max_lat),
            "minLon": str(aktualny_min_lon),
            "maxLon": str(aktualny_max_lon),
            "resolution": "0.0001220703125",
            "threshold": "5000"
        }
        
        # --- BLOK PONAWIANIA (RETRY PATTERN) ---
        sukces = False
        
        for proba in range(1, MAKSYMALNA_LICZBA_PROB + 1):
            try:
                res = requests.post(url_mapy, headers=headers_api, params=parametry, data=filtry, timeout=10)
                
                if res.status_code == 200:
                    punkty = [e["id"] for e in res.json() if e.get("type") == "point"]
                    wszystkie_id.update(punkty)
                    print(f"[{licznik_kwadratow:02d}/91] Kwadrat Lat {aktualny_min_lat:.2f}, Lon {aktualny_min_lon:.2f} -> Znaleziono: {len(punkty)} wypadków")
                    
                    sukces = True # Zaznaczamy, że się udało
                    break         # Przerywamy pętlę prób (bo po co próbować dalej, skoro mamy dane!)
                    
                else:
                    print(f"[{licznik_kwadratow:02d}/91] ⚠️ Błąd serwera (Kod: {res.status_code}). Próba {proba}/{MAKSYMALNA_LICZBA_PROB}...")
                    
            except requests.exceptions.Timeout:
                 print(f"[{licznik_kwadratow:02d}/91] 🕒 Serwer nie odpowiada (Timeout). Próba {proba}/{MAKSYMALNA_LICZBA_PROB}...")
            except Exception as e:
                print(f"[{licznik_kwadratow:02d}/91] ❌ Inny błąd połączenia. Próba {proba}/{MAKSYMALNA_LICZBA_PROB}...")

            # Jeśli to nie była ostatnia próba i nie było sukcesu, poczekaj przed kolejnym uderzeniem
            if not sukces and proba < MAKSYMALNA_LICZBA_PROB:
                time.sleep(CZAS_CZEKANIA_PO_BLEDZIE)
                
        # Co się dzieje, jeśli wyczerpaliśmy wszystkie próby i nadal jest błąd?
        if not sukces:
            print(f"[{licznik_kwadratow:02d}/91] ☠️ Kwadrat całkowicie pominięty po {MAKSYMALNA_LICZBA_PROB} próbach.")
        # ----------------------------------------
            
        licznik_kwadratow += 1
        aktualny_min_lon += KROK
        
        time.sleep(1) # Standardowa przerwa między kwadratami (żeby nie wywołać błędów)
        
    aktualny_min_lat += KROK

czas_trwania = round(time.time() - start_time)
print(f"\n✅ SKANOWANIE ZAKOŃCZONE! Czas operacji: {czas_trwania} sekund.")
print(f"🎯 Zebrano łącznie {len(wszystkie_id)} unikalnych identyfikatorów wypadków.")

nazwa_pliku = "warszawa_wypadki_id.txt"
with open(nazwa_pliku, "w") as f:
    for id_zdarzenia in wszystkie_id:
        f.write(f"{id_zdarzenia}\n")
        
print(f"💾 Wszystkie ID zostały bezpiecznie zapisane do pliku: {nazwa_pliku}")