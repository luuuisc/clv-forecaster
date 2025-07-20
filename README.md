# Customer Lifetime Value (CLV) Forecaster

## 🎯 Objetivo del Proyecto

Desarrollar un sistema **end-to-end** que calcule y exponga el **Customer Lifetime Value (CLV)** de cada cliente de un e-commerce.  
El entregable incluye:

1. **ETL reproducible** que limpia y consolida las transacciones históricas.  
2. **Modelos de CLV** (Pareto/NBD) registrados en MLflow.  
3. **Servicio FastAPI / Docker** con el endpoint `/predict_clv` para integrarse a CRM, ESP o BI.  
4. **Dashboard Streamlit/Plotly** para explorar cohortes y segmentos de valor.

---

## Aplicación en la industria

| Área | Uso del CLV | Beneficios concretos |
|------|-------------|----------------------|
| **Marketing de retención** | Priorizar e-mails, SMS o push según valor futuro | ↓ CAC, ↑ ROI en canales propios |
| **Gestión de presupuestos** | Dirigir inversión publicitaria a segmentos de mayor retorno | Eficiencia del gasto ↑ ~15 % |
| **Finanzas** | Proyectar ingresos recurrentes para flujos de caja y valoración | Planificación más realista que el promedio histórico |
| **Producto** | Detectar patrones de churn y oportunidades de upsell/cross-sell | Features que elevan la recurrencia |
| **Atención al cliente** | Ajustar SLA y recursos según valor del cliente | Retención de cuentas de alto valor |


## 🚀 Entregables finales  

1. **API REST** (`/predict_clv`) con FastAPI  
2. **Dashboard CLV** interactivo (Plotly/Streamlit)  
3. Pipeline MLOps rastreado en **MLflow** y contenedorizado con **Docker**


## Motivación de negocio

- **Marketing**: identificar segmentos de alto valor y optimizar _Customer
  Acquisition Cost_ (CAC).  
- **Finanzas**: proyectar ingresos futuros y calcular provisiones.  
- **Producto**: priorizar features que eleven retención y compra repetida.


## Dataset

Usamos el **Online Retail II (UCI)**: transacciones de un e-commerce británico
(2009-2011) con: `InvoiceDate`, `CustomerID`, `Quantity`, `Price`,
`Country`.  
El notebook `notebooks/etl_clv.ipynb` descarga y limpia este set, eliminando:

- devoluciones (`Quantity < 0`)
- facturas sin cliente (`CustomerID` nulo)
- pedidos con `UnitPrice ≤ 0`

Exporta `data/processed/clv.parquet` comprimido con **Snappy**.

## Descripción del dataset — *Online Retail II*

