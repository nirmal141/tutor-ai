import requests

def test_health_check():
    """Test the health endpoint of the local LLM server."""
    api_base = "http://127.0.0.1:1234"
    response = requests.get(f"{api_base}/health", timeout=2)
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "timestamp" in data