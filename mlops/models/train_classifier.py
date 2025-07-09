# mlops/models/train_classifier.py

import mlflow
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.datasets import make_classification
from sklearn.metrics import accuracy_score
import warnings

# Suppress warnings for a cleaner output
warnings.filterwarnings("ignore")

print("Starting the training script...")

# 1. Set the experiment name in MLflow. 
# If the experiment does not exist, MLflow will create it.
try:
    mlflow.set_experiment("AutonomousVehicleClassifier")
    print("MLflow experiment set to 'AutonomousVehicleClassifier'")
except Exception as e:
    print(f"Could not set MLflow experiment. Error: {e}")
    exit()

# 2. Start an MLflow run. All the tracking will be recorded under this run.
# The 'with' statement ensures that the run is properly closed.
with mlflow.start_run() as run:
    run_id = run.info.run_id
    print(f"MLflow run started with ID: {run_id}")

    # 3. Generate synthetic data for prototyping using scikit-learn.
    # In a real-world scenario, you would load data from a CSV, database, or data lake.
    X, y = make_classification(
        n_samples=1000, 
        n_features=10, 
        n_informative=5, 
        n_redundant=0, 
        random_state=42
    )
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    print("Successfully generated and split synthetic data.")

    # 4. Define model parameters and log them.
    # Logging parameters is crucial for reproducibility.
    params = {
        "solver": "lbfgs", 
        "random_state": 42,
        "max_iter": 200
    }
    mlflow.log_params(params)
    print(f"Logged parameters: {params}")

    # 5. Train the model.
    # We use a simple Logistic Regression model for this prototype.
    lr = LogisticRegression(**params)
    lr.fit(X_train, y_train)
    print("Model training completed.")

    # 6. Evaluate the model and log metrics.
    # Metrics help in comparing different model versions.
    y_pred = lr.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    mlflow.log_metric("accuracy", accuracy)
    print(f"Model accuracy: {accuracy:.4f}")

    # 7. Log the trained model as an artifact.
    # This saves the model in a format that MLflow can understand and serve.
    # The 'artifact_path' is the name of the directory where the model will be saved within the run's artifacts.
    mlflow.sklearn.log_model(
        sk_model=lr,
        artifact_path="model"
    )
    print("Model successfully logged to MLflow.")
    print("-" * 50)
    print(f"To view this run, use the command: mlflow ui")
    print(f"Run ID for this training session is: {run_id}")
    print("-" * 50)

print("Training script finished.")
