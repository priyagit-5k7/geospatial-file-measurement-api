import uuid
from sqlalchemy import Column, String, Integer, Float, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.db.database import Base

class FileMetadata(Base):
    __tablename__ = "file_metadata"

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    filename = Column(String, index=True)
    feature_count = Column(Integer, default=0)
    crs = Column(String, nullable=True) # Source CRS
    status = Column(String, default="PROCESSING") # PROCESSING, COMPLETED, FAILED
    error_message = Column(String, nullable=True)
    
    features = relationship("FeatureMeasurement", back_populates="file")

class FeatureMeasurement(Base):
    __tablename__ = "feature_measurement"

    id = Column(Integer, primary_key=True, index=True)
    file_id = Column(String, ForeignKey("file_metadata.id"))
    feature_index = Column(String, index=True)
    geometry_type = Column(String)
    geometry_wkt = Column(String) # Store geometry as WKT for simplicity in SQLite without Spatialite
    properties = Column(JSON, nullable=True)
    measurement_value = Column(Float, nullable=True)
    measurement_unit = Column(String, nullable=True)
    measurement_crs = Column(String, nullable=True) # The CRS used for measurement
    
    file = relationship("FileMetadata", back_populates="features")
