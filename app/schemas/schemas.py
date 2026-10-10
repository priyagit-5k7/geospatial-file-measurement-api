from pydantic import BaseModel
from typing import List, Optional, Any, Dict

class FeatureMeasurementSchema(BaseModel):
    feature_index: str
    geometry_type: str
    geometry_wkt: str
    properties: Optional[Dict[str, Any]]
    measurement_value: Optional[float]
    measurement_unit: Optional[str]
    measurement_crs: Optional[str]

    class Config:
        orm_mode = True
        from_attributes = True

class FileStatusResponse(BaseModel):
    id: str
    filename: str
    feature_count: int
    crs: Optional[str]
    status: str
    error_message: Optional[str]

    class Config:
        orm_mode = True
        from_attributes = True

class FileUploadResponse(BaseModel):
    id: str
    message: str

class MeasurementsResponse(BaseModel):
    id: str
    measurements: List[FeatureMeasurementSchema]
