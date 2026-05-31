import pandas as pd
import statsmodels.api as sm
from statsmodels.stats.outliers_influence import variance_inflation_factor

def calculate_vif(X: pd.DataFrame) -> pd.DataFrame:
    X_with_const = sm.add_constant(X)
    vif_data = pd.DataFrame()
    vif_data["Zmienna"] = X_with_const.columns
    vif_data["VIF"] = [
        variance_inflation_factor(X_with_const.values, i)
        for i in range(X_with_const.shape[1])
    ]
    return vif_data[vif_data["Zmienna"] != "const"].reset_index(drop=True)


def estimate_count_models(X: pd.DataFrame, y: pd.Series, label: str):
    X_with_const = sm.add_constant(X)

    print(f"  ESTYMACJA MODELI: {label}")
    print("\nWSPÓŁCZYNNIKI INFLACJI WARIANCJI (VIF)")
    try:
        vif_df = calculate_vif(X)
        print(vif_df.to_string(index=False, formatters={"VIF": "{:.2f}".format}))
    except Exception as e:
        print(f"Nie udało się obliczyć VIF: {e}")

    try:
        model_nb = sm.NegativeBinomial(y, X_with_const).fit(disp=False)
        print("\n--- SUMMARY NEGATIVE BINOMIAL")
        print(model_nb.summary())
        return model_nb
    except Exception as e:
        print(f"\n Error {e}")
        return None