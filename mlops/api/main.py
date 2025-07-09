# mlops/api/main.py

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import mlflow
import numpy as np
import os

# --- Configuration ---
# For a prototype, we'll set the run ID directly.
# In a production system, this would be managed by a CI/CD pipeline,
# which would fetch the latest "production-ready" model from the MLflow Model Registry.
#
# IMPORTANT: Replace "<YOUR_RUN_ID>" with the actual run_id from your training script output.
RUN_ID = os.environ.get("MLFLOW_RUN_ID", "<YOUR_RUN_ID>") 
MODEL_ARTIFACT_PATH = "model"
MLFLOW_TRACKING_URI = os.environ.get("MLFLOW_TRACKING_URI", "mlruns") # Assumes local `mlruns` directory

# --- Pydantic Model for Input Validation ---
# This ensures that the data sent to the /predict endpoint has the correct structure.
# Our model expects 10 features.
class PredictionInput(BaseModel):
    features: list[list[float]]

# --- FastAPI Application ---
app = FastAPI(
    title="Autonomous Vehicle Classifier API",
    description="An API to serve predictions from an MLflow-trained model.",
    version="0.1.0"
)

# --- Model Loading ---
# We load the model once when the application starts.
try:
    # Construct the full model URI
    logged_model_uri = f'runs:/{RUN_ID}/{MODEL_ARTIFACT_PATH}'
    print(f"Loading model from: {logged_model_uri}")
    
    # Set the tracking URI for MLflow
    mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
    
    # Load the model using MLflow's pyfunc loader
    model = mlflow.pyfunc.load_model(logged_model_uri)
    print("Model loaded successfully.")
except Exception as e:
    print(f"Error loading the model: {e}")
    # If the model fails to load, we assign None and the API will return an error.
    model = None
    
# --- API Endpoints ---
@app.get("/")
def read_root():
    """A simple endpoint to check if the API is running."""
    return {"status": "ok", "message": "MLOps API is running."}

@app.post("/predict")
async def predict(input_data: PredictionInput):
    """
    Endpoint to get predictions from the model.
    
    - **input_data**: A JSON object with a 'features' key.
      'features' should be a list of lists (e.g., [[feature1, feature2, ...], ...]).
    """
    if model is None:
        raise HTTPException(
            status_code=503, 
            detail="Model is not available. Please check the server logs."
        )

    try:
        # Convert the input list to a NumPy array for the model
        features_array = np.array(input_data.features)
        
        # Get predictions
        predictions = model.predict(features_array)
        
        # Return predictions in a JSON-friendly format
        return {"predictions": predictions.tolist()}
    except Exception as e:
        raise HTTPException(
            status_code=400, 
            detail=f"Error during prediction: {str(e)}"
        )

