from fastapi import FastAPI
from app.api import endpoints
from app.db.database import engine, Base

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Geospatial File Measurement API",
    description="Aereo Cloud Internship Assignment - Backend Service for processing Shapefiles and KML",
    version="1.0.0"
)

app.include_router(endpoints.router, prefix="/api")

@app.get("/")
def root():
    return {"message": "Welcome to the Geospatial API. Use /docs for Swagger UI."}
