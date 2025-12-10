# ☄️ NASA Near Earth Object (NEO) Hazard Prediction

<h3 align="center">CS210 - Data Science Project</h3>

This project analyzes NASA's Near Earth Object (NEO) dataset to understand asteroid characteristics and predict whether an asteroid is potentially hazardous. It uses **machine learning**, **SQLite**, and a **Flask web app** for interactive predictions.  

---

## 🚀 Project Goals

- Clean and preprocess NASA asteroid data  
- Analyze asteroid features and orbital patterns  
- Build a machine learning model to predict hazard status  
- Store asteroid data and feature ranges (min/max) in SQLite  
- Allow users to generate random asteroids and predict hazards  
- Visualize randomly generated asteroid orbits in 3D
- Allow the user to copy JSON values of their randomly generated asteroids and test it manually using `Test_Random_Data.ipynb` notebook 

---

## 🧰 Tools & Technologies

| Category | Tools |
|-----------|-------|
| Language | Python |
| Libraries | Pandas, NumPy, joblib, SQLite3, random |
| Machine Learning | scikit-learn |
| Web App | Flask |
| Visualization | Matplotlib, Seaborn, three.js |

---

## 🧠 Features

1. **Data Cleaning & Preprocessing**  
   - Handle missing values  
   - Normalize columns  
   - Drop irrelevant features  

2. **Machine Learning Model**  
   - Train a model to predict `Hazardous`  
   - Save model and scaler for later use  

3. **SQLite Database**  
   - Save min/max ranges for numeric features 
   - Store asteroid data and predictions for randomly generated data  


4. **Flask Web App**  
   - Generate random asteroids within realistic ranges  
   - Predict hazard status  
   - 3D orbit visualization  

5. **Jupyter Notebooks**  
   - Visualize real orbits from the dataset  
   - Test hazard status using the randomly generated asteroid data from `#4`

---

## 🧠 Project Structure
.env
.gitattributes
.gitignore
README.md
requirements.txt
push.txt
LICENSE

Database/
├── asteroids.db
└── model.py

Datasets/
├── European_Space_Agency_NEOs_Scraped_Data.csv
├── European_Space_Agency_NEO_Designations.csv
├── NASA_NEO_Dataset.csv
├── NASA_NEO_Data_API.csv
├── NLP/
│   ├── asteroids_wiki.txt
│   └── asteroids_wiki_cleaned.txt
└── Processed Datasets/
    └── NASA+EuropeanSpaceAgency_NEO_Data_Cleaned.csv

ML Models/
├── hazard_model.pkl
├── scaler.pkl
└── NLP Model/

Flask App/
├── app.py
├── functions.py
├── static/
└── templates/

MAIN Notebooks/
├── CS210main.ipynb
├── CS210_k_means_clustering.ipynb
├── CS210_nlp.ipynb
├── Secondary_Datasource_(SCRAPED).ipynb
└── Tertiary_Datasource_(API).ipynb

Extra Notebooks/
├── Orbit_Visualizer.ipynb
└── Test_Random_Data.ipynb

Test/
└── test_notebook.py


## ✅ How to Use 

(Built using `Python 3.13.9`, ensure `Python --version` > 3.10)

## Basis step:
```bash
git clone https://github.com/ismail-farooq/NASA-Asteroid-Near-Earth-Object.git
python -m venv .venv
pip install -r requirements.txt
``` 

---


### 1. Run the Notebook:
```bash
cd Notebooks/
code CS210.ipynb
```
and Run the file

### 2. Visualize random orbits from the real dataset:
```bash
cd Notebooks/
code Orbit_Visualizer.ipynb
```
and Run the file

### 3. Run the Flask app to randomly generate asteroid data and predict `Hazard` status:

```bash
cd App/
python app.py
```
open `http://127.0.0.1:5000`
and click `Generate Random Asteroid`

### 4. View your randomly generated asteroid:

```bash
cd App/
python app.py
```
open `http://127.0.0.1:5000`
and click `Generate Random Asteroid` 
then click `View Asteroid Orbit`

### 5. Test your randomly generated asteroid using the ML models yourself:

```bash
cd App/
python app.py
```
open `http://127.0.0.1:5000`
and click `Generate Random Asteroid` 
then click `Copy Asteroid Values JSON`
then go back to your code editor and then
```bash
cd ../Notebooks # go back a directory and into the Notebooks directory
code Test_Random_Data.ipynb
```
Paste in your JSON in the 2nd cell under the Blue markdown 
Run the notebook

