
"""
database.py
SQLite database layer for the AI-Powered Personalized Nutrition and
Meal Planning System.

Handles:
  - User registration & login (with hashed passwords)
  - User health profile storage
  - AI-generated meal plan storage & retrieval

Usage:
    from database import init_db, register_user, verify_login, \
        save_user_profile, save_meal_plan, get_meal_plan
"""

import sqlite3
import hashlib
import hmac
import os
import json
from datetime import datetime

DB_PATH = "nutrition_app.db"


# ---------------------------------------------------------------------
# CONNECTION
# ---------------------------------------------------------------------
def get_connection():
    """Open a connection with foreign keys enforced and row access by name."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    return conn


# ---------------------------------------------------------------------
# SCHEMA
# ---------------------------------------------------------------------
def init_db():
    """Create all tables if they don't already exist. Safe to call every app start."""
    conn = get_connection()
    cur = conn.cursor()

    # ---- Users (login) ----
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id       INTEGER PRIMARY KEY AUTOINCREMENT,
            username      TEXT UNIQUE NOT NULL,
            email         TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            salt          TEXT NOT NULL,
            created_at    TEXT NOT NULL
        )
    """)

    # ---- Health / profile info (Step 1 & 3 of your workflow) ----
    cur.execute("""
        CREATE TABLE IF NOT EXISTS user_profile (
            profile_id        INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id           INTEGER NOT NULL,
            age               INTEGER,
            gender            TEXT,
            height_cm         REAL,
            weight_kg         REAL,
            activity_level    TEXT,     -- e.g. sedentary, moderate, active
            dietary_preference TEXT,    -- e.g. vegetarian, vegan, keto
            fitness_goal      TEXT,     -- e.g. weight loss, muscle gain
            allergies         TEXT,     -- comma-separated or JSON list
            bmi               REAL,
            daily_calories    REAL,
            protein_g         REAL,
            carbs_g           REAL,
            fat_g             REAL,
            fiber_g           REAL,
            updated_at        TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE
        )
    """)

    # ---- Meal plans (one row per AI-generated plan / day) ----
    cur.execute("""
        CREATE TABLE IF NOT EXISTS meal_plans (
            plan_id      INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id      INTEGER NOT NULL,
            plan_date    TEXT NOT NULL,      -- date the plan is FOR
            ai_summary   TEXT,               -- AI's dietary tips/explanation
            created_at   TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE
        )
    """)

    # ---- Individual meals/items inside a plan ----
    cur.execute("""
        CREATE TABLE IF NOT EXISTS meal_plan_items (
            item_id      INTEGER PRIMARY KEY AUTOINCREMENT,
            plan_id      INTEGER NOT NULL,
            meal_type    TEXT NOT NULL,   -- breakfast, lunch, dinner, snack
            food_name    TEXT NOT NULL,
            calories     REAL,
            protein_g    REAL,
            carbs_g      REAL,
            fat_g        REAL,
            recipe_text  TEXT,            -- AI-generated recipe / instructions
            FOREIGN KEY (plan_id) REFERENCES meal_plans (plan_id) ON DELETE CASCADE
        )
    """)

    conn.commit()
    conn.close()


# ---------------------------------------------------------------------
# PASSWORD HASHING (no external deps; use bcrypt/argon2 for production)
# ---------------------------------------------------------------------
def _hash_password(password: str, salt: bytes = None):
    if salt is None:
        salt = os.urandom(16)
    pw_hash = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 100_000)
    return pw_hash.hex(), salt.hex()


def _verify_password(password: str, salt_hex: str, stored_hash_hex: str) -> bool:
    salt = bytes.fromhex(salt_hex)
    new_hash, _ = _hash_password(password, salt)
    return hmac.compare_digest(new_hash, stored_hash_hex)


# ---------------------------------------------------------------------
# USER / LOGIN FUNCTIONS
# ---------------------------------------------------------------------
def register_user(username: str, email: str, password: str) -> int:
    """Create a new user. Returns the new user_id, or raises sqlite3.IntegrityError
    if username/email already exists."""
    pw_hash, salt = _hash_password(password)
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """INSERT INTO users (username, email, password_hash, salt, created_at)
           VALUES (?, ?, ?, ?, ?)""",
        (username, email, pw_hash, salt, datetime.utcnow().isoformat()),
    )
    conn.commit()
    user_id = cur.lastrowid
    conn.close()
    return user_id


def verify_login(username: str, password: str):
    """Returns the user row (as a dict) if credentials are correct, else None."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE username = ?", (username,))
    row = cur.fetchone()
    conn.close()
    if row and _verify_password(password, row["salt"], row["password_hash"]):
        return dict(row)
    return None


