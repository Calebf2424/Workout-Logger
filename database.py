import os
import psycopg2
from psycopg2.extras import RealDictCursor

DATABASE_URL = os.environ.get("DATABASE_URL")

def get_connection():
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)

def create_sets_table():
    with get_connection() as conn:
        with conn.cursor() as c:
            c.execute("""
                CREATE TABLE IF NOT EXISTS sets (
                    id SERIAL PRIMARY KEY,
                    exercise TEXT NOT NULL,
                    reps INTEGER,
                    weight INTEGER,
                    rpe REAL,
                    date TEXT NOT NULL,
                    user_id INTEGER
                )
            """)

def create_custom_exercise_table():
    with get_connection() as conn:
        with conn.cursor() as c:
            c.execute("""
                CREATE TABLE IF NOT EXISTS custom_exercises (
                    name TEXT PRIMARY KEY,
                    muscle TEXT NOT NULL
                )
            """)

def insert_set(exercise, reps, weight, rpe, date, user_id=None):
    with get_connection() as conn:
        with conn.cursor() as c:
            c.execute("""
                INSERT INTO sets (exercise, reps, weight, rpe, date, user_id)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (exercise, reps, weight, rpe, date, user_id))

def insert_custom_exercise(name, muscle):
    with get_connection() as conn:
        with conn.cursor() as c:
            c.execute("""
                INSERT INTO custom_exercises (name, muscle)
                VALUES (%s, %s)
                ON CONFLICT (name) DO NOTHING
            """, (name, muscle))

def get_all_sets():
    with get_connection() as conn:
        with conn.cursor() as c:
            c.execute("SELECT * FROM sets")
            return c.fetchall()

def get_specific_day(chosen_date):
    with get_connection() as conn:
        with conn.cursor() as c:
            c.execute("SELECT * FROM sets WHERE date = %s", (chosen_date,))
            return c.fetchall()

def get_all_custom_exercises():
    with get_connection() as conn:
        with conn.cursor() as c:
            c.execute("SELECT name, muscle FROM custom_exercises")
            return [{"name": row["name"], "muscle": row["muscle"]} for row in c.fetchall()]

def clear_database():
    with get_connection() as conn:
        with conn.cursor() as c:
            c.execute("DELETE FROM sets")
            c.execute("DELETE FROM custom_exercises")

def delete_set(set_id):
    with get_connection() as conn:
        with conn.cursor() as c:
            c.execute("DELETE FROM sets WHERE id = %s", (set_id,))

def get_set_by_id(set_id):
    with get_connection() as conn:
        with conn.cursor() as c:
            c.execute("SELECT * FROM sets WHERE id = %s", (set_id,))
            return c.fetchone()

def update_set(set_id, reps, weight, rpe):
    with get_connection() as conn:
        with conn.cursor() as c:
            c.execute("""
                UPDATE sets
                SET reps = %s, weight = %s, rpe = %s
                WHERE id = %s
            """, (reps, weight, rpe, set_id))

def clear_custom_exercises():
    with get_connection() as conn:
        with conn.cursor() as c:
            c.execute("DELETE FROM custom_exercises")

def create_planned_routines_table():
    with get_connection() as conn:
        with conn.cursor() as c:
            c.execute("""
                CREATE TABLE IF NOT EXISTS planned_routines (
                    id SERIAL PRIMARY KEY,
                    name TEXT NOT NULL
                )
            """)

def create_routine_sets_table():
    with get_connection() as conn:
        with conn.cursor() as c:
            c.execute("""
                CREATE TABLE IF NOT EXISTS routine_sets (
                    id SERIAL PRIMARY KEY,
                    routine_id INTEGER NOT NULL,
                    exercise TEXT NOT NULL,
                    sets INTEGER NOT NULL DEFAULT 1,
                    position INTEGER NOT NULL DEFAULT 0,
                    FOREIGN KEY(routine_id) REFERENCES planned_routines(id) ON DELETE CASCADE
                )
            """)

def insert_routine(name):
    with get_connection() as conn:
        with conn.cursor() as c:
            c.execute("INSERT INTO planned_routines (name) VALUES (%s) RETURNING id", (name,))
            return c.fetchone()["id"]

def insert_routine_set(routine_id, exercise, sets=1):
    with get_connection() as conn:
        with conn.cursor() as c:
            c.execute("SELECT MAX(position) FROM routine_sets WHERE routine_id = %s", (routine_id,))
            max_pos = c.fetchone()["max"]
            next_pos = (max_pos + 1) if max_pos is not None else 0
            c.execute("""
                INSERT INTO routine_sets (routine_id, exercise, sets, position)
                VALUES (%s, %s, %s, %s)
            """, (routine_id, exercise, sets, next_pos))

def get_all_routines():
    with get_connection() as conn:
        with conn.cursor() as c:
            c.execute("SELECT id, name FROM planned_routines ORDER BY name")
            return c.fetchall()

def get_sets_for_routine(routine_id):
    with get_connection() as conn:
        with conn.cursor() as c:
            c.execute("""
                SELECT id, exercise, sets FROM routine_sets
                WHERE routine_id = %s
                ORDER BY position ASC, id ASC
            """, (routine_id,))
            return c.fetchall()

def delete_routine(routine_id):
    with get_connection() as conn:
        with conn.cursor() as c:
            c.execute("DELETE FROM routine_sets WHERE routine_id = %s", (routine_id,))
            c.execute("DELETE FROM planned_routines WHERE id = %s", (routine_id,))

def update_routine_set_position(set_id, position):
    with get_connection() as conn:
        with conn.cursor() as c:
            c.execute("""
                UPDATE routine_sets
                SET position = %s
                WHERE id = %s
            """, (position, set_id))
