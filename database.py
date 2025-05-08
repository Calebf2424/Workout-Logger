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

def clear_custom_exercises():
    conn = get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM custom_exercises")
    conn.commit()
    conn.close()

#routines 
def create_planned_routines_table():
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS planned_routines (
        id    INTEGER PRIMARY KEY AUTOINCREMENT,
        name  TEXT    NOT NULL
    )
    """)
    conn.commit()
    conn.close()

def create_routine_sets_table():
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS routine_sets (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        routine_id  INTEGER NOT NULL,
        exercise    TEXT    NOT NULL,
        sets        INTEGER NOT NULL DEFAULT 1,
        position    INTEGER NOT NULL DEFAULT 0,
        FOREIGN KEY(routine_id) REFERENCES planned_routines(id) ON DELETE CASCADE
    )
    """)
    conn.commit()
    conn.close()

def insert_routine(name: str) -> int:
    conn = get_connection()
    c = conn.cursor()
    c.execute("INSERT INTO planned_routines (name) VALUES (?)", (name,))
    routine_id = c.lastrowid
    conn.commit()
    conn.close()
    return routine_id

def insert_routine_set(routine_id: int, exercise: str, sets: int = 1):
    conn = get_connection()
    c = conn.cursor()

    # Get current max position for that routine
    c.execute("SELECT MAX(position) FROM routine_sets WHERE routine_id = ?", (routine_id,))
    max_pos = c.fetchone()[0]
    next_pos = (max_pos + 1) if max_pos is not None else 0

    c.execute(
        "INSERT INTO routine_sets (routine_id, exercise, sets, position) VALUES (?, ?, ?, ?)",
        (routine_id, exercise, sets, next_pos)
    )
    conn.commit()
    conn.close()

def get_all_routines() -> list[dict]:
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT id, name FROM planned_routines ORDER BY name")
    rows = c.fetchall()
    conn.close()
    return [{"id": r[0], "name": r[1]} for r in rows]

def get_sets_for_routine(routine_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT id, exercise, sets FROM routine_sets
        WHERE routine_id = ?
        ORDER BY position ASC, id ASC
    """, (routine_id,))
    rows = c.fetchall()
    conn.close()
    return [{"id": row[0], "exercise": row[1], "sets": row[2]} for row in rows]

def delete_routine(routine_id: int):
    conn = get_connection()
    c = conn.cursor()
    # Remove template sets first (CASCADE would do it, but explicit is safe)
    c.execute("DELETE FROM routine_sets WHERE routine_id = ?", (routine_id,))
    c.execute("DELETE FROM planned_routines WHERE id = ?", (routine_id,))
    conn.commit()
    conn.close()

def update_routine_set_position(set_id, position):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        UPDATE routine_sets
        SET position = ?
        WHERE id = ?
    """, (position, set_id))
    conn.commit()
    conn.close()
