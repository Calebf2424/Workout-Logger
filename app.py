from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, make_response  # type: ignore
from werkzeug.security import generate_password_hash, check_password_hash                       # type: ignore
from datetime import date, timedelta, datetime
import pytz                                                                           # type: ignore
import uuid
from dotenv import load_dotenv                                                        # type: ignore
import os

from database import *
from data import *

app = Flask(__name__)
load_dotenv()
app.secret_key = os.environ.get("SECRET_KEY", "fallback-dev-key")

# --- TABLE CREATION ---
create_users_table()
create_sets_table()
create_custom_exercise_table()
create_planned_routines_table()
create_routine_sets_table()

# --- SESSION HANDLING ---
@app.before_request
def require_guest():
    allowed_routes = {"static", "landing", "create_guest", "login", "register", "restore_session"}
    if request.endpoint in allowed_routes:
        return
    if "guest_id" not in session and "user_id" not in session:
        return redirect(url_for("landing"))

@app.route("/landing")
def landing():
    return render_template("landing.html")

@app.route("/create-guest", methods=["POST"])
def create_guest():
    guest_id = f"guest_{uuid.uuid4().hex[:8]}"
    session["guest_id"] = guest_id
    create_guest_user(guest_id)

    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return jsonify({"guest_id": guest_id})

    return redirect(url_for("index"))

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username").strip()
        password = request.form.get("password")
        email    = request.form.get("email").strip()
        if len(username) < 5:
            flash("Username must be at least 5 characters long.", "danger")
            return redirect(url_for("register"))

        if get_user_by_username(username):
            flash("Username already taken.", "danger")
            return redirect(url_for("register"))

        password_hash = generate_password_hash(password)
        guest_id = session.get("guest_id")  # Pull guest ID if it exists

        new_user_id = create_user_account(username, password_hash, email, guest_id)

        if new_user_id:
            # Clear guest ID and log in as real user
            session.clear()
            session["user_id"] = new_user_id
            session["is_guest"] = False
            flash("Account created successfully!", "success")

            # Tell frontend to remove guest ID from localStorage
            response = make_response(redirect(url_for("index")))
            response.set_cookie("clear_guest_id", "1", max_age=5, path="/")
            return response
        else:
            flash("Registration failed.", "danger")

    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        user = get_user_by_username(username)
        if user and check_password_hash(user["password_hash"], password):
            session.clear()
            session["user_id"] = user["id"]
            session["is_guest"] = False
            flash("Logged in successfully!", "success")
            return redirect(url_for("index"))
        else:
            flash("Invalid username or password.", "danger")
            return redirect(url_for("login"))

    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully.", "info")
    response = make_response(redirect(url_for("landing")))
    response.set_cookie("clear_guest_id", "1", max_age=5, path="/")
    return response

@app.route("/restore-session", methods=["POST"])
def restore_session():
    data = request.get_json()
    guest_id = data.get("guest_id")

    if guest_id:
        session["guest_id"] = guest_id
        create_guest_user(guest_id)
        return jsonify({"status": "ok"})
    return jsonify({"status": "missing"}), 400

# --- CORE ROUTES ---
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/add-workout", methods=["GET", "POST"])
def add_workout():
    user_id = get_current_user_id()
    if request.method == "POST":
        exercise = request.form.get("exercise")
        if exercise == "__custom__":
            name = request.form.get("custom_name")
            muscle = request.form.get("custom_muscle")
            exercise = name
            register_custom_exercise(name, muscle, user_id)

        reps = request.form.get("reps")
        weight = request.form.get("weight")
        rpe = request.form.get("rpe") if app_settings["rpe_enabled"] else None
        tz_name = app_settings.get("timezone", "UTC")

        tz = pytz.timezone(tz_name)
        local_now = datetime.now(tz)
        log_date = local_now.date().isoformat()

        insert_set(exercise, int(reps), int(weight), float(rpe) if rpe else None, log_date, user_id)
        flash("Set added!")
        return redirect(url_for("add_workout"))

    all_exercises = presaved_exercises + get_all_custom_exercises(user_id)
    muscle_groups = sorted(
        set(e["muscle"] for e in all_exercises),
        key=lambda x: preferred_order.index(x) if x in preferred_order else float("inf")
    )
    return render_template("add.html", exercises=all_exercises, muscle_groups=muscle_groups, settings=app_settings)

