from flask import Flask, request, jsonify, render_template, session
import pandas as pd
import joblib
from pathlib import Path
import random
import json
import os
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "RAG"))
from rag_pipeline import get_pipeline
from huggingface_hub import hf_hub_download

app = Flask(__name__)
app.secret_key = 'KEY' 

os.environ["HF_HOME"] = "/tmp/hf"
os.environ["HUGGINGFACE_HUB_CACHE"] = "/tmp/hf"
os.environ["TRANSFORMERS_CACHE"] = "/tmp/hf"
def load_model1():
    return hf_hub_download(
        repo_id="HollowWinter429/hazard_model",
        filename="hazard_model.pkl",
        cache_dir="/tmp/hf"
    )

def load_model2():
    return hf_hub_download(
        repo_id="HollowWinter429/hazard_model",
        filename="scaler.pkl",
        cache_dir="/tmp/hf"
    )

hazard_path = load_model1()
scaler_path = load_model2()

hazard_model = joblib.load(hazard_path)
scaler = joblib.load(scaler_path)

# DB_PATH1 = Path(__file__).parent.parent / 'Database' 
# DB_PATH = DB_PATH1 / 'asteroids.db'


def load_feature_ranges():
    return {
        "Absolute_Magnitude": [13.92, 13.92],
        "Est_Dia_In_Km_Min": [0.0048367649, 0.0048367649],
        "Est_Dia_In_Km_Max": [0.0108153351, 0.0108153351],
        "Relative_Velocity_Km_Per_Hr": [943.3321928485, 943.3321928485],
        "Miss_Dist_Kilometers": [0.00166, 0.00166],
        "Minimum_Orbit_Intersection": [0.00000206111, 0.00000206111],
        "Jupiter_Tisserand_Invariant": [2.4, 2.4],
        "Epoch_Osculation": [2453496.5, 2453496.5],
        "Eccentricity": [0.00752235509936797, 0.00752235509936797],
        "Semi_Major_Axis": [0.7321056673857965, 0.7321056673857965],
        "Inclination": [0.01451294322958202, 0.01451294322958202],
        "Asc_Node_Longitude": [0.00194067415759618, 0.00194067415759618],
        "Orbital_Period": [228.8016121087175, 228.8016121087175],
        "Perihelion_Distance": [0.08074429595890999, 0.08074429595890999],
        "Perihelion_Arg": [0.0069176245736902, 0.0069176245736902],
        "Aphelion_Dist": [0.8940436043120773, 0.8940436043120773],
        "Perihelion_Time": [2453535.0605106894, 2453535.0605106894],
        "Mean_Anomaly": [0.0031914911023824, 0.0031914911023824],
        "Mean_Motion": [0.1638053948608621, 0.1638053948608621]
    }
ranges = load_feature_ranges()

def generate_random_asteroid(ranges):
    return {col: round(random.uniform(min_val, max_val), 5) for col, (min_val, max_val) in ranges.items()}

# def save_asteroid_to_db(asteroid, hazardous):
#     conn = sqlite3.connect(DB_PATH)
#     c = conn.cursor()
#     columns = ', '.join(asteroid.keys()) + ', Hazardous'
#     placeholders = ', '.join(['?'] * (len(asteroid) + 1))
#     values = list(asteroid.values()) + [hazardous]
#     c.execute(f'INSERT INTO asteroids ({columns}) VALUES ({placeholders})', values)
#     conn.commit()
#     conn.close()

# Load model
#model = GPT2LMHeadModel.from_pretrained(str(model_folder))
#tokenizer = GPT2Tokenizer.from_pretrained(str(model_folder))

# def generate_report(asteroid):
#     prompt = (
#         f"NEO report:\n"
#         f"Semi-Major Axis: {asteroid['Semi_Major_Axis']} AU, "
#         f"Eccentricity: {asteroid['Eccentricity']}, "
#         f"Inclination: {asteroid['Inclination']} degrees, "
#         f"Close Approach Distance: {asteroid['Miss_Dist_Kilometers']} km, "
#         f"Hazardous: {asteroid['Hazardous']}.\n\n"
#         "Scientific Summary:"
#     )

#     inputs = tokenizer.encode(prompt, return_tensors="pt")
#     output = model.generate(
#         inputs,
#         max_length=250,
#         temperature=0.7,
#         no_repeat_ngram_size=3
#     )
#     return tokenizer.decode(output[0], skip_special_tokens=True)


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

        # save_asteroid_to_db(asteroid, prediction)
        #report = generate_report(asteroid)
        return render_template("index.html", asteroid=asteroid, prediction=prediction, asteroid_json=asteroid_json, confidence=confidence, submitted=True)

    return render_template("index.html", submitted=False)

@app.route('/orbit')
def orbit():
    return render_template('orbit.html')

@app.route('/api/asteroid')
def api_asteroid():
    if 'current_asteroid' in session:
        asteroid = session['current_asteroid']
    
    return jsonify(asteroid)

@app.route("/chat")
def chat():
    """Renders the RAG chat UI."""
    return render_template("chat.html")
 
 
# ── Route: RAG API endpoint (called by chat.html via fetch) ───────────────────
@app.route("/api/rag", methods=["POST"])
def rag_query():
    """
    POST JSON: { "question": str }
    Optionally injects the current session asteroid as context.
 
    Returns JSON:
    {
      "answer":  str,
      "sources": [{ "chunk_index": int, "distance": float, "preview": str }],
      "model":   str
    }
    """
    data = request.get_json(force=True)
    question = (data.get("question") or "").strip()
 
    if not question:
        return jsonify({"error": "No question provided."}), 400
 
    # Pull current asteroid from session if one exists
    asteroid_context = session.get("current_asteroid")
 
    try:
        pipeline = get_pipeline()
        result   = pipeline.ask(question, asteroid_context=asteroid_context)
        return jsonify(result)
    except FileNotFoundError as e:
        return jsonify({"error": str(e)}), 503
    except Exception as e:
        return jsonify({"error": f"RAG error: {e}"}), 500

@app.route("/api/generate", methods=["POST"])
def api_generate():
    """
    Returns JSON with asteroid data, prediction, confidence, and report.
    Called by the frontend JS instead of POSTing to '/'.
    """
    ranges = load_feature_ranges()
    asteroid = generate_random_asteroid(ranges)
    df = pd.DataFrame([asteroid])
    df_scaled = scaler.transform(df)
    prediction = int(hazard_model.predict(df_scaled)[0])
    confidence = hazard_model.predict_proba(df_scaled)[0].tolist()
 
    asteroid['Hazardous'] = prediction
    session['current_asteroid'] = asteroid
 
    # save_asteroid_to_db(asteroid, prediction)
    #report = generate_report(asteroid)
 
    return jsonify({
        **asteroid,
        "prediction": prediction,
        "confidence": confidence[prediction],
    })
 

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
