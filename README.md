# Customer Lifetime Value (CLV) Forecaster

## 🎯 Objetivo del Proyecto

Desarrollar un sistema **end-to-end** que calcule y exponga el **Customer Lifetime Value (CLV)** de cada cliente de un e-commerce.  
El entregable incluye:

1. **ETL reproducible** que limpia y consolida las transacciones históricas.  
2. **Modelos de CLV** (Pareto/NBD + XGBoost de supervivencia opcional) registrados en MLflow.  
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
≈ 1,067,000 filas (líneas de producto) × 8 columnas, cubriendo **01-dic-2009 → 09-dic-2011**. Cada fila registra un artículo dentro de una factura; una misma factura puede generar varias filas.  [UCI Machine Learning Repository](https://archive.ics.uci.edu/ml/datasets/online%2Bretail%2BII?utm_source=chatgpt.com) 
[Kaggle](https://www.kaggle.com/datasets/mathchi/online-retail-ii-data-set-from-ml-repository?utm_source=chatgpt.com)

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
6. **Almacenamiento** – Disponible en `.csv` (~117 MB) y `.xlsx` (dos hojas: *Year 2009-2010*, *Year 2010-2011*). El CSV facilita lecturas en *streaming* y evita dependencias de Excel.  [oai_citation:4‡Medium](https://medium.com/data-science/preprocessing-large-datasets-online-retail-data-with-500k-instances-3f24141f511?utm_source=chatgpt.com)  
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
│   ├── etl_clv.ipynb     # limpieza y feature engineering
│   └── model_pareto.ipynb
├── src/
│   ├── __init__.py
│   ├── data/
│   │   ├── load.py
│   │   └── preprocess.py
│   ├── models/
│   │   ├── pareto_nbd.py
│   │   └── xgb_survival.py
│   └── api/
│       └── main.py       # FastAPI app
├── tests/
│   ├── test_data.py
│   └── test_models.py
├── docker/
│   ├── Dockerfile
│   └── docker-compose.yml
└── .github/
    └── workflows/
        └── ci.yml        # lint + tests + build
```


## Instalación rápida

```bash
git clone https://github.com/<tu-user>/clv-forecaster.git
cd clv-forecaster
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

Requisitos mínimos
- Python ≥ 3.9
- pip ≥ 22
- RAM 4 GB (el dataset cabe cómodamente)

## Uso rápido

1.	ETL

    ```bash
    jupyter notebook notebooks/etl_clv.ipynb
    ```

2. Entrenamiento + tracking

    ```bash
    python -m src.models.pareto_nbd train
    mlflow ui
    ```

3. API local

    ```bash
    uvicorn src.api.main:app --reload
    ```

4. Dashboard

    ```bash
    streamlit run dashboards/clv_dashboard.py
    ```

## Principales dependencias

| Categoría                 | Paquete(s)                         | Propósito Principal                                                      |
| :------------------------ | :--------------------------------- | :----------------------------------------------------------------------- |
| **Análisis de Datos**     | `pandas`, `pyarrow`                | Manipulación de datos y lectura/escritura eficiente en formato Parquet.    |
| **Modelado CLV**          | `lifetimes`, `xgboost`             | Implementación de modelos probabilísticos (Pareto/NBD) y de supervivencia. |
| **MLOps**                 | `mlflow`                           | Seguimiento de experimentos, versionado de modelos y registro de métricas. |
| **API & Backend**         | `fastapi`, `uvicorn`               | Creación de una API REST de alto rendimiento para servir predicciones.   |
| **Visualización**         | `streamlit`, `plotly`              | Desarrollo de dashboards interactivos para explorar resultados y cohortes. |
| **Testing & Calidad**     | `pytest`, `hypothesis`             | Pruebas unitarias, de integración y basadas en propiedades.              |
| **Contenerización**       | `docker`, `docker-compose`         | Empaquetado de la aplicación y sus dependencias para un despliegue aislado y reproducible. |

## Buenas prácticas incluidas
- Copy-on-Write en Pandas 2.3 para memoria eficiente.
- Tipado con type hints y mypy.
- Pre-commit hooks: black, flake8, isort.
- Tests de rendimiento (pytest-benchmark) en modelos.
- Continuous Integration (GitHub Actions) → lint + tests + build Docker.

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

**Idea global**  
1. **ETL** prepara los datos → 2. **Modelos** (Pareto/NBD y/o XGBoost) calculan CLV → 3. **MLflow** registra todo → 4. **FastAPI + Docker** sirven el modelo a otros sistemas (**CRM**, **ESP**, **BI**) → 5. **Streamlit/Plotly** ofrecen una interfaz visual para analistas y marketers.

## Contribuciones

Las pull-requests son bienvenidas. Antes de proponer cambios:
	1.	Crea un issue con descripción concisa.
	2.	Sigue el estilo de commit feat|fix|docs(scope): mensaje.
	3.	Verifica que pytest y flake8 pasen localmente.

## Licencia

This project is licensed under the MIT License.

## Referencias clave
- Fader, Sarmi & Hardie – Customer-Base Analysis in a Discrete-Time Framework.
- Wes McKinney – Python for Data Analysis (3.ª ed.).
- Sitio oficial de Pandas 2.3 – guía Copy-on-Write.
- Blog B. Coussement – “CLV Models with Pareto/NBD”.
