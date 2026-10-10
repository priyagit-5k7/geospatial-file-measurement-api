# Geospatial File Measurement API (Aereo Cloud Internship Assignment)

## 📌 Project Overview
A robust backend API service built with **FastAPI** that accepts geospatial files (zipped Shapefiles and KML files), processes their geometric features using **GeoPandas**, safely stores their metadata in a local **SQLite** database, and computes precise geographical measurements (Polygon Area, LineString Length).

## 🚀 Problem Statement & Objectives
The goal of this recruitment assignment is to build a highly maintainable, accurate API capable of parsing varying geospatial file formats, securely handling CRS reprojections to compute real spatial measurements (rather than naïve geographic distances), and exposing RESTful workflows with robust testing and graceful error handling. 

## ✨ Implemented Features
- **Accepts varying formats:** Direct validation and reading of `.kml` and zipped `.shp` archives (gracefully verifying companion files `.dbf` and `.shx`).
- **Dynamic CRS Projection for Accurate Measurements:** Detects coordinate reference systems. If geographic (`EPSG:4326`), dynamically estimates the best local **UTM zone** (`estimate_utm_crs()`) to ensure metric Area (sq. meters) and Length (meters) measurements are precise. Uses a globally accurate Equal-Area projection (`EPSG:6933`) fallback for inputs that span too many UTM zones (e.g., width > 12°).
- **Persistent Storage:** Caches the processed files and generated metadata into an embedded SQLite database using SQLAlchemy so that future GET requests instantly retrieve parsed metrics.
- **Resilient Exception Handling:** Gracefully handles Path Traversal attempts in ZIP files, unsupported filetypes, missing CRS metadata in inputs, and ignores unsupported metric calculations for dimensionless Point geometries.

## 🛠 Technology Stack & Architecture
- **FastAPI / Uvicorn:** Chosen over Django/DRF for modern concurrency, automatic rigorous schema validation (Pydantic), and blazing-fast response times.
- **GeoPandas / Shapely / pyproj / Fiona:** For robust geometric parsing (including KML libkml driver compatibility) and topological accuracy.
- **SQLAlchemy / SQLite:** Embeddable, zero-config relational persistence. Highly justified here to ensure seamless developer onboarding without heavy dependencies like Dockerized Postgres.

### Folder Structure
```text
app/
 ├── main.py                    # App entrypoint
 ├── api/endpoints.py           # REST URL Routing
 ├── core/config.py             # Env and config validation
 ├── db/
 │   ├── database.py            # SQLite Bootstrap
 │   └── models.py              # FileMetadata and Feature SQLAlchemy Tables
 ├── schemas/schemas.py         # Pydantic schemas for I/O validation
 └── services/
     ├── file_parser.py         # Safe zip traversal and Fiona IO
     └── measurement_service.py # Geospatial Coordinate Transformation Mathematics
tests/                          # Pytest suite testing logic & constraints
```

## ⚙ Prerequisites & Installation (Windows)
1. **Python 3.11+**
2. Depending on your Windows environment, compiling Fiona/pyproj might require GDAL. If you run into build errors during `pip install`, it's highly recommended to use the provided Docker container or install binary wheels from `conda` (e.g. `conda install geopandas`).

### Windows PowerShell Setup 

```powershell
# 1. Clone repo
git clone <repository_url>
cd <repository_folder>

# 2. Initialize Virtual Environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# 3. Install Dependencies
pip install -r requirements.txt
```

### Running the Server
Once activated:
```powershell
uvicorn app.main:app --reload
```
View automated Swagger API Documentation at: http://127.0.0.1:8000/docs

## 🐳 Docker Deployment
If binary dependency conflicts arise, simply use Docker to abstract away underlying C++ GDAL bindings!
```bash
docker build -t aereo-api .
docker run -p 8000:8000 aereo-api
```

## 📡 API Endpoints 

### 1. Upload File
`POST /api/files/`
- **Payload (multipart):** `file` (.kml or .zip Shapefile)
- **Response (201):**
```json
{
  "id": "e0b96918-a6d0-40db-91b7-a379133bd579",
  "message": "File uploaded and processed successfully."
}
```

### 2. Get File Information
`GET /api/files/{id}/`
- **Response (200):**
```json
{
  "id": "e0b96918-a6d0-40db-91b7-a379133bd579",
  "filename": "survey.kml",
  "feature_count": 12,
  "crs": "EPSG:4326",
  "status": "COMPLETED",
  "error_message": null
}
```

### 3. Get Geometry Measurements
`GET /api/files/{id}/measurements/`
- **Response (200):**
```json
{
  "id": "e0b96918-a6d0-40db-91b7-a379133bd579",
  "measurements": [
    {
      "feature_index": "0",
      "geometry_type": "Polygon",
      "geometry_wkt": "POLYGON ((...))",
      "properties": {"name": "Plot A"},
      "measurement_value": 451.2,
      "measurement_unit": "sq. meters",
      "measurement_crs": "EPSG:32643"
    }
  ]
}
```

## 🌡 Testing
Automated testing uses synthetic geometries for both KML bounding boxes and Zipped Shapefiles.
Tests guarantee endpoint status codes, validation rule triggers, and CRS measurement expectations.

Run via PowerShell:
```powershell
$env:PYTHONPATH="."
pytest -v tests/
```

## 🔍 Assumptions & Measurement Formulas
- Standard Cartesian degree arithmetic (`latitude`/`longitude`) produces inherently useless lengths.
- Measurements are natively extracted via **Shapely** (`.length`, `.area`) only *after* dynamic UTM reprojection guarantees metric accuracy. 
- Very large datasets covering huge longitudinal swaths (>12 degrees) are inherently unstable in UTM; the program safely catches these edge cases and switches to World Cylindrical Equal Area projections.

## 🔮 Learnings & Future Target Scope
**Learnings:** Safely wrapping Fiona inside an API requires handling strict temporary filesystem constraints. Bypassing unzipping vulnerability vectors was cleverly solved by using direct VFS streams `zip://...` inside GeoPandas without extracting un-trusted file chunks to temp directories.
**Future Scope:** 
1. The measurement computations block the server thread briefly for large polygons. Future refactors could adopt Celery/Redis for background jobs, and `GET /api/files/{id}` polling could return `PROCESSING` instead while workers digest massive files.
2. Direct cloud integration targeting AWS S3 (handling extremely large files using streaming). 