# ---------------------------------------------------------------------
# HEALTH PROFILE FUNCTIONS
# ---------------------------------------------------------------------
def save_user_profile(user_id: int, profile: dict):
    """
    profile keys expected (all optional except what you require in your app):
    age, gender, height_cm, weight_kg, activity_level, dietary_preference,
    fitness_goal, allergies, bmi, daily_calories, protein_g, carbs_g, fat_g, fiber_g
    """
    conn = get_connection()
    cur = conn.cursor()
    # One profile row per user: update if it exists, else insert
    cur.execute("SELECT profile_id FROM user_profile WHERE user_id = ?", (user_id,))
    existing = cur.fetchone()
    fields = ["age", "gender", "height_cm", "weight_kg", "activity_level",
              "dietary_preference", "fitness_goal", "allergies", "bmi",
              "daily_calories", "protein_g", "carbs_g", "fat_g", "fiber_g"]
    values = [profile.get(f) for f in fields]

    if existing:
        set_clause = ", ".join(f"{f} = ?" for f in fields)
        cur.execute(
            f"UPDATE user_profile SET {set_clause}, updated_at = ? WHERE user_id = ?",
            (*values, datetime.utcnow().isoformat(), user_id),
        )
    else:
        cols = ", ".join(fields)
        placeholders = ", ".join("?" for _ in fields)
        cur.execute(
            f"""INSERT INTO user_profile (user_id, {cols}, updated_at)
                VALUES (?, {placeholders}, ?)""",
            (user_id, *values, datetime.utcnow().isoformat()),
        )
    conn.commit()
    conn.close()


def get_user_profile(user_id: int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM user_profile WHERE user_id = ?", (user_id,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None


# ---------------------------------------------------------------------
# MEAL PLAN FUNCTIONS
# ---------------------------------------------------------------------
def save_meal_plan(user_id: int, plan_date: str, ai_summary: str, items: list):
    """
    items: list of dicts, each like:
      {
        "meal_type": "breakfast",
        "food_name": "Oats with banana",
        "calories": 350, "protein_g": 12, "carbs_g": 55, "fat_g": 6,
        "recipe_text": "Cook oats with water/milk, top with sliced banana..."
      }
    """
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """INSERT INTO meal_plans (user_id, plan_date, ai_summary, created_at)
           VALUES (?, ?, ?, ?)""",
        (user_id, plan_date, ai_summary, datetime.utcnow().isoformat()),
    )
    plan_id = cur.lastrowid

    for item in items:
        cur.execute(
            """INSERT INTO meal_plan_items
               (plan_id, meal_type, food_name, calories, protein_g, carbs_g, fat_g, recipe_text)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (plan_id, item.get("meal_type"), item.get("food_name"),
             item.get("calories"), item.get("protein_g"), item.get("carbs_g"),
             item.get("fat_g"), item.get("recipe_text")),
        )
    conn.commit()
    conn.close()
    return plan_id


def get_meal_plans(user_id: int):
    """Returns all meal plans for a user, each with its nested items."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT * FROM meal_plans WHERE user_id = ? ORDER BY plan_date DESC",
        (user_id,),
    )
    plans = [dict(row) for row in cur.fetchall()]

    for plan in plans:
        cur.execute(
            "SELECT * FROM meal_plan_items WHERE plan_id = ?", (plan["plan_id"],)
        )
        plan["items"] = [dict(row) for row in cur.fetchall()]

    conn.close()
    return plans


# ---------------------------------------------------------------------
# Quick manual test
# ---------------------------------------------------------------------
if __name__ == "__main__":
    init_db()
    print("Database initialized:", DB_PATH)

    try:
        uid = register_user("test_user", "test@example.com", "Passw0rd!")
        print("Registered user_id:", uid)
    except sqlite3.IntegrityError:
        user = verify_login("test_user", "Passw0rd!")
        uid = user["user_id"]
        print("User already existed, logged in as:", uid)

    save_user_profile(uid, {
        "age": 24, "gender": "F", "height_cm": 165, "weight_kg": 60,
        "activity_level": "moderate", "dietary_preference": "vegetarian",
        "fitness_goal": "weight maintenance", "allergies": "peanuts",
        "bmi": 22.0, "daily_calories": 2000,
        "protein_g": 90, "carbs_g": 250, "fat_g": 60, "fiber_g": 30
    })
    print("Profile saved:", get_user_profile(uid))

    plan_id = save_meal_plan(uid, str(datetime.utcnow().date()), "Balanced day with good fiber intake.", [
        {"meal_type": "breakfast", "food_name": "Vegetable poha", "calories": 300,
         "protein_g": 8, "carbs_g": 55, "fat_g": 6, "recipe_text": "Cook flattened rice with mustard seeds, onions, peas and lemon."}
    ])
    print("Meal plans:", json.dumps(get_meal_plans(uid), indent=2))
