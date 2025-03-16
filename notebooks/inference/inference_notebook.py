# Databricks notebook source
# %pip install mlflow>=2.10.1 scikit-learn>=1.3.0 pandas>=2.0.0

# COMMAND ----------

import mlflow
import pandas as pd
import numpy as np
from sklearn.datasets import load_iris
from datetime import datetime

# COMMAND ----------
# Load model
model = mlflow.pyfunc.load_model("models:/prod_catalog.ml_models.iris_model@production")

# COMMAND ----------
# Generate inference data
iris = load_iris()
inference_data = pd.DataFrame(iris.data[:100], columns=iris.feature_names)

# COMMAND ----------
# Schema validation
expected_schema = {
    'sepal length (cm)': 'float64',
    'sepal width (cm)': 'float64', 
    'petal length (cm)': 'float64',
    'petal width (cm)': 'float64'
}

if inference_data.dtypes.astype(str).to_dict() != expected_schema:
    dbutils.notebook.exit("Schema validation failed")

# COMMAND ----------
# Predictions
predictions = model.predict(inference_data)
inference_data['prediction'] = predictions

# COMMAND ----------
# Save results
date_str = datetime.today().strftime("%Y-%m-%d")
output_path = f"/Volumes/prod_catalog/ml_models/inference_results/{date_str}/predictions.csv"
inference_data.to_csv(output_path, index=False)