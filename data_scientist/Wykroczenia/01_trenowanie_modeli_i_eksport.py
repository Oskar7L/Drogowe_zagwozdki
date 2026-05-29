import pandas as pd
import numpy as np
import statsmodels.api as sm
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.inspection import permutation_importance
from sklearn.metrics import confusion_matrix, classification_report
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
import warnings

warnings.filterwarnings('ignore')

df = pd.read_csv('Ostateczna_Baza_Analiza.csv')

zmienne_do_usuniecia = ['data', 'skrzyzowanie', 'wykroczenie', 'sygnalizacja', 'warunki_pogodowe',
                        'warunki_oswietleniowe', 'stan_nawierzchni', 'ustap_pierwszenstwa_lz',
                        'koniec_drogi_z_pierwszenstwem_lz', 'tramwaj']
df = df.drop(columns=[col for col in zmienne_do_usuniecia if col in df.columns], errors='ignore')

kategorie_bazowe = ['pogoda_dobre_warunki', 'oswietlenie_dzien', 'nawierzchnia_sucha']
X = df.drop(columns=['Y_kategoria'] + kategorie_bazowe, errors='ignore').apply(pd.to_numeric, errors='coerce').fillna(0)

mapowanie_do_modelu = {'Manewry_i_przepisy': 0, 'Dynamika_i_odleglosc': 1, 'Wymuszenie_pojazdy': 2,
                       'Zdarzenia_z_pieszymi': 3}
mapowanie_do_tekstu = {0: 'Manewry', 1: 'Dynamika', 2: 'Wymuszenia', 3: 'Piesi'}
y_kategoryczne = df['Y_kategoria'].map(mapowanie_do_modelu)
X_logit = sm.add_constant(X)

print("- Przetwarzam Model 1: Regresja One-vs-Rest...")
zmienne_binarne = ['sciezka_rowerowa', 'sygnalizacja_obecna', 'sygnalizacja_awaria', 'pogoda_opady',
                   'pogoda_zla_widocznosc', 'oswietlenie_noc_jasno', 'oswietlenie_noc_ciemno_zmrok',
                   'nawierzchnia_trudna']

def generuj_interpretacje(row):
    zmienna = row['Cecha']
    or_val = row['OR']
    p_val = row['P_value']

    if p_val >= 0.05:
        return "Nieistotna statystycznie (p >= 0.05) - wynik może być dziełem przypadku."

    procent = abs((or_val - 1) * 100)
    if zmienna in zmienne_binarne:
        if or_val > 1:
            return f"Wystąpienie tej cechy sprawia, że szansa na to zdarzenie jest {or_val:.2f} razy większa."
        else:
            return f"Wystąpienie tej cechy sprawia, że szansa na to zdarzenie maleje o {procent:.1f}%."
    else:
        kierunek = "rośnie" if or_val > 1 else "maleje"
        return f"Wraz ze wzrostem o 1 jednostkę, szansa na wystąpienie zdarzenia {kierunek} o {procent:.1f}%."

wszystkie_wyniki_ovr = []
kategorie_oryginalne = ['Zdarzenia_z_pieszymi', 'Wymuszenie_pojazdy', 'Manewry_i_przepisy', 'Dynamika_i_odleglosc']
przyjazne_nazwy = {'Zdarzenia_z_pieszymi': 'Piesi', 'Wymuszenie_pojazdy': 'Wymuszenia', 'Manewry_i_przepisy': 'Manewry',
                   'Dynamika_i_odleglosc': 'Dynamika'}

for kat_orig in kategorie_oryginalne:
    y_bin = (df['Y_kategoria'] == kat_orig).astype(int)
    model_ovr = sm.Logit(y_bin, X_logit).fit(disp=0, method='bfgs', maxiter=1000)

    df_ovr = pd.DataFrame({
        'Kategoria': przyjazne_nazwy[kat_orig],
        'Cecha': model_ovr.params.index,
        'OR': np.exp(model_ovr.params.values),
        'P_value': model_ovr.pvalues.values
    })

    df_ovr = df_ovr[df_ovr['Cecha'] != 'const']
    df_ovr['Interpretacja'] = df_ovr.apply(generuj_interpretacje, axis=1)
    wszystkie_wyniki_ovr.append(df_ovr)

df_pelny_ovr = pd.concat(wszystkie_wyniki_ovr)
df_slownik_pelny = pd.read_csv('OR_interpretacje.csv')
df_pelny_ovr = pd.merge(df_pelny_ovr, df_slownik_pelny, on=['Kategoria', 'Cecha'], how='left')
df_pelny_ovr.to_csv('eksport_ovr_pelny.csv', index=False)

print("- Przetwarzam Model 2: MNLogit...")
model_mn = sm.MNLogit(y_kategoryczne, X_logit).fit(disp=0, method='lbfgs', maxiter=2000)

wszystkie_asocjacje = []
for i, kat in zip(range(1, 4), ['Dynamika', 'Wymuszenia', 'Piesi']):
    df_mn = pd.DataFrame({
        'Kategoria': kat,
        'Cecha': X.columns,
        'Efekt_Log': np.log(np.exp(model_mn.params.iloc[1:, i - 1].values)),
        'P_value': model_mn.pvalues.iloc[1:, i - 1].values
    })
    wszystkie_asocjacje.append(df_mn[df_mn['P_value'] < 0.1])

pd.concat(wszystkie_asocjacje).to_csv('eksport_mnlogit_pelny.csv', index=False)

print("- Przetwarzam Model 3: Lasy Losowe...")
X_train, X_test, y_train, y_test = train_test_split(X, y_kategoryczne, test_size=0.2, stratify=y_kategoryczne,
                                                    random_state=42)

pipeline = Pipeline([
    ('imputer', SimpleImputer(strategy='median')),
    ('rf', RandomForestClassifier(n_estimators=300, class_weight='balanced', random_state=42))
])
pipeline.fit(X_train, y_train)
y_pred = pipeline.predict(X_test)

perm = permutation_importance(pipeline, X_test, y_test, n_repeats=5, random_state=42)
pd.DataFrame({
    'Cecha': X.columns,
    'Waga': perm.importances_mean
}).to_csv('eksport_rf_waznosc.csv', index=False)

y_test_tekst = y_test.map(mapowanie_do_tekstu)
y_pred_tekst = pd.Series(y_pred).map(mapowanie_do_tekstu)
etykiety = ['Manewry', 'Dynamika', 'Wymuszenia', 'Piesi']

pd.DataFrame(
    confusion_matrix(y_test_tekst, y_pred_tekst, labels=etykiety, normalize='true') * 100,
    index=etykiety, columns=etykiety
).to_csv('eksport_macierz.csv')

pd.DataFrame(
    classification_report(y_test_tekst, y_pred_tekst, labels=etykiety, output_dict=True)
).T.to_csv('eksport_raport.csv')

print("\nSUKCES! Utworzono 5 plikow CSV z pelnymi danymi.")