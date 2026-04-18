# Drogowe Zagwozdki 🚦

Projekt analityczny dotyczący zagadnień drogowych. Repozytorium podzielone jest według ról zespołowych, co ułatwia współpracę i zarządzanie kodem.

## Struktura projektu

| Folder | Rola | Opis |
|---|---|---|
| [`data_engineer/`](./data_engineer/) | Data Engineer | Pipeline'y danych, ETL, bazy danych |
| [`data_scientist/`](./data_scientist/) | Data Scientist | Modele ML, eksperymenty, notebooki |
| [`data_analyst/`](./data_analyst/) | Data Analyst | Raporty, zapytania SQL, wizualizacje |
| [`dashboard_devs/`](./dashboard_devs/) | Dashboard Developer | Aplikacje dashboardowe, UX/UI |

## Jak zacząć?

1. Sklonuj repozytorium:
   ```bash
   git clone https://github.com/Oskar7L/Drogowe_zagwozdki.git
   ```
2. Przejdź do folderu odpowiadającego Twojej roli.
3. Zapoznaj się z plikiem `README.md` w danym folderze.
4. Zacznij pracę zgodnie ze strukturą opisaną w README.

## Zasady współpracy

- Każda rola pracuje głównie w swoim folderze.
- Zmiany wprowadzaj na osobnych branchach i twórz Pull Requesty do **wip**.
- Po weryfikacji prace są mergowane z **wip** do **main**.
- Opisuj commity w języku polskim lub angielskim, jasno i zwięźle.
