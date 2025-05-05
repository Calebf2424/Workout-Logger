import sqlite3

DB_NAME = "sets.db"

def get_connection():
    return sqlite3.connect(DB_NAME)

def create_sets_table():
    conn = get_connection()
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS sets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        exercise TEXT NOT NULL,
        reps INTEGER,
        weight INTEGER,
        rpe REAL,
        date TEXT NOT NULL,
        user_id INTEGER
    )
    """)

    conn.commit()
    conn.close()

def create_custom_exercise_table():
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS custom_exercises (
            name TEXT PRIMARY KEY,
            muscle TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

def insert_set(exercise, reps, weight, rpe, date, user_id=None):
    conn = get_connection()
    c = conn.cursor()

    c.execute("""
    INSERT INTO sets (exercise, reps, weight, rpe, date, user_id)
    VALUES (?, ?, ?, ?, ?, ?)
    """, (exercise, reps, weight, rpe, date, user_id))

    conn.commit()
    conn.close()

def insert_custom_exercise(name, muscle):
    conn = get_connection()
    c = conn.cursor()

    c.execute("""
    INSERT OR IGNORE INTO custom_exercises (name, muscle)
    VALUES (?, ?)
    """, (name, muscle))
    
    conn.commit()
    conn.close()

def get_all_sets():
    conn = get_connection()
    c = conn.cursor()

    c.execute("SELECT * FROM sets")
    rows = c.fetchall()

    conn.close()
    return rows

def get_specific_day(chosen_date):
    conn = get_connection()
    c = conn.cursor()

    c.execute("SELECT * FROM sets WHERE date = ?", (chosen_date,))

    rows = c.fetchall()

    conn.close()
    return rows

def get_all_custom_exercises():
    conn = get_connection()
    c = conn.cursor()

    c.execute("SELECT name, muscle FROM custom_exercises")

    rows = c.fetchall()
    conn.close()
    return [{"name": row[0], "muscle": row[1]} for row in rows]

#for debugging
def clear_database():
    conn = get_connection()
    c = conn.cursor()

    c.execute("DELETE FROM sets")
    c.execute("DELETE FROM custom_exercises")
    conn.commit()
    conn.close()

def delete_set(set_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM sets WHERE id = ?", (set_id,))
    conn.commit()
    conn.close()

def get_set_by_id(set_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM sets WHERE id = ?", (set_id,))
    row = c.fetchone()
    conn.close()
    return row

def update_set(set_id, reps, weight, rpe):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        UPDATE sets
        SET reps = ?, weight = ?, rpe = ?
        WHERE id = ?
    """, (reps, weight, rpe, set_id))
    conn.commit()
    conn.close()
