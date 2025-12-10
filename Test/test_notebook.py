import pytest
import joblib
import numpy as np
from pathlib import Path

CWD = Path(__file__).parent / '..'

MODEL_DIR = CWD / 'Model'

nasa_csv = MODEL_DIR / 'hazard_model.pkl'


model_output_path = MODEL_DIR / 'hazard_model.pkl'
scaler_output_path = MODEL_DIR / 'scaler.pkl'

model = joblib.load(model_output_path)
scaler = joblib.load(scaler_output_path)

def test_model_prediction_shape():
    arr = np.random.rand(1, 19)
    arr_scaled = scaler.transform(arr)
    y_pred = model.predict(arr_scaled)
    
    assert y_pred.shape == (1,)

def test_prediction_is_binary():
    arr = np.random.rand(1, 19)
    arr_scaled = scaler.transform(arr)
    y_pred = model.predict(arr_scaled)
    assert y_pred[0] in [0, 1], "Model output not binary"

def test_scaler_consistency():
    arr = np.random.rand(5, 19)
    scaled = scaler.transform(arr)
    assert scaled.shape == (5, 19), "Scaler output shape mismatch"
