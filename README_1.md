# Multimodal Construction Intelligence Platform

Streamlit app: PPE/safety audit, crack diagnostics, cost & real-estate valuation (INR), weather-aware site assistant.

## Tech stack
Python 3.9+, Streamlit, Pillow, Google Gemini (multimodal), JSON data contracts.

## Features
- Safety & PPE audit with hazard severity and downloadable JSON report
- Crack classification with width, causes, repairs, urgency
- Budget, capex, valuation, cement/steel estimates, concept rendering
- Weather advisories and an engineering chatbot
- Demo mode when no API key is provided

## Run locally
    pip install -r requirements.txt
    streamlit run app.py

Paste a Gemini API key in the sidebar for live analysis (never commit keys).
