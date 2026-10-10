import pytest
import os
import zipfile
import fiona
import geopandas as gpd
from shapely.geometry import Polygon, LineString, Point
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.db.database import get_db, Base

# Set setting BEFORE app load
os.environ["SQLALCHEMY_DATABASE_URI"] = "sqlite:///./test.db"

engine = create_engine("sqlite:///./test.db", connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope="session")
def client():
    Base.metadata.create_all(bind=engine)
    with TestClient(app) as c:
        yield c
    Base.metadata.drop_all(bind=engine)
    if os.path.exists("./test.db"):
        os.remove("./test.db")

@pytest.fixture(scope="session")
def synthetic_shapefile_zip(tmp_path_factory):
    # Create simple shapes. EPSG:4326.
    poly = Polygon([(50.0, 50.0), (51.0, 50.0), (51.0, 51.0), (50.0, 51.0)])
    line = LineString([(50.0, 50.0), (51.0, 51.0)])
    pt = Point(50.5, 50.5)

    gdf = gpd.GeoDataFrame({
        'geometry': [poly, line, pt],
        'name': ['box', 'line', 'point'],
        'value': [10, 20, 30]
    }, crs="EPSG:4326")

    temp_dir = tmp_path_factory.mktemp("shapefiles")
    shp_path = temp_dir / "test_data.shp"
    gdf.to_file(shp_path)

    zip_path = temp_dir / "test_data.zip"
    with zipfile.ZipFile(zip_path, 'w') as zf:
        for ext in ['.shp', '.shx', '.dbf', '.prj']:
            file_to_zip = temp_dir / f"test_data{ext}"
            if file_to_zip.exists():
                zf.write(file_to_zip, arcname=f"test_data{ext}")

    return zip_path

@pytest.fixture(scope="session")
def synthetic_kml(tmp_path_factory):
    fiona.drvsupport.supported_drivers['KML'] = 'rw'
    fiona.drvsupport.supported_drivers['LIBKML'] = 'rw'
    
    poly = Polygon([(10.0, 10.0), (11.0, 10.0), (11.0, 11.0), (10.0, 11.0)])
    gdf = gpd.GeoDataFrame({'geometry': [poly], 'name': ['kml_box']}, crs="EPSG:4326")
    
    temp_dir = tmp_path_factory.mktemp("kml")
    kml_path = temp_dir / "test_data.kml"
    # Note: KML driver can be picky about properties, but simple writing usually works
    try:
        gdf.to_file(kml_path, driver='KML')
    except Exception:
        # Fallback raw KML if driver struggles to write
        kml_content = (
            '<?xml version="1.0" encoding="utf-8" ?>\n'
            '<kml xmlns="http://www.opengis.net/kml/2.2">\n'
            '<Document><Folder><name>kml_box</name>\n'
            '<Placemark>\n'
            '    <Polygon><outerBoundaryIs><LinearRing><coordinates>\n'
            '        10.0,10.0,0 11.0,10.0,0 11.0,11.0,0 10.0,11.0,0 10.0,10.0,0\n'
            '    </coordinates></LinearRing></outerBoundaryIs></Polygon>\n'
            '</Placemark>\n'
            '</Folder></Document></kml>\n'
        )
        kml_path.write_text(kml_content)
        
    return kml_path
