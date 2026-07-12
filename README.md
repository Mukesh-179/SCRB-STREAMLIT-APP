# 🚔 SCRB Crime Intelligence & Analytics Platform

An AI-powered crime analytics platform built with **Python**, **Streamlit**, and **Machine Learning** to analyze crime data, identify hotspots, detect anomalies, forecast crime trends, and generate actionable intelligence through an interactive dashboard.

## ✨ Features

- 📊 Crime Trend Analysis
- 🗺️ Geospatial Hotspot Detection
- 🤖 ML Anomaly Detection (Isolation Forest)
- 📈 Crime Forecasting
- 🎯 Hotspot Clustering (K-Means)
- 🔗 Network & Link Analysis
- 📋 Data Quality & Duplicate Detection
- 📂 Custom Dataset Upload & Analysis
- 📑 PDF, Excel & CSV Report Generation
- 📊 KPI Dashboard

## 🛠️ Tech Stack

- Python
- Streamlit
- Pandas
- NumPy
- Scikit-learn
- Plotly
- NetworkX
- OpenPyXL
- ReportLab

---

## 🚀 Installation

```bash
# Clone the repository
git clone https://github.com/Mukesh-179/SCRB-STREAMLIT-APP.git

# Navigate to project
cd SCRB-STREAMLIT-APP

# Install dependencies
pip install -r requirements.txt
```

---

## ▶️ Run the Application

### Using Streamlit

```bash
streamlit run app.py
```

### Or

```bash
python -m streamlit run app.py
```

---

## 🌐 Default URLs

After running the application, Streamlit starts on:

**Local URL**

```
http://localhost:8501
```

**Network URL**

```
http://<your-local-ip>:8501
```

If port **8501** is already in use:

```bash
streamlit run app.py --server.port 8502
```

or

```bash
streamlit run app.py --server.port 8503
```

---

## 📂 Supported Dataset

Required columns:

- Complaint Number
- Major Crime Head
- Crime Head and Section
- Minor Crime Head
- Commits
- Month

---

## 📸 Screenshots

_Add dashboard screenshots here._

---

## 👨‍💻 Developer

**Mukesh Vemuri**

GitHub: https://github.com/Mukesh-179

---

⭐ **If you found this project useful, consider giving it a Star!**
