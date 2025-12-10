import sqlite3
import random
from pathlib import Path
from transformers import GPT2LMHeadModel, GPT2Tokenizer
import torch

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
model_folder = "NLP Model"

model = GPT2LMHeadModel.from_pretrained(str(model_folder))
tokenizer = GPT2Tokenizer.from_pretrained(str(model_folder))

def generate_report(asteroid):
    prompt = (
        f"Write a concise scientific report for the following Near-Earth Object (NEO):\n\n"
        f"Semi-Major Axis: {asteroid['Semi_Major_Axis']} AU\n"
        f"Eccentricity: {asteroid['Eccentricity']}\n"
        f"Inclination: {asteroid['Inclination']} degrees\n"
        f"Miss Distance: {asteroid['Miss_Dist_Kilometers']} km\n"
        f"Absolute Magnitude: {asteroid['Absolute_Magnitude']}\n"
        f"Estimated Diameter: {asteroid['Est_Dia_In_Km_Min']} - {asteroid['Est_Dia_In_Km_Max']} km\n"
        f"Relative Velocity: {asteroid['Relative_Velocity_Km_Per_Hr']} km/hr\n"
        f"Hazardous: {'Yes' if asteroid['Hazardous'] else 'No'}\n\n"
        "Use the following sections: Overview, Orbital Characteristics, Physical Characteristics, Hazard Assessment, Summary.\n"
        "Write only about this asteroid, do not mention the PDF, NASA report, or appendices.\n"
        "Use complete sentences and scientific units."
    )
    inputs = tokenizer.encode(prompt, return_tensors="pt")
    output = model.generate(
        inputs,
        max_length=512,
        temperature=0.7,
        no_repeat_ngram_size=4,
        pad_token_id=tokenizer.eos_token_id
    )
    return tokenizer.decode(output[0], skip_special_tokens=True)

