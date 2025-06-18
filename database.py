from datetime import datetime

import sqlite3
import os
import csv

# Create database and tables (run only once)
def init_db():
    conn = sqlite3.connect('predictions.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS predictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,       
            image_path TEXT NOT NULL,
            prediction TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    first_name TEXT,
    last_name TEXT,
    username TEXT UNIQUE NOT NULL,
    dob TEXT,
    gender TEXT,
    email TEXT,
    phone TEXT,
    alt_phone TEXT,
    password TEXT,
    house TEXT,
    street TEXT,
    landmark TEXT,
    city TEXT,
    state TEXT,
    pin TEXT,
    country TEXT,
    language TEXT
)''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS reset_tokens (
        email TEXT,
        token TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')

    conn.commit()
    conn.close()

# Call this when app starts
init_db()

# Save prediction to DB
def save_to_database(username, image_path, prediction_result):
    conn = sqlite3.connect('predictions.db')  # Use your actual database path
    cursor = conn.cursor()
    cursor.execute("INSERT INTO predictions (username, image_path, prediction) VALUES (?, ?, ?)",
                   (username, image_path, prediction_result))
    conn.commit()
    conn.close()


# Get predictions for a specific user
def get_all_predictions(username):
    conn = sqlite3.connect('predictions.db')
    cursor = conn.cursor()
    cursor.execute("SELECT image_path, prediction, confidence, timestamp FROM predictions WHERE username = ?", (username,))
    predictions = cursor.fetchall()
    conn.close()
    
    # Convert to datetime if needed
    formatted_predictions = [(image, disease, confidence, datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')) 
                             for image, disease, confidence, timestamp in predictions]
    
    return formatted_predictions



# Get all predictions for CSV
def export_predictions_to_csv(file_path='predictions.csv'):
    conn = sqlite3.connect('predictions.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM predictions ORDER BY id DESC")
    results = cursor.fetchall()
    conn.close()

    with open(file_path, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['ID', 'Image Path', 'Prediction'])  # headers
        writer.writerows(results)

    return file_path

# Delete all predictions (for admin or full reset)
def delete_all_predictions():
    conn = sqlite3.connect('predictions.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM predictions")
    conn.commit()
    conn.close()



# Delete predictions for a specific user
def delete_user_predictions(username):
    conn = sqlite3.connect('predictions.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM predictions WHERE username = ?", (username,))
    conn.commit()
    conn.close()   

# ----------------------------
# User Auth Functions
# ----------------------------

# Add user to the users table
def add_user(
    first_name, last_name, username, dob, gender, email, phone,
    alt_phone, password, house, street, landmark, city,
    state, pin, country, language
):
    conn = sqlite3.connect('predictions.db')
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO users (
                first_name, last_name, username, dob, gender, email, phone, alt_phone,
                password, house, street, landmark, city, state, pin, country, language
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            first_name, last_name, username, dob, gender, email, phone, alt_phone,
            password, house, street, landmark, city, state, pin, country, language
        ))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False  # Username already exists
    finally:
        conn.close()


# Validate user login
def validate_user(username, password):
    conn = sqlite3.connect('predictions.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
    user = cursor.fetchone()
    conn.close()
    return user
