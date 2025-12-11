from flask import Flask, request, jsonify, render_template, session
import sqlite3
import pandas as pd
import joblib
from pathlib import Path
import random
import json
import random
from pathlib import Path
from transformers import GPT2LMHeadModel, GPT2Tokenizer
import torch


app = Flask(__name__)
app.secret_key = 'KEY' 


MODEL_PATH = Path(__file__).parent.parent / 'ML Models' 
DB_PATH1 = Path(__file__).parent.parent / 'Database' 

HAZARD_MODEL = MODEL_PATH / 'hazard_model.pkl'
SCALER_PATH = MODEL_PATH / 'scaler.pkl'

hazard_model = joblib.load(HAZARD_MODEL)
scaler = joblib.load(SCALER_PATH)

DB_PATH = DB_PATH1 / 'asteroids.db'

DB_PATH1 = Path(__file__).parent.parent / 'Database' 
DB_PATH = DB_PATH1 / 'asteroids.db'


def load_feature_ranges():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT feature_name, min_value, max_value FROM feature_ranges')
    rows = c.fetchall()
    conn.close()
    return {row[0]: (row[1], row[2]) for row in rows}

ranges = load_feature_ranges()

def generate_random_asteroid(ranges):
    return {col: round(random.uniform(min_val, max_val), 5) for col, (min_val, max_val) in ranges.items()}

def save_asteroid_to_db(asteroid, hazardous):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    columns = ', '.join(asteroid.keys()) + ', Hazardous'
    placeholders = ', '.join(['?'] * (len(asteroid) + 1))
    values = list(asteroid.values()) + [hazardous]
    c.execute(f'INSERT INTO asteroids ({columns}) VALUES ({placeholders})', values)
    conn.commit()
    conn.close()

# Load model
model_folder = Path(__file__).parent.parent / 'ML Models' / 'NLP Model'

model = GPT2LMHeadModel.from_pretrained(str(model_folder))
tokenizer = GPT2Tokenizer.from_pretrained(str(model_folder))

def generate_report(asteroid):
    prompt = (
        f"NEO report:\n"
        f"Semi-Major Axis: {asteroid['Semi_Major_Axis']} AU, "
        f"Eccentricity: {asteroid['Eccentricity']}, "
        f"Inclination: {asteroid['Inclination']} degrees, "
        f"Close Approach Distance: {asteroid['Miss_Dist_Kilometers']} km, "
        f"Hazardous: {asteroid['Hazardous']}.\n\n"
        "Scientific Summary:"
    )

    inputs = tokenizer.encode(prompt, return_tensors="pt")
    output = model.generate(
        inputs,
        max_length=250,
        temperature=0.7,
        no_repeat_ngram_size=3
    )
    return tokenizer.decode(output[0], skip_special_tokens=True)


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

#if __name__ == "__main__":
#    app.run(debug=True)
