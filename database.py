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
                    is_premium BOOLEAN DEFAULT FALSE,
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

def update_routine_set_count(set_id, new_count):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE routine_sets
                SET sets = %s
                WHERE id = %s
            """, (new_count, set_id))

def delete_routine_set(set_id):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM routine_sets WHERE id = %s", (set_id,))

#accounts
def create_user_account(username, password_hash, email, guest_id=None):
    with get_connection() as conn:
        with conn.cursor() as cur:
            if guest_id:
                # Upgrade existing guest record
                cur.execute("""
                    UPDATE users
                    SET username = %s,
                        password_hash = %s,
                        email = %s,
                        is_guest = FALSE,
                        guest_id = NULL
                    WHERE guest_id = %s
                    RETURNING id;
                """, (username, password_hash, email, guest_id))
            else:
                # Create a brand new user
                cur.execute("""
                    INSERT INTO users (username, password_hash, email, is_guest)
                    VALUES (%s, %s, %s, FALSE)
                    RETURNING id;
                """, (username, password_hash, email))

            result = cur.fetchone()
            return result["id"] if result else None

def get_user_by_username(username):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM users WHERE username = %s AND is_guest = FALSE", (username,))
            return cur.fetchone()

#settings 
def create_user_settings_table():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS user_settings (
                    user_id INTEGER PRIMARY KEY REFERENCES users(id),
                    rpe_enabled BOOLEAN DEFAULT FALSE,
                    timezone TEXT DEFAULT 'UTC',
                    max_weight INTEGER DEFAULT 225
                );
            """)

def get_user_settings(user_id):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM user_settings WHERE user_id = %s", (user_id,))
            return cur.fetchone()

def set_user_settings(user_id, rpe_enabled, timezone, max_weight):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO user_settings (user_id, rpe_enabled, timezone, max_weight)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (user_id)
                DO UPDATE SET rpe_enabled = EXCLUDED.rpe_enabled,
                              timezone = EXCLUDED.timezone,
                              max_weight = EXCLUDED.max_weight
            """, (user_id, rpe_enabled, timezone, max_weight))

#programming
def create_programs_table():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS programs (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES users(id),
                    name TEXT NOT NULL,
                    days INTEGER NOT NULL,
                    loop BOOLEAN DEFAULT TRUE,
                    is_active BOOLEAN DEFAULT FALSE,
                    start_date DATE DEFAULT CURRENT_DATE,
                    current_day INTEGER DEFAULT 0
                );
            """)

def create_program_routines_table():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS program_routines (
                    id SERIAL PRIMARY KEY,
                    program_id INTEGER REFERENCES programs(id) ON DELETE CASCADE,
                    day_index INTEGER NOT NULL,
                    routine_id INTEGER REFERENCES planned_routines(id)
                );
            """)

def insert_program(user_id, name, days, loop):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO programs (user_id, name, days, loop)
                VALUES (%s, %s, %s, %s)
                RETURNING id
            """, (user_id, name, days, loop))
            return cur.fetchone()["id"]

def insert_program_routine(program_id, day_index, routine_id):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO program_routines (program_id, day_index, routine_id)
                VALUES (%s, %s, %s)
            """, (program_id, day_index, routine_id))
def get_user_programs(user_id):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT * FROM programs
                WHERE user_id = %s
                ORDER BY is_active DESC, id DESC
            """, (user_id,))
            return cur.fetchall()

def get_program_by_id(program_id):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM programs WHERE id = %s", (program_id,))
            return cur.fetchone()

def get_program_routines(program_id):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT pr.day_index, pr.routine_id, r.name
                FROM program_routines pr
                JOIN planned_routines r ON pr.routine_id = r.id
                WHERE pr.program_id = %s
                ORDER BY pr.day_index
            """, (program_id,))
            return cur.fetchall()

def deactivate_all_programs(user_id):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE programs
                SET is_active = FALSE
                WHERE user_id = %s
            """, (user_id,))

def activate_program(program_id, start_day=0):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE programs
                SET is_active = TRUE,
                    start_date = CURRENT_DATE,
                    current_day = %s
                WHERE id = %s
            """, (start_day, program_id))

def delete_program(program_id):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM programs WHERE id = %s", (program_id,))

def update_program_metadata(program_id, name, days, loop):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE programs
                SET name = %s,
                    days = %s,
                    loop = %s
                WHERE id = %s
            """, (name, days, loop, program_id))

def delete_program_routines(program_id):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM program_routines WHERE program_id = %s", (program_id,))

def get_active_program(user_id):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT * FROM programs
                WHERE user_id = %s AND is_active = TRUE
                LIMIT 1
            """, (user_id,))
            return cur.fetchone()

def get_routine_by_day(program_id, day_index):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT r.id, r.name
                FROM program_routines pr
                JOIN planned_routines r ON pr.routine_id = r.id
                WHERE pr.program_id = %s AND pr.day_index = %s
                LIMIT 1
            """, (program_id, day_index))
            return cur.fetchone()

def update_current_day_for_program(program_id, new_day):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE programs
                SET current_day = %s,
                    start_date = CURRENT_DATE
                WHERE id = %s
            """, (new_day, program_id))
