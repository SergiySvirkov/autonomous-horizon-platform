# mlops/api/test_main.py

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

# We need to import the 'app' instance from our main API file
from .main import app

# This creates a client that can be used to make requests to the FastAPI app
client = TestClient(app)

@pytest.fixture
def mock_mlflow_model():
    """
    This is a pytest fixture that mocks the MLflow model loading.
    It replaces `mlflow.pyfunc.load_model` with a mock object for the duration of a test.
    """
    # Create a mock object that simulates the behavior of a loaded MLflow model.
    # The mock's `predict` method will return a fixed value.
    mock_model = MagicMock()
    mock_model.predict.return_value = [1]  # Simulate a prediction result of class '1'

    # The 'patch' context manager replaces the target object for the duration of the 'with' block.
    # Here, we replace the `load_model` function in the `main` module.
    with patch('mlops.api.main.mlflow.pyfunc.load_model', return_value=mock_model) as mock_loader:
        # 'yield' passes the mock object to the test function.
        yield mock_loader

def test_read_root():
    """
    Tests the root endpoint ('/') to ensure the API is running.
    """
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "message": "MLOps API is running."}

def test_predict_endpoint_success(mock_mlflow_model):
    """
    Tests a successful prediction request to the '/predict' endpoint.
    This test uses the 'mock_mlflow_model' fixture.
    """
    # Define valid input data for the model (10 features).
    test_payload = {
        "features": [[1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0]]
    }
    
    response = client.post("/predict", json=test_payload)
    
    assert response.status_code == 200
    # The response should match the return value of our mocked model's predict method.
    assert response.json() == {"predictions": [1]}

def test_predict_endpoint_validation_error():
    """
    Tests the '/predict' endpoint with invalid input data to check for validation errors.
    """
    # This payload is invalid because it's not a list of lists.
    invalid_payload = {"features": [1, 2, 3]}
    
    response = client.post("/predict", json=invalid_payload)
    
    # FastAPI should return a 422 Unprocessable Entity error for Pydantic validation failures.
    assert response.status_code == 422

def test_predict_endpoint_model_not_loaded():
    """
    Tests the API's behavior when the model fails to load.
    """
    # We patch the 'model' variable in the 'main' module to be None.
    with patch('mlops.api.main.model', None):
        test_payload = {
            "features": [[1.0] * 10]
        }
        response = client.post("/predict", json=test_payload)
        
        # The API should return a 503 Service Unavailable error.
        assert response.status_code == 503
        assert "Model is not available" in response.json()["detail"]

