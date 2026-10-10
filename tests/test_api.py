from fastapi.testclient import TestClient

def test_root_endpoint(client: TestClient):
    response = client.get("/")
    assert response.status_code == 200

def test_shapefile_upload_and_measurements(client: TestClient, synthetic_shapefile_zip):
    # 1. Upload
    with open(synthetic_shapefile_zip, "rb") as f:
        response = client.post(
            "/api/files/",
            files={"file": ("test_data.zip", f, "application/zip")}
        )
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    file_id = data["id"]
    
    # 2. Get Info
    response = client.get(f"/api/files/{file_id}/")
    assert response.status_code == 200
    info = response.json()
    assert info["filename"] == "test_data.zip"
    assert info["status"] == "COMPLETED"
    assert info["feature_count"] == 3
    
    # 3. Get Measurements
    response = client.get(f"/api/files/{file_id}/measurements/")
    assert response.status_code == 200
    meas = response.json()
    assert len(meas["measurements"]) == 3
    
    # Verify Polygon
    poly_feature = next(m for m in meas["measurements"] if m["geometry_type"] == "Polygon")
    # A 1-degree square at lat 50 is approximately 111km * 71km = ~ 7.9 billion sq meters
    assert poly_feature["measurement_unit"] == "sq. meters"
    assert poly_feature["measurement_value"] > 1e9 
    
    # Verify Point
    point_feature = next(m for m in meas["measurements"] if m["geometry_type"] == "Point")
    assert point_feature["measurement_unit"] is None
    assert point_feature["measurement_value"] is None

def test_kml_upload(client: TestClient, synthetic_kml):
    with open(synthetic_kml, "rb") as f:
        response = client.post(
            "/api/files/",
            files={"file": ("test_data.kml", f, "application/vnd.google-earth.kml+xml")}
        )
    assert response.status_code == 201
    file_id = response.json()["id"]
    
    response = client.get(f"/api/files/{file_id}/")
    assert response.json()["status"] == "COMPLETED"
    
def test_invalid_file_extension(client: TestClient):
    response = client.post(
        "/api/files/",
        files={"file": ("test_data.txt", b"Hello", "text/plain")}
    )
    assert response.status_code == 400
    assert "Only .zip (Shapefile) or .kml allowed" in response.json()["detail"]
