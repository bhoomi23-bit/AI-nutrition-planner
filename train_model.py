import os
import pandas as pd
import joblib

from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score


# ============================================================
# 1. LOAD DATASET
# ============================================================

DATASET_PATH = "nutrition_dataset.csv"
MODEL_PATH = "model/nutrition_health_model.pkl"

print("Loading dataset...")

df = pd.read_csv(DATASET_PATH)

print("Dataset loaded successfully!")
print("Rows:", df.shape[0])
print("Columns:", df.shape[1])


# ============================================================
# 2. SELECT FEATURES
# ============================================================

features = [
    "calories",
    "carbs_g",
    "calcium_mg",
    "fat_g",
    "protein_g",
    "saturated_fat_g",
    "vitamin_c_mg",
    "fiber_g",
    "iron_mg",
    "sodium_mg",
    "sugar_g",
    "cholesterol_mg"
]

target = "health_score"


# ============================================================
# 3. CHECK REQUIRED COLUMNS
# ============================================================

missing_columns = [
    column for column in features + [target]
    if column not in df.columns
]

if missing_columns:

    print("\nERROR!")
    print("The following columns are missing:")

    for column in missing_columns:
        print("-", column)

    exit()


# ============================================================
# 4. CREATE INPUT AND TARGET DATA
# ============================================================

X = df[features]

y = df[target]


# ============================================================
# 5. SPLIT DATASET
# ============================================================

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.20,
    random_state=42
)

print("\nTraining samples:", len(X_train))
print("Testing samples:", len(X_test))


# ============================================================
# 6. CREATE MACHINE LEARNING MODEL
# ============================================================

model = Pipeline([

    (
        "imputer",
        SimpleImputer(strategy="median")
    ),

    (
        "random_forest",
        RandomForestRegressor(
            n_estimators=250,
            random_state=42,
            n_jobs=-1,
            min_samples_leaf=2
        )
    )
])


# ============================================================
# 7. TRAIN MODEL
# ============================================================

print("\nTraining Random Forest model...")

model.fit(X_train, y_train)

print("Model training completed!")


# ============================================================
# 8. PREDICTIONS
# ============================================================

print("\nMaking predictions...")

y_pred = model.predict(X_test)


# ============================================================
# 9. MODEL EVALUATION
# ============================================================

mae = mean_absolute_error(
    y_test,
    y_pred
)

rmse = mean_squared_error(
    y_test,
    y_pred
) ** 0.5

r2 = r2_score(
    y_test,
    y_pred
)


print("\n================================")
print("       MODEL PERFORMANCE")
print("================================")

print("MAE  :", mae)
print("RMSE :", rmse)
print("R2   :", r2)


# ============================================================
# 10. SAVE MODEL
# ============================================================

os.makedirs("model", exist_ok=True)

joblib.dump(
    model,
    MODEL_PATH
)

print("\n================================")
print("MODEL SAVED SUCCESSFULLY!")
print("================================")

print("Model location:")
print(MODEL_PATH)