@app.route("/history")
def history():
    return render_template("history.html")

@app.route("/history/day", methods=["GET", "POST"])
def day_history():
    if request.method == "POST":
        chosen_date = request.form.get("date")
    else:
        chosen_date = request.args.get("date")

    if chosen_date:
        user_id = get_current_user_id()
        sets = get_specific_day(chosen_date, user_id)
        muscle_counts = summarize_muscles(sets, user_id)

        dt = date.fromisoformat(chosen_date)
        prev_date = (dt - timedelta(days=1)).isoformat()
        next_date = (dt + timedelta(days=1)).isoformat()
        display_date = f"{dt.strftime('%B')} {dt.day}, {dt.year}"

        return render_template("day_history.html", sets=sets, chosen_date=chosen_date,
                               prev_date=prev_date, next_date=next_date,
                               display_date=display_date,
                               muscle_counts=muscle_counts, settings=app_settings)

    return render_template("day_history.html", sets=None, chosen_date=None,
                       muscle_counts={}, settings=app_settings)

@app.route("/history/week", methods=["GET", "POST"])
def week_history():
    if request.method == "POST":
        chosen_date = request.form.get("date")
    else:
        chosen_date = request.args.get("date")

    if not chosen_date:
        return render_template("week_history.html", sets=None, chosen_date=None,
                               muscle_counts={}, settings=app_settings)

    # Align chosen date to the start of the week (Sunday)
    dt = date.fromisoformat(chosen_date)
    sunday = dt - timedelta(days=dt.weekday() + 1) if dt.weekday() != 6 else dt
    week_dates = [(sunday + timedelta(days=i)).isoformat() for i in range(7)]

    user_id = get_current_user_id()
    all_sets = []
    for d in week_dates:
        all_sets.extend(get_specific_day(d, user_id))

    muscle_counts = summarize_muscles(all_sets, user_id)

    full_counts = {muscle: muscle_counts.get(muscle, 0) for muscle in preferred_order}

    sorted_muscles = sorted(full_counts.items(), key=lambda item: (-item[1], item[0].lower()))

    display_range = f"{sunday.strftime('%B')} {sunday.day} – {(sunday + timedelta(days=6)).strftime('%B')} {(sunday + timedelta(days=6)).day}"

    return render_template("week_history.html", sets=all_sets, chosen_date=sunday.isoformat(),
                           display_range=display_range, muscle_counts=muscle_counts, sorted_muscles=sorted_muscles,
                           settings=app_settings, preferred_order=preferred_order)

@app.route("/summary")
def summary():
    user_id = get_current_user_id()
    tzname = app_settings.get("timezone", "America/Edmonton")
    tz = pytz.timezone(tzname)
    local_today = datetime.now(tz).date().isoformat()

    sets = get_specific_day(local_today, user_id)
    muscle_counts = summarize_muscles(sets, user_id)

    return render_template("summary.html", sets=sets, today=local_today,
                           muscle_counts=muscle_counts, settings=app_settings)

@app.route("/settings", methods=["GET", "POST"])
def settings():
    if request.method == "POST":
        app_settings["rpe_enabled"] = request.form.get("rpe_enabled") == "on"
        app_settings["timezone"] = request.form.get("timezone", "UTC")
        app_settings["max_weight"] = int(request.form.get("max_weight", 225))
        return redirect(url_for("index"))

    return render_template("settings.html", settings=app_settings, timezones=pytz.all_timezones)

@app.route("/delete-set/<int:set_id>", methods=["POST"])
def delete_set_route(set_id):
    origin = request.form.get("origin")
    date_param = request.form.get("date")
    delete_set(set_id)
    if origin == "summary":
        return redirect(url_for("summary") + "#exercises")
    elif origin == "history" and date_param:
        return redirect(url_for("day_history", date=date_param))
    return redirect(url_for("index"))

@app.route("/edit-set/<int:set_id>", methods=["GET", "POST"])
def edit_set_route(set_id):
    if request.method == "POST":
        reps = int(request.form["reps"])
        weight = int(request.form["weight"])
        rpe = float(request.form["rpe"]) if app_settings["rpe_enabled"] and request.form.get("rpe") else None
        origin = request.form.get("origin")
        date_param = request.form.get("date")
        update_set(set_id, reps, weight, rpe)
        if origin == "summary":
            return redirect(url_for("summary") + "#exercises")
        return redirect(url_for("day_history", date=date_param))

    origin = request.args.get("origin")
    date_param = request.args.get("date")
    set_data = get_set_by_id(set_id)
    return render_template("edit.html", set_data=set_data,
                           origin=origin, date_param=date_param, settings=app_settings)

