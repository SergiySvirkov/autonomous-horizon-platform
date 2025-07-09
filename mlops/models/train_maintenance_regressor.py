# mlops/models/train_maintenance_regressor.py

import mlflow
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.datasets import make_regression
from sklearn.metrics import mean_absolute_error, r2_score
import warnings

warnings.filterwarnings("ignore")

print("Starting the predictive maintenance training script...")

# Set a new experiment name for this model type
mlflow.set_experiment("PredictiveMaintenance")

with mlflow.start_run() as run:
    run_id = run.info.run_id
    print(f"MLflow run started with ID: {run_id}")

    # Generate synthetic data representing sensor readings and time to failure.
    # Features could be things like: total_mileage, avg_vibration, engine_temp, etc.
    X, y = make_regression(
        n_samples=2000, 
        n_features=15, 
        n_informative=10, 
        noise=2.5,
        random_state=42
    )
    # The target 'y' represents 'days_until_failure'. We make it positive.
    y = np.abs(y) 
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    print("Successfully generated synthetic maintenance data.")

    # Define model parameters for the RandomForestRegressor
    params = {
        "n_estimators": 150,
        "max_depth": 10,
        "min_samples_leaf": 5,
        "random_state": 42
    }
    mlflow.log_params(params)
    print(f"Logged parameters: {params}")

    # Train the regression model
    rfr = RandomForestRegressor(**params)
    rfr.fit(X_train, y_train)
    print("Model training completed.")

    # Evaluate the model using regression metrics
    y_pred = rfr.predict(X_test)
    mae = mean_absolute_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)
    
    metrics = {"mean_absolute_error": mae, "r2_score": r2}
    mlflow.log_metrics(metrics)
    print(f"Model Metrics: {metrics}")

    # Log the trained model
    mlflow.sklearn.log_model(
        sk_model=rfr,
        artifact_path="model",
        # Register the model in the MLflow Model Registry for better version management
        registered_model_name="PredictiveMaintenanceModel"
    )
    print("Model successfully logged and registered in MLflow.")
    print("-" * 50)
    print(f"To view this run, use the command: mlflow ui")
    print(f"Run ID for this training session is: {run_id}")
    print("-" * 50)

print("Training script finished.")
