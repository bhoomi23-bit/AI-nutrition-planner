# 🥗 AI Nutrition Planner

A Streamlit-based web application that generates personalized nutrition
recommendations and AI-powered daily meal plans based on a user's health
profile, dietary preferences, and allergies.

Built as a group project combining health metric calculations, a machine
learning food recommendation model, and a generative AI meal planner.

---

## ✨ Features

- **User Accounts** — sign up / log in with hashed password storage (SQLite)
- **Health Profile** — collects age, height, weight, activity level, dietary
  preference, fitness goal, and allergies
- **Health Analysis** — calculates BMI, BMR, TDEE, and daily macro targets
  (calories, protein, carbs, fat)
- **Food Recommendation (ML)** — a Random Forest model scores foods from a
  nutrition dataset to build a preferred food pool
- **AI Meal Planning** — sends the user's targets and recommended foods to
  the **Google Gemini API**, which generates a structured daily meal plan
  (breakfast/lunch/snacks/dinner) as JSON
- **Persistent Storage** — meal plans and profiles are saved to a local
  SQLite database and viewable under "Previous Plans"
- **Graceful Fallback** — if the AI API is unavailable (rate limit, network,
  missing key), the app automatically builds a simple plan directly from the
  recommended foods instead of failing

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Frontend / App | [Streamlit](https://streamlit.io) |
| Health calculations | Python (BMI, BMR, TDEE formulas) |
| Food recommendation | scikit-learn `RandomForestRegressor` |
| AI meal generation | [Google Gemini API](https://ai.google.dev) (`google-genai` SDK) |
| Database | SQLite |
| Config | `python-dotenv` |

---

## 📂 Project Structure

```
AI-nutrition-planner/
│
├── main.py                    # Streamlit app entry point (run this) — all pages
├── ai_meal_planner.py         # Gemini AI integration — generates meal plans
├── database.py                # SQLite layer: users, profiles, meal plans
├── train_model.py             # Trains the Random Forest food-scoring model
├── test_meal_planner.py       # Standalone test for the AI meal planner
├── nutrition_dataset.csv      # Food/nutrient dataset used for training
├── nutrition_health_model.pkl # Trained Random Forest model
├── requirements.txt
├── .gitignore
├── .env                       # API keys (NOT committed — see below)
├── app.py                     # (currently unused placeholder — not the entry point)
└── README.md
```

> **Note:** run the app with `streamlit run main.py`, not `app.py` — the
> latter is currently an empty placeholder left over from initial setup.

---

## 🚀 Getting Started

### 1. Clone the repo
```bash
git clone https://github.com/bhoomi23-bit/AI-nutrition-planner.git
cd AI-nutrition-planner
```

### 2. Create a virtual environment and install dependencies
```bash
python -m venv .venv
.venv\Scripts\Activate.ps1      # Windows PowerShell
# source .venv/bin/activate      # macOS/Linux

pip install -r requirements.txt
```

### 3. Add your Gemini API key
Get a free key from [Google AI Studio](https://aistudio.google.com/app/apikey),
then create a `.env` file in the project root:
```
GEMINI_API_KEY=your_key_here
```
> ⚠️ `.env` is git-ignored and should never be committed. If deploying on
> Streamlit Community Cloud, add this key under **Settings → Secrets** instead.

### 4. (Optional) Train the food recommendation model
```bash
python train_model.py
```
This generates `nutrition_health_model.pkl` from `nutrition_dataset.csv`.

### 5. Run the app
```bash
streamlit run main.py
```

---

## 🧪 Testing the AI Integration Standalone

Before running the full app, you can test the meal planner module on its own:
```bash
python test_meal_planner.py
```
This checks that the API key loads, the Gemini API responds, and a valid
meal plan is returned and parsed.

---

## ⚠️ Disclaimer

This application is for **educational purposes only**. It does not provide
medical or professional dietary advice. Consult a qualified nutrition
professional or physician for personalized guidance.

---

## 👥 Contributors

- Health analysis, profile & UI
- Random Forest food recommendation model
- AI meal planning integration (Gemini) & app wiring
- Database & authentication

Hafsa - AI meal planning inetegration (Gemini) & app wiring

