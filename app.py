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
create_user_settings_table()
create_programs_table()
create_program_routines_table()

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
    is_guest = "guest_id" in session and "user_id" not in session
    return render_template("index.html", is_guest=is_guest)

@app.route("/add-workout", methods=["GET", "POST"])
def add_workout():
    user_id = get_current_user_id()
    settings = get_settings()

    if request.method == "POST":
        exercise = request.form.get("exercise")
        if exercise == "__custom__":
            name = request.form.get("custom_name")
            muscle = request.form.get("custom_muscle")
            exercise = name
            register_custom_exercise(name, muscle, presaved_exercises, user_id)

        reps = request.form.get("reps")
        weight = request.form.get("weight")
        rpe = request.form.get("rpe") if settings["rpe_enabled"] else None

        log_date = get_local_date_from_settings(settings)

        insert_set(exercise, int(reps), int(weight), float(rpe) if rpe else None, log_date, user_id)
        flash("Set added!")
        return redirect(url_for("add_workout"))

    all_exercises = presaved_exercises + get_all_custom_exercises(user_id)
    muscle_groups = sort_muscle_groups(all_exercises, preferred_order)

    return render_template("add.html", exercises=all_exercises, muscle_groups=muscle_groups, settings=settings)

@app.route("/history")
def history():
    return render_template("history.html")

@app.route("/history/day", methods=["GET", "POST"])
def day_history():
    settings = get_settings()
    user_id = get_current_user_id()

    if request.method == "POST":
        chosen_date = request.form.get("date")
    else:
        chosen_date = request.args.get("date")

    if chosen_date:
        sets = get_specific_day(chosen_date, user_id)
        muscle_counts = summarize_muscles(sets, user_id)

        dt = date.fromisoformat(chosen_date)
        prev_date = (dt - timedelta(days=1)).isoformat()
        next_date = (dt + timedelta(days=1)).isoformat()
        display_date = f"{dt.strftime('%B')} {dt.day}, {dt.year}"

        return render_template("day_history.html", sets=sets, chosen_date=chosen_date,
                               prev_date=prev_date, next_date=next_date,
                               display_date=display_date,
                               muscle_counts=muscle_counts, settings=settings)

    return render_template("day_history.html", sets=None, chosen_date=None,
                       muscle_counts={}, settings=app_settings)

@app.route("/history/week", methods=["GET", "POST"])
def week_history():
    settings = get_settings()
    user_id = get_current_user_id()

    if request.method == "POST":
        chosen_date = request.form.get("date")
    else:
        chosen_date = request.args.get("date")

    if not chosen_date:
        return render_template("week_history.html", sets=None, chosen_date=None,
                               muscle_counts={}, settings=settings)

    # Align chosen date to the start of the week (Sunday)
    dt = date.fromisoformat(chosen_date)
    sunday = dt - timedelta(days=dt.weekday() + 1) if dt.weekday() != 6 else dt
    week_dates = [(sunday + timedelta(days=i)).isoformat() for i in range(7)]

    all_sets = []
    for d in week_dates:
        all_sets.extend(get_specific_day(d, user_id))

    muscle_counts = summarize_muscles(all_sets, user_id)

    full_counts = {muscle: muscle_counts.get(muscle, 0) for muscle in preferred_order}

    sorted_muscles = sorted(full_counts.items(), key=lambda item: (-item[1], item[0].lower()))

    display_range = f"{sunday.strftime('%B')} {sunday.day} – {(sunday + timedelta(days=6)).strftime('%B')} {(sunday + timedelta(days=6)).day}"

    return render_template("week_history.html", sets=all_sets, chosen_date=sunday.isoformat(),
                           display_range=display_range, muscle_counts=muscle_counts, sorted_muscles=sorted_muscles,
                           settings=settings, preferred_order=preferred_order)