**Fuente**  
UCI Machine Learning Repository → *Online Retail II* (transacción real de un e-commerce británico)  [UCI Machine Learning Repository](https://archive.ics.uci.edu/ml/datasets/online%2Bretail%2BII?utm_source=chatgpt.com)

**Volumen**  
≈ 1,067,000 filas (líneas de producto) × 8 columnas, cubriendo **01-dic-2009 → 09-dic-2011**. Cada fila registra un artículo dentro de una factura; una misma factura puede generar varias filas. 

### Esquema de columnas

| Columna        | Tipo sugerido | Descripción                                                            |
|----------------|--------------|------------------------------------------------------------------------|
| `Invoice`      | `string`     | Código de factura. Prefijo **“C”** indica devolución.                  |
| `StockCode`    | `string`     | SKU (código del producto).                                             |
| `Description`  | `string`     | Nombre del producto. Incluye caracteres especiales  (ISO-8859-1).      |
| `Quantity`     | `int64`      | Unidades vendidas; **negativo ⇒ devolución**.                          |
| `InvoiceDate`  | `datetime64[ns]` | Fecha y hora de la transacción.                                  |
| `UnitPrice`    | `float64`    | Precio unitario (libras esterlinas).                                   |
| `CustomerID`   | `Int64` (nullable) | Identificador de cliente; ~25 % de filas sin ID.            |
| `Country`      | `category`   | País del cliente (38 valores; Reino Unido domina).                     |  [oai_citation:3‡Brainly](https://brainly.com/question/33344596?utm_source=chatgpt.com)

### Organización y particularidades

1. **Nivel de granularidad** – Cada fila = 1 línea de producto; para obtener el ticket completo agrupa por `Invoice`.  
2. **Retornos** – Filas con `Quantity < 0` y `Invoice` con “C…” anulan pedidos anteriores.  
3. **Clientes anónimos** – Ausencia de `CustomerID` impide calcular métricas de retención; se recomienda descartarlos o imputar con un placeholder.  
4. **Moneda** – Todos los importes están en **GBP**; convierte a tu divisa si planeas mezclar con otras fuentes.  
5. **Temporización** – Ventana de casi 2 años permite análisis de **cohortes** y modelos de recencia-frecuencia.  
6. **Almacenamiento** – Disponible en `.csv` (~117 MB) y `.xlsx` (dos hojas: *Year 2009-2010*, *Year 2010-2011*). El CSV facilita lecturas en *streaming* y evita dependencias de Excel.  [Preprocessing Large Datasets: Online Retail Data with 500k+ Instances](https://medium.com/data-science/preprocessing-large-datasets-online-retail-data-with-500k-instances-3f24141f511)  
7. **Calidad** – Existen duplicados de línea exactos y descripciones vacías; conviene aplicar `drop_duplicates()` y `fillna('Unknown')`.

### Uso típico en proyectos CLV

* **ETL**: leer, filtrar devoluciones, eliminar `UnitPrice ≤ 0`, generar columna `Sales = Quantity × UnitPrice`.  
* **RFM**: calcular *Recency*, *Frequency*, *Monetary* por `CustomerID` para alimentar Pareto/NBD.  
* **Cohortes**: agrupar por mes de primera compra (`InvoiceDate.dt.to_period('M')`).  
* **Análisis de producto**: market basket, reglas de asociación por `Invoice`.

> Este dataset es ideal para ejercicios de **customer analytics**, predicción de **CLV**, segmentación y detección de churn, ya que refleja compras reales, incluye devoluciones y ofrece una dimensión temporal suficiente para modelos de supervivencia.

## Arquitectura de la solución

```text
          +----------+       +-----------+
  CSV  -> |  ETL ✨  | ---->  | Parquet   |   ----+
          +----------+       +-----------+       |
                                                 v
                         +-----------------------------------+
                         |  Modelo Pareto/NBD  ➜  CLV table |
                         +-----------------------------------+
                                                |
               +---------------------+          |  MLflow
               |  XGBoost Survival   | ---------+  tracking
               +---------------------+
                        |
                        v
            +-----------------+     Docker / k8s    +--------------+
            | FastAPI server  |  ----------------->  |   React/     |
            | `/predict_clv`  |                     | Streamlit UI |
            +-----------------+                     +--------------+
```

## Estructura de carpetas

```
clv-forecaster/
├── README.md
├── requirements.txt
├── .gitignore
├── data/
│   ├── raw/              # zip original de Kaggle
│   └── processed/        # .parquet limpio
├── notebooks/
│   ├── mlruns 
│   ├── etl_clv.ipynb     # limpieza y feature engineering
│   └── model_pareto.ipynb
├── models/
│   ├── bgf.pkl
│   └── ggf.pkl
├── src/
│   ├── __pycache__/ 
│   └── api/
│       └── main.py       # FastAPI app
├── tests/
│   ├── __pycache__/
│   ├── test_api.py
├── docker/
│   ├── Dockerfile
```

## Instalación rápida

```bash
git clone https://github.com/luuuisc/clv-forecaster
cd clv-forecaster
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

Requisitos mínimos
- Python ≥ 3.9
- pip ≥ 22
- RAM 4 GB (el dataset cabe cómodamente)

## Estructura de carpetas y archivos

| Ruta / archivo | Contenido | Para qué se usa |
|----------------|-----------|-----------------|
| `data/raw/online_retail_II.csv` (✗ git) | Dataset original descargado de Kaggle | Fuente única de verdad. Se mantiene fuera de Git. |
| `data/processed/clv.parquet` | Datos limpios (ventas positivas, tipos correctos) | Input estándar para todos los modelos y dashboards. |
| `data/processed/clv_predictions.parquet` | Tabla final con `frequency`, `recency`, `T`, `monetary`, `clv_6m` | What-if rápido y dashboard. |
| `notebooks/etl_clv.ipynb` | Código + docs de limpieza **ETL** | Genera `clv.parquet`. |
| `notebooks/model_pareto_nbd.ipynb` | Entrena **BetaGeo** y **GammaGamma**, calcula CLV, registra en MLflow | Prototipo de modelado. |
| `mlruns/` (✗ git) | Experimentos MLflow | Runs, parámetros, métricas, artefactos. |
| `models/` <br>  • `bgf.pkl` <br>  • `ggf.pkl` | Modelos serializados con `joblib` | Cargados por la API para predicción on-line. |
| `src/api/main.py` | Servicio **FastAPI** con endpoint `/predict_clv` | Integra los modelos a CRM/ESP/BI. |
| `requirements.txt` | Dependencias fijadas | Reproducibilidad. |
| `README.md` | Visión, glosario, pasos, estructura | Documentación viva. |
| `.gitignore` | Excluye datasets brutos, artefactos MLflow, venv | Repo limpio y ligero. |

### Flujo de trabajo end-to-end

```
CSV bruto  ──▶  etl_clv.ipynb  ──▶  clv.parquet
                               │
                               ▼
                model_pareto_nbd.ipynb  (RFM + BetaGeo + GammaGamma)
                               │
                               ▼
                    clv_predictions.parquet
                               │
                               ▼
                   mlflow run + artefactos
                               │
                               ▼
            FastAPI /predict_clv  →  CRM / ESP / BI
```

## Uso del modelo

#### 1. Clonar y crear venv
```bash
git clone https://github.com/luuuisc/clv-forecaster && cd clv-forecaster
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

#### 2. Colocar CSV bruto (o usar Kaggle API)
```bash
mkdir -p data/raw && cp /tu/ruta/online_retail_II.csv data/raw/
```

#### 3. Ejecutar ETL
```bash
jupyter nbconvert --to notebook --execute notebooks/etl_clv.ipynb
```

#### 4. Entrenar modelo
```bash
jupyter nbconvert --to notebook --execute notebooks/model_pareto_nbd.ipynb
```

#### 5. Servir API
```bash
uvicorn src.api.main:app --host 0.0.0.0 --port 8000
```

#### 6. Ejecución dashboard
```bash
streamlit run dashboards/clv_dashboard.py
```

Swagger disponible en http://localhost:8000/docs.

## 📊 Dashboard interactivo (Streamlit)

### Cómo ejecutarlo

```bash
# desde la raíz del proyecto
streamlit run dashboards/clv_dashboard.py
# abrirá http://localhost:8501
```

Requiere `streamlit` y `plotly`, ya incluidos en `requirements.txt`.

### Componentes del panel Streamlit

| Sección                       | ¿Qué muestra?                                                         | Interpretación clave                                                                                                   | Preguntas que responde                                          |
|-------------------------------|-----------------------------------------------------------------------|------------------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------|
| **Filtro «País»**             | Selector «Todos» + 38 países                                          | Actualiza simultáneamente heatmap, boxplot y métrica.                                                                  | ¿Cómo cambian retención y CLV según país o región?              |
| **Filtro «Paleta de color»**  | Opciones: Viridis · Blues · TealGrn · Hot (se puede ampliar)          | Permite al usuario elegir la escala cromática del heatmap para comodidad visual.                                       | —                                                               |
| **Heatmap de retención**      | Matriz *Cohorte × Mes* → nº clientes activos (escala seleccionada)    | Fila = cohorte de alta; columnas = meses posteriores. Degradado lento = buena retención.                               | ¿Qué cohorte se comporta mejor? ¿Hay picos estacionales claros? |
| **Boxplot CLV 6 m**           | Distribución y outliers de `clv_6m`                                   | Caja = IQR; bigotes = rango típico; puntos = outliers (valiosos o atípicos).                                           | ¿Cuántos clientes superan £X? ¿Hay concentración de valor?      |
| **Métrica resumen**           | `CLV` medio de la vista actual (con filtros aplicados)                | Sirve de referencia para fijar CAC máximo, evaluar ROI de campañas, etc.                                               | ¿Cuál es el valor medio por cliente en el segmento filtrado?    |


### Cómo sacar insight rápidamente
1. Selecciona “Todos” → revisa la diagonal principal del heatmap:
    - 60 % la 1ª columna ✔️
    - <10 % a los 6 meses ❌ (alerta de churn).
2. Elige un país concreto (p.ej. Netherlands).
    - Observa si mantiene o cae más rápido vs global.
3. Mira el boxplot:
    - Muchos puntos por encima del upper whisker = oportunidad de campaña VIP.
    - Caja muy baja = ingresos concentrados en pocos clientes (“80/20”).

En dos frases:
El dashboard traduce datos transaccionales y predicciones de CLV en visualizaciones accionables para Marketing. Permite comparar retención por cohorte, detectar canales estacionales y evaluar el potencial de ingresos futuro por país o segmento.

## 🧪 ¿Cómo probar el endpoint `/predict_clv`?

### Opción A ─ Swagger UI (recomendado)

1. **Inicia la API**  
   ```bash
   uvicorn src.api.main:app --reload
   ```

2. Abre tu navegador en http://localhost:8000/docs.

    Swagger cargará automáticamente todos los endpoints.

3. En la sección POST /predict_clv
    - Haz clic y pulsa Try it out.
    - Rellena el JSON de ejemplo:
        ```bash
        {
        "frequency": 3,
        "recency": 120,
        "T": 365,
        "monetary": 40.0
        }
        ```
    - Pulsa Execute.

        En Response body verás algo como:
        ```bash
        {
        "clv_6m": 12.48
        }
        ```
        
**Interpretación**

El cliente (3 compras, última hace 120 d, 1 año de antigüedad, ticket medio £40) se espera que genere £12.48 en los próximos 6 meses.

### Opción B ─ cURL / Terminal

```bash
curl -X POST http://localhost:8000/predict_clv \
     -H "Content-Type: application/json" \
     -d '{ "frequency": 3, "recency": 120, "T": 365, "monetary": 40.0 }'
```

Respuesta:

```bash
{"clv_6m":12.48}
```

(Puedes sustituir los valores para testear distintos perfiles de cliente.)

### Campos de entrada

| Campo       | Significado                                                                                   |
|-------------|------------------------------------------------------------------------------------------------|
| `frequency` | Número de compras históricas del cliente                                                       |
| `recency`   | Días transcurridos desde la última compra                                                      |
| `T`         | Antigüedad del cliente en días (diferencia entre primera compra y fecha de corte del dataset) |
| `monetary`  | Ticket medio histórico en GBP (importe medio gastado por compra)                               |

La API valida estos campos con Pydantic; si falta alguno o el tipo es incorrecto devolverá 422 Unprocessable Entity.

## Tecnologías y librerías empleadas

| Categoría | Paquetes clave | Función |
|-----------|----------------|---------|
| **Manipulación de datos** | `pandas 2.3`, `pyarrow` | Limpieza y Parquet (Snappy). |
| **Modelos CLV** | `lifetimes` (BetaGeoFitter, GammaGammaFitter) | Probabilidad de compra futura y ticket medio. |
| **Experimentos** | `mlflow` | Runs, parámetros, métricas, artefactos. |
| **Serialización** | `joblib` | Guarda modelos para carga rápida. |
| **Servicio web** | `fastapi`, `uvicorn`, `pydantic` | API + validación + Swagger. |
| **Dashboard** | `streamlit`, `plotly` | Cohortes y CLV interactivos (próximo). |
| **Contenedorización** | `docker` | Empaquetar API + modelos. |
| **Testing/calidad** | `pytest`, `black`, `flake8` | Calidad y CI (por configurar). |

## Detalle de los modelos

| Modelo | Variables que consume | Hiperparámetros | Salida clave |
|--------|----------------------|-----------------|--------------|
| **BetaGeoFitter** | `frequency`, `recency`, `T` | `penalizer_coef = 0.001` | `pred_purchases_6m` – nº esperado de compras en 180 d |
| **GammaGammaFitter** | `frequency`, `monetary` | `penalizer_coef = 0.001` | `exp_avg_sales` – gasto medio esperado por compra |
| **CLV 6 m** | Resultado de ambos modelos | — | `clv_6m = pred_purchases_6m × exp_avg_sales` |

## 🗺️ Roadmap Sugerido

Este proyecto está diseñado para ser construido de manera incremental. A continuación, se presenta una posible secuencia de desarrollo dividida en sprints.

| Sprint | Enfoque Principal             | Entregables Clave                                                              |
| :----- | :---------------------------- | :----------------------------------------------------------------------------- |
| **1**  | **Fundación y ETL**           | Estructura del proyecto, pipeline de ETL reproducible (`clv.parquet`).         |
| **2**  | **Primer Modelo y MLOps**     | Modelo baseline (Pareto/NBD) con seguimiento de experimentos en MLflow.        |
| **3**  | **API de Predicción**         | Endpoint `/predict_clv` en FastAPI, `Dockerfile` y `docker-compose.yml`.       |
| **4**  | **Visualización y Modelo Avanzado** | Dashboard interactivo en Streamlit y exploración de un modelo XGBoost Survival. |
| **5**  | **Despliegue a Producción**   | Pipeline de CI/CD para despliegue automático en un servicio cloud (AWS/GCP).  |

## Glosario de siglas y conceptos

| Sigla / término | Significado | Rol dentro del proyecto |
|-----------------|-------------|-------------------------|
| **ETL** | **E**xtract – **T**ransform – **L**oad | Flujo reproducible que extrae los datos brutos, los limpia y los guarda en Parquet para que todos los pasos posteriores partan de la misma versión de los datos. |
| **CLV** | **C**ustomer **L**ifetime **V**alue (Valor de Vida del Cliente) | Métrica clave: ingresos netos que un cliente generará durante toda su relación con la empresa. Es la variable objetivo de nuestros modelos. |
| **Pareto/NBD** | **Pareto / Negative Binomial Distribution** | Modelo estadístico que, a partir de recencia, frecuencia y edad del cliente, estima la probabilidad de compras futuras y, por extensión, el CLV. |
| **XGBoost** | e**X**treme **G**radient **Boost**ing | Algoritmo de árboles potenciado por gradiente. En modo “supervivencia” lo usaremos (opcionalmente) para predecir tiempo hasta la siguiente compra o churn. |
| **MLflow** | *Machine Learning flow* | Plataforma open-source para registrar experimentos, versiones de datos y artefactos de modelos, facilitando reproducibilidad y comparación. |
| **FastAPI** | Framework web asíncrono en Python | Expondrá el modelo entrenado en un endpoint HTTP (`/predict_clv`) que devuelve el CLV estimado dado un cliente. |
| **Docker** | Contenerización de aplicaciones | Empaqueta código, dependencias y modelo en una imagen que corre igual en cualquier entorno: local, servidor o nube. |
| **CRM** | **C**ustomer **R**elationship **M**anagement | Sistema donde Marketing/Ventas gestionan contactos. Consumirá nuestro endpoint para mostrar el CLV en tiempo real. |
| **ESP** | **E**-mail **S**ervice **P**rovider | Plataformas de e-mail (SendGrid, Mailchimp). Usarán el CLV para personalizar frecuencia, ofertas y segmentación. |
| **BI** | **B**usiness **I**ntelligence | Herramientas de dashboarding (Tableau, Power BI) que podrán leer el Parquet o el API para métricas agregadas. |
| **Streamlit** | Framework Python para apps web de datos | Construiremos un panel interactivo donde el equipo de negocio explore cohortes y distribuciones de CLV. |
| **Plotly** | Librería de gráficas interactivas | Generará los charts (curvas de retención, boxplots, etc.) dentro del dashboard de Streamlit. |

## Contribuciones

Las pull-requests son bienvenidas. 

Antes de proponer cambios:
1. Crea un issue con descripción concisa.
2. Sigue el estilo de commit feat|fix|docs(scope): mensaje.
3. Verifica que pytest y flake8 pasen localmente.

## Licencia

This project is licensed under the MIT License.
