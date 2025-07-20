from pathlib import Path
import pandas as pd
import joblib
from fastapi import FastAPI
from pydantic import BaseModel, Field

# ---------- carga de modelos ----------
ROOT_DIR   = Path(__file__).resolve().parents[2]
MODELS_DIR = ROOT_DIR / "models"

bgf = joblib.load(MODELS_DIR / "bgf.pkl")
ggf = joblib.load(MODELS_DIR / "ggf.pkl")

TIME_HORIZON = 180  # días

# ---------- FastAPI ----------
app = FastAPI(
    title="CLV Forecaster",
    description="Predice CLV a 6 meses usando BG/NBD + Gamma-Gamma",
    version="0.1.0",
)

## ---------- modelos de entrada ----------
class CLVInput(BaseModel):
    frequency: int = Field(..., ge=1, description="Nº de compras históricas")
    recency: int = Field(..., ge=0, description="Días entre 1ª y última compra")
    T: int = Field(..., gt=0, description="Edad del cliente (días)")
    monetary: float = Field(..., gt=0, description="Ticket medio histórico")


## ---------- rutas ----------
@app.post("/predict_clv")
def predict_clv(payload: CLVInput):
    """Devuelve el CLV a 6 meses para un único cliente."""
    df = pd.DataFrame([payload.dict()])

    # ----- usa las mismas variables en minúsculas -----
    exp_purchases = bgf.conditional_expected_number_of_purchases_up_to_time(
        TIME_HORIZON,
        df["frequency"],
        df["recency"],
        df["T"]
    )
    exp_sales = ggf.conditional_expected_average_profit(
        df["frequency"],
        df["monetary"]
    )
    clv_6m = float((exp_purchases * exp_sales).iloc[0])
    return {"clv_6m": round(clv_6m, 2)}