# --- PREMADE ROUTINES ---
@app.route("/premade", methods=["GET", "POST"])
def premade():
    if request.method == "POST":
        action = request.form.get("action")
        if action == "create":
            return redirect(url_for("create_routine"))
        elif action.startswith("start_"):
            routine_id = int(action.replace("start_", ""))
            return redirect(url_for("start_routine", routine_id=routine_id))
        elif action.startswith("delete_"):
            routine_id = int(action.replace("delete_", ""))
            delete_routine(routine_id)
            return redirect(url_for("premade"))
    user_id = get_current_user_id()
    routines = get_all_routines(user_id)
    return render_template("premade.html", routines=routines)

#start
@app.route("/start-routine/<int:routine_id>")
def start_routine(routine_id):
    sets_data = get_sets_for_routine(routine_id)

    workout_queue = []
    for row in sets_data:
        for i in range(row["sets"]):
            workout_queue.append({
                "exercise": row["exercise"],
                "set_number": i + 1
            })
    session["active_routine"] = {
        "routine_id": routine_id,
        "sets": workout_queue,
        "current_index": 0
    }

    return redirect(url_for("workout_mode"))

@app.route("/workout-mode", methods=["GET"])
def workout_mode():
    routine = session.get("active_routine")
    if not routine:
        flash("No active workout")
        return redirect(url_for("premade"))
    
    sets = routine["sets"]
    index = routine["current_index"]

    #check if workout is finished
    if index >= len(sets):
        flash("Workout complete!")
        session.pop("active_routine", None)
        return redirect(url_for("summary"))
    
    current_set = sets[index]
    exercise = current_set["exercise"]
    set_number = current_set["set_number"]
    next_exercise = None
    if index < len(sets) - 1:
        next_exercise = sets[index + 1]["exercise"]


    return render_template("workout_mode.html",
                       exercise=exercise,
                       set_number=set_number,
                       index=index + 1,
                       total=len(sets),
                       next_exercise=next_exercise,
                       settings=app_settings)

@app.route("/complete-set", methods=["POST"])
def complete_set():
    routine = session.get("active_routine")
    if not routine:
        flash("No active workout.")
        return redirect(url_for("premade"))

    idx = routine["current_index"]
    current = routine["sets"][idx]
    user_id = get_current_user_id()
    exercise = current["exercise"]
    reps     = int(request.form["reps"])
    weight   = float(request.form["weight"])
    rpe      = float(request.form["rpe"]) if request.form.get("rpe") else None

    tz = pytz.timezone(app_settings.get("timezone", "UTC"))
    local_now = datetime.now(tz)
    log_date = local_now.date().isoformat()

    insert_set(exercise, reps, weight, rpe, log_date, user_id)

    routine["current_index"] = idx + 1
    session["active_routine"] = routine

    return redirect(url_for("workout_mode"))

