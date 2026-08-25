import os
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_health_check():
    """
    Verifies the operational status of the API gateway.
    Ensures the service is responsive before executing complex routing.
    """
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy", "service": "rag_module"}

def test_asset_upload_and_retrieve():
    """
    Simulates a full integration cycle of asset management.
    Validates multipart form data handling, disk storage isolation, 
    and directory traversal for asset listing.
    """
    test_project = "proj_test_automated"
    dummy_file_path = "test_logo.jpg"
    
    with open(dummy_file_path, "wb") as file_buffer:
        file_buffer.write(b"mock_binary_payload")
        
    try:
        with open(dummy_file_path, "rb") as file_stream:
            upload_response = client.post(
                f"/api/v1/projects/{test_project}/assets",
                data={"asset_type": "images"},
                files={"file": (dummy_file_path, file_stream, "image/jpeg")}
            )
        
        assert upload_response.status_code == 200
        upload_data = upload_response.json()
        assert upload_data["status"] == "success"
        assert "asset_id" in upload_data["data"]
        
        retrieve_response = client.get(f"/api/v1/projects/{test_project}/assets")
        assert retrieve_response.status_code == 200
        
        retrieve_data = retrieve_response.json()
        assert len(retrieve_data["assets"]) > 0
        assert retrieve_data["assets"][0]["type"] == "images"
        
    finally:
        if os.path.exists(dummy_file_path):
            os.remove(dummy_file_path)