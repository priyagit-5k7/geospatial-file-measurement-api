import os
import shutil
import tempfile
import json
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, status
from sqlalchemy.orm import Session
from pathlib import Path
from app.db.database import get_db
from app.db.models import FileMetadata, FeatureMeasurement
from app.schemas.schemas import FileUploadResponse, FileStatusResponse, MeasurementsResponse, FeatureMeasurementSchema
from app.services.file_parser import parse_geospatial_file, FileParserError
from app.services.measurement_service import calculate_measurements
from app.core.config import settings

router = APIRouter()

@router.post("/files/", response_model=FileUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_file(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not (file.filename.lower().endswith('.zip') or file.filename.lower().endswith('.kml')):
        raise HTTPException(status_code=400, detail="Invalid file type. Only .zip (Shapefile) or .kml allowed.")
        
    # Create DB entry for tracking
    file_meta = FileMetadata(filename=file.filename, status="PROCESSING")
    db.add(file_meta)
    db.commit()
    db.refresh(file_meta)
    
    # Save file to temp location safely
    try:
        suffix = Path(file.filename).suffix
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
            shutil.copyfileobj(file.file, temp_file)
            temp_file_path = temp_file.name
            
        # 1. Parse File
        gdf = parse_geospatial_file(temp_file_path, file.filename)
        
        # 2. Extract source CRS and record it
        source_crs_str = str(gdf.crs) if gdf.crs else None
        
        # 3. Calculate Measurements (Reprojects and returns measurements without dropping original geometries)
        gdf = calculate_measurements(gdf)
        
        # 4. Save Features to DB
        feature_count = 0
        for index, row in gdf.iterrows():
            geom = row.geometry
            if geom is None or geom.is_empty:
                continue
                
            props = {col: str(row[col]) for col in gdf.columns if col not in ['geometry', 'measurement_value', 'measurement_unit', 'measurement_crs'] and not (isinstance(row[col], float) and row.isna()[col])}
            
            fm = FeatureMeasurement(
                file_id=file_meta.id,
                feature_index=str(index),
                geometry_type=geom.geom_type,
                geometry_wkt=geom.wkt,
                properties=props,
                measurement_value=row.get("measurement_value"),
                measurement_unit=row.get("measurement_unit"),
                measurement_crs=row.get("measurement_crs")
            )
            db.add(fm)
            feature_count += 1
            
        file_meta.status = "COMPLETED"
        file_meta.feature_count = feature_count
        file_meta.crs = source_crs_str
        db.commit()
        
    except FileParserError as e:
        file_meta.status = "FAILED"
        file_meta.error_message = str(e)
        db.commit()
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        file_meta.status = "FAILED"
        file_meta.error_message = "Internal processing error."
        db.commit()
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")
    finally:
        if 'temp_file_path' in locals() and os.path.exists(temp_file_path):
            os.remove(temp_file_path)
            
    return FileUploadResponse(id=file_meta.id, message="File uploaded and processed successfully.")

@router.get("/files/{id}/", response_model=FileStatusResponse)
def get_file_info(id: str, db: Session = Depends(get_db)):
    file_meta = db.query(FileMetadata).filter(FileMetadata.id == id).first()
    if not file_meta:
        raise HTTPException(status_code=404, detail="File not found")
    return file_meta

@router.get("/files/{id}/measurements/", response_model=MeasurementsResponse)
def get_file_measurements(id: str, db: Session = Depends(get_db)):
    file_meta = db.query(FileMetadata).filter(FileMetadata.id == id).first()
    if not file_meta:
        raise HTTPException(status_code=404, detail="File not found")
        
    measurements = db.query(FeatureMeasurement).filter(FeatureMeasurement.file_id == id).all()
    
    return MeasurementsResponse(
        id=id,
        measurements=measurements
    )
