# ☄️ NASA Near Earth Object (NEO) Data Analysis

<h3 align="center">CS210 - Data Management for Data Science Project</h3>

This project analyzes NASA's Near Earth Object (NEO) dataset to understand asteroid characteristics, orbital patterns, and potential hazards. The workflow includes data cleaning, normalization, feature selection, and preparation for further machine learning or statistical modeling.

---

## 🚀 Project Overview

The goal of this project is to:
- Clean and preprocess NASA’s asteroid dataset
- Normalize column names and handle missing values
- Drop redundant or irrelevant columns
- Prepare data for **linear algebra operations**, **statistical analysis**, and **ML modeling**
- Identify relationships between asteroid features and potential hazard status

---

## 🧰 Technologies & Tools Used

| Category | Tools |
|-----------|-------|
| **Language** | Python 🐍 |
| **Libraries** | Pandas, NumPy, Pathlib, re |
| **Visualization (optional)** | Matplotlib, Seaborn |
| **Environment** | Jupyter Notebook / VS Code |

---

## 🧠 Key Steps in the Notebook

### 1. Import Required Libraries  
```python
import pandas as pd
from pathlib import Path
import re