@app.route("/create-routine", methods=["GET", "POST"])
def create_routine():
    user_id = get_current_user_id()
    all_exercises = presaved_exercises + get_all_custom_exercises(user_id)

    if request.method == "POST":
        action = request.form.get("action")
        user_id = get_current_user_id()
        # STEP 1 — Create the routine
        if action == "add":
            if "new_routine" not in session:
                name = request.form.get("routine_name", "").strip()
                if not name:
                    flash("Give your routine a name first!", "danger")
                    return redirect(url_for("create_routine"))

                rid = insert_routine(name, user_id)
                session["new_routine"] = {"id": rid, "name": name}
                flash(f"Routine '{name}' created!", "success")
                return redirect(url_for("create_routine"))

            # STEP 2 — Add an exercise to the routine
            rid = session["new_routine"]["id"]
            exercise = request.form.get("exercise")

            if not exercise:
                flash("Please select an exercise.", "danger")
                return redirect(url_for("create_routine"))

            # Custom exercise handling
            if exercise == "__custom__":
                custom_name = request.form.get("custom_name", "").strip()
                custom_muscle = request.form.get("custom_muscle", "").strip()

                if not custom_name or not custom_muscle:
                    flash("Please fill in both name and muscle group for custom exercise.", "danger")
                    return redirect(url_for("create_routine"))

                register_custom_exercise(custom_name, custom_muscle, presaved_exercises, user_id)
                exercise = custom_name

            # Sets count
            sets_count = int(request.form.get("sets", 1))
            insert_routine_set(rid, exercise, sets_count, user_id)
            flash(f"Added {sets_count}× {exercise}", "success")
            return redirect(url_for("create_routine"))

        # Save the routine
        elif action == "save":
            if "new_routine" in session:
                rid = session["new_routine"]["id"]
            # Handle order update
            order = request.form.get("order", "")
            ids = [int(x) for x in order.split(",") if x.strip().isdigit()]
            for index, set_id in enumerate(ids):
                update_routine_set_position(set_id, index)

            name = session["new_routine"]["name"]
            flash(f"Routine “{name}” saved!", "success")
            session.pop("new_routine", None)

            return redirect(url_for("premade"))

        # Discard routine and delete from DB
        elif action == "discard":
            if "new_routine" in session:
                rid = session["new_routine"]["id"]
                delete_routine(rid)
                session.pop("new_routine", None)
            flash("Routine discarded.", "danger")
            return redirect(url_for("premade"))

    # GET method — show the form
    current = session.get("new_routine")
    current_sets = []
    if current:
        current_sets = get_sets_for_routine(current["id"])

    # Pass muscle group options for custom selector
    muscle_groups = sorted(
        set(e["muscle"] for e in all_exercises),
        key=lambda m: preferred_order.index(m) if m in preferred_order else float('inf')
    )

    return render_template(
        "create_routine.html",
        exercises=all_exercises,
        muscle_groups=muscle_groups,
        current_routine=current,
        current_sets=current_sets,
        settings=app_settings
    )

@app.route("/reorder-routine-sets", methods=["POST"])
def reorder_routine_sets():
    order = request.form.get("order", "")
    ids = [int(x) for x in order.split(",") if x.strip().isdigit()]

    # Set new position field in DB (you’d add a `position` column to `routine_sets`)
    for index, set_id in enumerate(ids):
        update_routine_set_position(set_id, index)

    flash("Routine order updated!", "success")
    return redirect(url_for("create_routine"))

@app.route("/preview-routine/<int:routine_id>")
def preview_routine(routine_id):
    user_id = get_current_user_id()
    routine_sets = get_sets_for_routine(routine_id)

    routine_name = next((r["name"] for r in get_all_routines(user_id) if r["id"] == routine_id), "Unnamed Routine")

    routine_sets_expanded = []
    for s in routine_sets:
        for _ in range(s["sets"]):
            routine_sets_expanded.append({
                                        "id": s["id"],
                                        "exercise": s["exercise"],
                                        "sets": 1
                                        })

    muscle_counts = summarize_muscles(routine_sets_expanded, user_id)

    return render_template(
        "preview_routine.html",
        routine_name=routine_name,
        routine_sets=routine_sets,
        settings=app_settings,     
        routine_id=routine_id,
        muscle_counts=muscle_counts
    )

@app.route("/skip-set", methods=["POST"])
def skip_set():
    action = request.form.get("action")
    routine = session.get("active_routine")

    if not routine:
        flash("No active workout.")
        return redirect(url_for("premade"))

    idx = routine["current_index"]
    skipped = routine["sets"][idx]

    if action == "skip_later":
        routine["sets"].append(skipped)  # move to end
    # In either case, move forward
    routine["current_index"] += 1

    session["active_routine"] = routine
    
    return redirect(url_for("workout_mode"))

@app.route("/dev")
def dev_page():
    return render_template("dev.html")

@app.route("/dev/user-count")
def dev_user_count():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM users WHERE is_guest = TRUE")
            count = cur.fetchone()["count"]
            return jsonify({"guest_user_count": count})

@app.route("/dev/usernames")
def dev_usernames():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT username FROM users WHERE username IS NOT NULL ORDER BY username")
            names = [row["username"] for row in cur.fetchall()]
    return jsonify({"usernames": names})

#funcs
def get_local_date():
    user_tz = session.get("timezone", "UTC")
    tz = pytz.timezone(user_tz)
    return datetime.now(tz).date().isoformat()

def get_current_user_id():
    return session.get("user_id") or get_user_id_by_guest(session.get("guest_id"))