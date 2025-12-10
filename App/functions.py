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

