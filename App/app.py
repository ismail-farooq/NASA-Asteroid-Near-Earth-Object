from flask import Flask, request, jsonify, render_template, session
import sqlite3
import pandas as pd
import joblib
from pathlib import Path
import random
import json
from functions import load_feature_ranges, generate_random_asteroid, save_asteroid_to_db, generate_report

app = Flask(__name__)
app.secret_key = 'KEY' 


MODEL_PATH = Path(__file__).parent.parent / 'ML Models' 
DB_PATH1 = Path(__file__).parent.parent / 'Database' 

HAZARD_MODEL = MODEL_PATH / 'hazard_model.pkl'
SCALER_PATH = MODEL_PATH / 'scaler.pkl'

hazard_model = joblib.load(HAZARD_MODEL)
scaler = joblib.load(SCALER_PATH)

DB_PATH = DB_PATH1 / 'asteroids.db'

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        # Generate random asteroid
        ranges = load_feature_ranges()
        asteroid = generate_random_asteroid(ranges)
        df = pd.DataFrame([asteroid])
        df_scaled = scaler.transform(df)
        prediction = hazard_model.predict(df_scaled)[0]

        confidence = hazard_model.predict_proba(df_scaled)[0]

        asteroid['Hazardous'] = int(prediction)
        asteroid_json = json.dumps(asteroid)
        session['current_asteroid'] = asteroid

        save_asteroid_to_db(asteroid, prediction)
        report = generate_report(asteroid)
        return render_template("index.html", asteroid=asteroid, prediction=prediction, asteroid_json=asteroid_json, confidence=confidence, report=report, submitted=True)

    return render_template("index.html", submitted=False)

@app.route('/orbit')
def orbit():
    return render_template('orbit.html')

@app.route('/api/asteroid')
def api_asteroid():
    if 'current_asteroid' in session:
        asteroid = session['current_asteroid']
    
    return jsonify(asteroid)

if __name__ == "__main__":
    app.run(debug=True)
