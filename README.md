# 📈 U.S. Treasury Yield Curve Dashboard

An interactive, academic-grade Streamlit dashboard that explores U.S. Treasury bond yields from 2000–2024, built as a university data visualization project.

---

## 🎯 Project Overview

The U.S. Treasury yield curve is one of the most-watched economic indicators in finance. This dashboard brings it to life with interactive Plotly charts, recession overlays, and animated monthly snapshots — all powered by official Treasury Department data.

**Key features:**
- 🌊 Animated yield curve with date picker and preset snapshots
- 📉 Historical yield trends with maturity filtering and smoothing
- 🔀 10Y–2Y / 10Y–3M spread analysis with recession indicators
- 🔥 Heatmap of annual yields and year-over-year changes
- Real-time KPI metrics for key maturities
- Clean dark-theme UI with student-friendly explanations

---

## 🗂️ Project Structure

```
treasury_yield_dashboard/
│
├── app.py                  # Main Streamlit application
├── requirements.txt        # Python dependencies
├── README.md               # This file
│
├── data/
│   ├── fetch_data.py       # Data loading module (live + synthetic fallback)
│   └── yields.parquet      # Cached yield data (auto-generated on first run)
│
└── assets/                 # Static assets (screenshots, diagrams)
```

---

## ⚙️ Setup Instructions

### Prerequisites
- Python 3.10 or higher
- pip (comes with Python)

### 1. Clone the repository
```bash
git clone https://github.com/zongfrank0802/Final-project-dashboard-for-treasury-yield-data-visualization
cd Final-project-dashboard-for-treasury-yield-data-visualization
```

### 2. Create and activate a virtual environment (recommended)
```bash
# macOS / Linux
python3 -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
venv\Scripts\activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Run the dashboard
```bash
streamlit run app.py
```

The app will open automatically at **http://localhost:8501**

---

## 📊 Data Source

| Detail | Info |
|--------|------|
| **Provider** | U.S. Department of the Treasury |
| **Dataset** | Daily Treasury Par Yield Curve Rates |
| **URL** | https://home.treasury.gov/resource-center/data-chart-center/interest-rates/ |
| **Format** | XML feed (parsed in `data/fetch_data.py`) |
| **Fallback** | Realistic synthetic data (auto-activates if the live feed is blocked) |
| **Coverage** | 2000–2024, business days only |
| **Maturities** | 1M, 2M, 3M, 6M, 1Y, 2Y, 3Y, 5Y, 7Y, 10Y, 20Y, 30Y |

The data is cached locally as `data/yields.parquet` after the first fetch to speed up subsequent runs.

---

## 📈 Visualizations

### 1. Yield Curve Snapshot + Animation (Tab 1)
- Select any date and see the yield curve for that day
- Compare multiple dates side-by-side
- Quick presets: Pre-GFC, Post-GFC, COVID, Rate Hike Peak
- Animated monthly timeline with Plotly animation controls

### 2. Historical Yield Trends (Tab 2)
- Multi-maturity line chart with a range slider
- Rolling-average smoothing (5d, 10d, 21d, 63d)
- NBER recession bands (2001, 2008–09, 2020)
- Summary statistics table

### 3. Spread Analysis (Tab 3)
- 10Y–2Y and 10Y–3M spreads with inversion shading
- Current signal: inverted vs. normal + percentile rank
- Inversion depth bar chart

### 4. Heatmap (Tab 4)
- Average annual yields by maturity (colour-coded)
- Year-over-year change heatmap

---

## 🚀 Deployment

### Streamlit Community Cloud (free, recommended for academic submission)
1. Push the project to a public GitHub repo
2. Go to https://share.streamlit.io
3. Connect your GitHub account
4. Select the repo and set **Main file path** to `app.py`
5. Click **Deploy** — you'll get a public URL in ~2 minutes

### Docker (optional)
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
EXPOSE 8501
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

```bash
docker build -t yield-dashboard .
docker run -p 8501:8501 yield-dashboard
```

---

## 🛠️ Tech Stack

| Library | Purpose |
|---------|---------|
| `streamlit` | Web app framework |
| `plotly` | Interactive charts (line, bar, heatmap, animation) |
| `pandas` | Data manipulation & resampling |
| `numpy` | Numerical computations |
| `requests` | HTTP calls to Treasury XML feed |
| `pyarrow` | Fast parquet file I/O |

---

## 🤝 AI Collaboration Statement

This project was developed with assistance from Claude (Anthropic), an AI assistant. Specifically, AI was used to:
- Generate boilerplate Streamlit layout and CSS styling patterns
- Suggest appropriate Plotly chart configurations for the yield-curve use case
- Draft initial docstrings and inline code comments

All economic interpretations, design decisions, visualization choices, and academic write-up content were reviewed, edited, and validated by the student author. The synthetic data generation algorithm was manually calibrated to reproduce documented real-world yield-curve behaviour (GFC inversion, COVID zero-rate period, 2022–23 hiking cycle). AI tools were used as a productivity aid, not as a replacement for understanding.

---

## 📚 References

1. U.S. Treasury. (2024). *Daily Treasury Par Yield Curve Rates*. https://home.treasury.gov
2. Federal Reserve Bank of San Francisco. (2018). *Information in the Yield Curve about Future Recessions*.
3. Mishkin, F. S. (1990). The Information in the Longer Maturity Term Structure about Future Inflation. *Quarterly Journal of Economics, 105*(3), 815–828.
4. Estrella, A., & Mishkin, F. S. (1998). Predicting U.S. Recessions: Financial Variables as Leading Indicators. *Review of Economics and Statistics, 80*(1), 45–61.

---

*Academic project — Data Visualization Course, Spring 2025*