@app.route("/summary")
def summary():
    settings = get_settings()
    user_id = get_current_user_id()
    
    tzname = app_settings.get("timezone", "America/Edmonton")
    tz = pytz.timezone(tzname)
    local_today = datetime.now(tz).date().isoformat()

    sets = get_specific_day(local_today, user_id)
    muscle_counts = summarize_muscles(sets, user_id)

    return render_template("summary.html", sets=sets, today=local_today,
                           muscle_counts=muscle_counts, settings=settings)

@app.route("/settings", methods=["GET", "POST"])
def settings():
    user_id = get_current_user_id()

    if request.method == "POST":
        rpe_enabled = request.form.get("rpe_enabled") == "on"
        timezone = request.form.get("timezone", "UTC")
        max_weight = int(request.form.get("max_weight", 225))

        set_user_settings(user_id, rpe_enabled, timezone, max_weight)
        flash("Settings saved!", "success")
        return redirect(url_for("index"))

    settings = get_user_settings(user_id)
    if settings is None:
        settings = {
            "rpe_enabled": False,
            "timezone": "UTC",
            "max_weight": 225
        }

    return render_template("settings.html", settings=settings, timezones=pytz.all_timezones)

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
    settings = get_settings()

    if request.method == "POST":
        reps = int(request.form["reps"])
        weight = int(request.form["weight"])
        rpe = float(request.form["rpe"]) if settings["rpe_enabled"] and request.form.get("rpe") else None

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
                           origin=origin, date_param=date_param, settings=settings)

# --- PREMADE ROUTINES ---
@app.route("/premade", methods=["GET", "POST"])
def premade():
    return handle_premade(request)

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
    settings = get_settings()
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
                       settings=settings)

@app.route("/complete-set", methods=["POST"])
def complete_set():
    settings = get_settings()
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

    log_date = get_local_date_from_settings(settings)

    insert_set(exercise, reps, weight, rpe, log_date, user_id)

    advance_routine()

    return redirect(url_for("workout_mode"))

@app.route("/create-routine", methods=["GET", "POST"])
def create_routine():
    if request.method == "POST":
        return handle_create_routine_post()
    return render_create_routine_form()

@app.route("/reorder-routine-sets", methods=["POST"])
def reorder_routine_sets():
    order = request.form.get("order", "")
    routine_id = request.form.get("routine_id")
    redirect_target = request.form.get("next", "create_routine")  # default fallback
    ids = [int(x) for x in order.split(",") if x.strip().isdigit()]

    for index, set_id in enumerate(ids):
        update_routine_set_position(set_id, index)

    flash("Routine order updated!", "success")

    if redirect_target == "premade":
        return redirect(url_for("premade"))
    elif routine_id:
        return redirect(url_for("edit_routine", routine_id=routine_id))
    return redirect(url_for("create_routine"))

@app.route("/edit-routine/<int:routine_id>", methods=["GET", "POST"])
def edit_routine(routine_id):
    if request.method == "POST":
        return handle_edit_routine_post(routine_id)
    return render_edit_routine_form(routine_id)

