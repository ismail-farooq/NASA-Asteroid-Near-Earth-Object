import sqlite3

conn = sqlite3.connect("asteroids.db")
c = conn.cursor()

c.execute('''
CREATE TABLE IF NOT EXISTS asteroids (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    Absolute_Magnitude REAL,
    Est_Dia_In_Km_Min REAL,
    Est_Dia_In_Km_Max REAL,
    Relative_Velocity_Km_Per_Hr REAL,
    Miss_Dist_Kilometers REAL,
    Minimum_Orbit_Intersection REAL,
    Jupiter_Tisserand_Invariant REAL,
    Epoch_Osculation REAL,
    Eccentricity REAL,
    Semi_Major_Axis REAL,
    Inclination REAL,
    Asc_Node_Longitude REAL,
    Orbital_Period REAL,
    Perihelion_Distance REAL,
    Perihelion_Arg REAL,
    Aphelion_Dist REAL,
    Perihelion_Time REAL,
    Mean_Anomaly REAL,
    Mean_Motion REAL,
    Hazardous INTEGER
)
''')

c.execute('CREATE TABLE IF NOT EXISTS feature_ranges ( feature_name TEXT PRIMARY KEY, min_value REAL, max_value REAL )')

conn.commit()
conn.close()
