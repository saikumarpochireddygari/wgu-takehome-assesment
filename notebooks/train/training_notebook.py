# Databricks notebook source
# COMMAND ----------
# %pip install mlflow>=2.10.1 scikit-learn>=1.3.0 pandas>=2.0.0 typing_extensions

# COMMAND ----------
dbutils.library.restartPython()

# COMMAND ----------
import mlflow
import pandas as pd
import numpy as np
from sklearn.datasets import load_iris
from sklearn.ensemble import RandomForestClassifier
from mlflow.models.signature import infer_signature

# COMMAND ----------
# Load data
iris = load_iris()
data = pd.DataFrame(np.c_[iris.data, iris.target], 
                   columns=iris.feature_names + ['target'])

# COMMAND ----------
# Prepare training data
train_data = data.sample(100, random_state=42)
X_train = train_data[iris.feature_names]
y_train = train_data['target']

# COMMAND ----------
experiment_name = "/Shared/production-iris-exp"

# Check if the experiment exists
experiment = mlflow.get_experiment_by_name(experiment_name)

if experiment is None:
    # Create the experiment if it does not exist
    experiment_id = mlflow.create_experiment(experiment_name)
else:
    experiment_id = experiment.experiment_id

# Set the experiment
mlflow.set_experiment(experiment_name)
mlflow.set_registry_uri("databricks-uc")

# COMMAND ----------
# Train model
model = RandomForestClassifier(n_estimators=100, max_depth=5, random_state=42)
model.fit(X_train, y_train)

# COMMAND ----------
# MLflow logging
with mlflow.start_run():
    # Log parameters
    mlflow.log_params({
        "n_estimators": 100,
        "max_depth": 5,
        "random_state": 42
    })
    
    # Log metrics
    mlflow.log_metric("training_accuracy", model.score(X_train, y_train))
    
    # Log model
    signature = infer_signature(X_train, model.predict(X_train))
    input_example = X_train.iloc[:5]
    
    mlflow.sklearn.log_model(
        sk_model=model,
        artifact_path="iris-model",
        signature=signature,
        input_example=input_example,
        registered_model_name="prod_catalog.ml_models.iris_model"
    )
    
    # Set production alias
    client = mlflow.MlflowClient()
    latest_version = client.get_latest_versions(
        "prod_catalog.ml_models.iris_model", 
        stages=["None"]
    )[0].version
    client.set_registered_model_alias(
        "prod_catalog.ml_models.iris_model",
        "production",
        latest_version
    )