@app.route("/preview-routine/<int:routine_id>")
def preview_routine(routine_id):
    settings = get_settings()
    user_id = get_current_user_id()
    routine_sets = get_sets_for_routine(routine_id)

    routine_name = next((r["name"] for r in get_all_routines(user_id) if r["id"] == routine_id), "Unnamed Routine")

    routine_sets_expanded = expand_routine_sets(routine_sets)

    muscle_counts = summarize_muscles(routine_sets_expanded, user_id)

    return render_template(
        "preview_routine.html",
        routine_name=routine_name,
        routine_sets=routine_sets,
        settings=settings,     
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
    sets = routine["sets"]

    # Safety: ensure index is valid
    if idx >= len(sets):
        flash("No more sets.")
        return redirect(url_for("workout_mode"))

    skipped_set = sets[idx]

    if action == "skip_later":
        # Move to end, but don't advance index
        sets.append(skipped_set)
        sets.pop(idx)  # remove from current spot

        # index stays the same
    elif action == "skip_today":
        # Just remove it permanently
        sets.pop(idx)

        # index stays the same, next set shifts into this position

    # If no sets left, go back to home
    if not sets:
        flash("All sets skipped.", "info")
        session.pop("active_routine", None)
        return redirect(url_for("premade"))

    # Save updated session
    routine["sets"] = sets
    routine["current_index"] = idx  # index unchanged
    session["active_routine"] = routine

    return redirect(url_for("workout_mode"))

#dev routes
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

#programming routes
@app.route("/programs")
def view_programs():
    user_id = get_current_user_id()
    programs = get_user_programs(user_id)
    active = get_active_program(user_id)
    active_id = active["id"] if active else None

    for p in programs:
        raw_routines = get_program_routines(p["id"])  # only filled days
        padded = [None] * p["days"]  # fill with None
        for r in raw_routines:
            padded[r["day_index"]] = r  # insert routine into correct index
        p["routines"] = padded

    return render_template("programs.html", programs=programs, active_id=active_id)

@app.route("/create-program", methods=["GET", "POST"])
def create_program():
    user_id = get_current_user_id()
    all_routines = get_all_routines(user_id)
    settings = get_settings()

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        days = int(request.form.get("days", 3))
        loop = request.form.get("loop") == "on"

        if not name or days < 1 or days > 10:
            flash("Invalid input.", "danger")
            return redirect(url_for("create_program"))

        program_id = insert_program(user_id, name, days, loop)

        for i in range(days):
            routine_id = request.form.get(f"routine_day_{i}")
            if routine_id == "rest":
                continue  # Skip rest days
            insert_program_routine(program_id, i, int(routine_id))

        flash("Program created!", "success")
        return redirect(url_for("view_programs"))

    return render_template("create_program.html", routines=all_routines, settings=settings)

@app.route("/activate-program/<int:program_id>", methods=["POST"])
def activate_selected_program(program_id):
    user_id = get_current_user_id()
    deactivate_all_programs(user_id)

    # Get selected start day from form (defaults to 0)
    start_day = int(request.form.get("start_day", 0))
    activate_program(program_id, start_day)

    flash("Program activated.", "success")
    return redirect(url_for("view_programs"))

@app.route("/delete-program/<int:program_id>", methods=["POST"])
def delete_selected_program(program_id):
    delete_program(program_id)
    flash("Program deleted.", "danger")
    return redirect(url_for("view_programs"))

@app.route("/program-summary/<int:program_id>")
def program_summary(program_id):
    user_id = get_current_user_id()
    program = get_program_by_id(program_id)

    if not program or program["user_id"] != user_id:
        flash("Program not found.", "danger")
        return redirect(url_for("view_programs"))

    split_length = program["days"]
    routines = get_program_routines(program_id)

    total_sets = {}
    for r in routines:
        if r["routine_id"]:
            sets = expand_routine_sets(get_sets_for_routine(r["routine_id"]))
            mc = summarize_muscles(sets, user_id)
            for m, count in mc.items():
                total_sets[m] = total_sets.get(m, 0) + count

    # Compute and sort sets per 7 days
    sets_per_week = {}
    for m in preferred_order:
        weekly = total_sets.get(m, 0) * 7 / split_length
        if weekly.is_integer():
            sets_per_week[m] = int(weekly)
        else:
            sets_per_week[m] = round(weekly, 2)

    # Sort by most sets first, then alphabetically
    sorted_sets = sorted(sets_per_week.items(), key=lambda x: (-x[1], x[0].lower()))

    return render_template("program_summary.html",
                           active_program=program,
                           sorted_sets=sorted_sets,
                           split_length=split_length)

@app.route("/edit-program/<int:program_id>", methods=["GET", "POST"])
def edit_program(program_id):
    return handle_edit_program(program_id)

@app.route("/deactivate-program/<int:program_id>", methods=["POST"])
def deactivate_selected_program(program_id):
    user_id = get_current_user_id()
    program = get_program_by_id(program_id)

    if program and program["user_id"] == user_id:
        deactivate_all_programs(user_id)
        flash("Program deactivated.", "warning")

    return redirect(url_for("view_programs"))
