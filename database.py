import os
import psycopg2 # type: ignore
from psycopg2.extras import RealDictCursor #type: ignore

DATABASE_URL = os.environ.get("DATABASE_URL")

def get_connection():
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)

# USERS
def create_users_table():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    guest_id TEXT UNIQUE,
                    username TEXT UNIQUE,
                    password_hash TEXT,
                    email TEXT UNIQUE,
                    is_guest BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)

def create_guest_user(guest_id):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO users (guest_id, is_guest)
                VALUES (%s, TRUE)
                ON CONFLICT (guest_id) DO NOTHING
            """, (guest_id,))

def get_user_id_by_guest(guest_id):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM users WHERE guest_id = %s", (guest_id,))
            row = cur.fetchone()
            return row["id"] if row else None

# SETS
def create_sets_table():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS sets (
                    id SERIAL PRIMARY KEY,
                    exercise TEXT NOT NULL,
                    reps INTEGER,
                    weight INTEGER,
                    rpe REAL,
                    date TEXT NOT NULL,
                    user_id INTEGER REFERENCES users(id)
                );
            """)

def insert_set(exercise, reps, weight, rpe, date, user_id=None):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO sets (exercise, reps, weight, rpe, date, user_id)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (exercise, reps, weight, rpe, date, user_id))

def get_all_sets(user_id):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM sets WHERE user_id = %s", (user_id,))
            return cur.fetchall()

def get_specific_day(chosen_date, user_id):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM sets WHERE date = %s AND user_id = %s", (chosen_date, user_id))
            return cur.fetchall()

def delete_set(set_id):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM sets WHERE id = %s", (set_id,))

def get_set_by_id(set_id):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM sets WHERE id = %s", (set_id,))
            return cur.fetchone()

def update_set(set_id, reps, weight, rpe):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE sets
                SET reps = %s, weight = %s, rpe = %s
                WHERE id = %s
            """, (reps, weight, rpe, set_id))

# CUSTOM EXERCISES
def create_custom_exercise_table():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS custom_exercises (
                    name TEXT PRIMARY KEY,
                    muscle TEXT NOT NULL,
                    user_id INTEGER REFERENCES users(id)
                );
            """)

def insert_custom_exercise(name, muscle, user_id):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO custom_exercises (name, muscle, user_id)
                VALUES (%s, %s, %s)
                ON CONFLICT (name) DO NOTHING
            """, (name, muscle, user_id))

def get_all_custom_exercises(user_id):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT name, muscle FROM custom_exercises WHERE user_id = %s", (user_id,))
            return [{"name": row["name"], "muscle": row["muscle"]} for row in cur.fetchall()]

def clear_custom_exercises(user_id):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM custom_exercises WHERE user_id = %s", (user_id,))

# ROUTINES
def create_planned_routines_table():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS planned_routines (
                    id SERIAL PRIMARY KEY,
                    name TEXT NOT NULL,
                    user_id INTEGER REFERENCES users(id)
                );
            """)

def create_routine_sets_table():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS routine_sets (
                    id SERIAL PRIMARY KEY,
                    routine_id INTEGER NOT NULL,
                    exercise TEXT NOT NULL,
                    sets INTEGER NOT NULL DEFAULT 1,
                    position INTEGER NOT NULL DEFAULT 0,
                    user_id INTEGER REFERENCES users(id),
                    FOREIGN KEY(routine_id) REFERENCES planned_routines(id) ON DELETE CASCADE
                );
            """)

def insert_routine(name, user_id):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("INSERT INTO planned_routines (name, user_id) VALUES (%s, %s) RETURNING id", (name, user_id))
            return cur.fetchone()["id"]

def insert_routine_set(routine_id, exercise, sets, user_id):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT MAX(position) FROM routine_sets WHERE routine_id = %s", (routine_id,))
            max_pos = cur.fetchone()["max"]
            next_pos = (max_pos + 1) if max_pos is not None else 0
            cur.execute("""
                INSERT INTO routine_sets (routine_id, exercise, sets, position, user_id)
                VALUES (%s, %s, %s, %s, %s)
            """, (routine_id, exercise, sets, next_pos, user_id))

def get_all_routines(user_id):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id, name FROM planned_routines WHERE user_id = %s ORDER BY name", (user_id,))
            return cur.fetchall()

def get_sets_for_routine(routine_id):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, exercise, sets FROM routine_sets
                WHERE routine_id = %s
                ORDER BY position ASC, id ASC
            """, (routine_id,))
            return cur.fetchall()

def delete_routine(routine_id):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM routine_sets WHERE routine_id = %s", (routine_id,))
            cur.execute("DELETE FROM planned_routines WHERE id = %s", (routine_id,))

def update_routine_set_position(set_id, position):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE routine_sets
                SET position = %s
                WHERE id = %s
            """, (position, set_id))
