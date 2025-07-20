"""
Test de integración rápido para el endpoint /predict_clv.

Estrategia:
1. Añadimos dinámicamente la carpeta src/ al PYTHONPATH para que
   Python encuentre 'api.main' cuando pytest se ejecuta desde la raíz.
2. Usamos TestClient de FastAPI para hacer una petición POST.
3. Verificamos código 200 y que clv_6m sea un número positivo.
"""

import sys
from pathlib import Path

# ---------- Habilitar importaciones relativas ----------
ROOT_DIR = Path(__file__).resolve().parents[1]     # clv-forecaster/
SRC_DIR = ROOT_DIR / "src"
sys.path.append(str(SRC_DIR))                      # ahora 'import api.main' funciona
# --------------------------------------------------------

from api.main import app                           # noqa: E402  (import después del sys.path append)
from fastapi.testclient import TestClient          # noqa: E402

client = TestClient(app)


def test_predict_clv():
    payload = {
        "frequency": 4,
        "recency": 100,
        "T": 365,
        "monetary": 30.0,
    }
    response = client.post("/predict_clv", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert "clv_6m" in data
    assert isinstance(data["clv_6m"], (int, float))
    assert data["clv_6m"] > 0