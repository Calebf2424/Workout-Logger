from database import *
import pytz                                                  #type: ignore
from datetime import datetime
from flask import request, session, flash, redirect, url_for, render_template #type: ignore
from database import *

#exercises on left associated muscle groups on right
presaved_exercises = [
    {"name": "Hip Abduction Machine", "muscle": "Abductors"},
    {"name": "Crunch", "muscle": "Abs"},
    {"name": "Ab Crunch Machine", "muscle": "Abs"},
    {"name": "Cable Crunch", "muscle": "Abs"},
    {"name": "Hanging Leg Raise", "muscle": "Abs"},
    {"name": "Hip Adduction Machine", "muscle": "Adductors"},
    {"name": "Cable Adduction", "muscle": "Adductors"},
    {"name": "Hammer Curl", "muscle": "Biceps"},
    {"name": "Incline Dumbbell Curl", "muscle": "Biceps"},
    {"name": "Barbell Curl", "muscle": "Biceps"},
    {"name": "Cable Curl", "muscle": "Biceps"},
    {"name": "Preacher Curl Machine", "muscle": "Biceps"},
    {"name": "Standing Calf Raise", "muscle": "Calves"},
    {"name": "Seated Calf Raise", "muscle": "Calves"},
    {"name": "Standing Calf Raise Machine", "muscle": "Calves"},
    {"name": "Seated Calf Raise Machine", "muscle": "Calves"},
    {"name": "Pec Deck", "muscle": "Chest"},
    {"name": "Machine Chest Press", "muscle": "Chest"},
    {"name": "Smith Machine Bench Press", "muscle": "Chest"},
    {"name": "Bench Press", "muscle": "Chest"},
    {"name": "Dumbbell Bench Press", "muscle": "Chest"},
    {"name": "Chest Fly", "muscle": "Chest"},
    {"name": "Push-Up", "muscle": "Chest"},
    {"name": "Back Extension Machine", "muscle": "Erectors"},
    {"name": "Deadlift", "muscle": "Erectors"},
    {"name": "Machine Shoulder Press", "muscle": "Front Delts"},
    {"name": "Overhead Press", "muscle": "Front Delts"},
    {"name": "Front Raise", "muscle": "Front Delts"},
    {"name": "Hip Thrust", "muscle": "Glutes"},
    {"name": "Glute Kickback", "muscle": "Glutes"},
    {"name": "Standing Glute Kickback Machine", "muscle": "Glutes"},
    {"name": "Seated Leg Curl", "muscle": "Hamstrings"},
    {"name": "Lying Leg Curl", "muscle": "Hamstrings"},
    {"name": "Romanian Deadlift", "muscle": "Hamstrings"},
    {"name": "Pull-Up", "muscle": "Lats"},
    {"name": "Lat Pulldown", "muscle": "Lats"},
    {"name": "Assisted Pull-Up Machine", "muscle": "Lats"},
    {"name": "Lat Pullover Machine", "muscle": "Lats"},
    {"name": "Decline Bench Press", "muscle": "Lower Chest"},
    {"name": "Cable Woodchopper", "muscle": "Obliques"},
    {"name": "Russian Twist", "muscle": "Obliques"},
    {"name": "Rotary Torso Machine", "muscle": "Obliques"},
    {"name": "Leg Press", "muscle": "Quads"},
    {"name": "Barbell Squat", "muscle": "Quads"},
    {"name": "Low Bar Squat", "muscle": "Hamstrings"},
    {"name": "Leg Extension Machine", "muscle": "Quads"},
    {"name": "Hack Squat", "muscle": "Quads"},
    {"name": "Smith Machine Squat", "muscle": "Quads"},
    {"name": "Reverse Pec Deck", "muscle": "Rear Delts"},
    {"name": "Bent-Over Lateral Raise", "muscle": "Rear Delts"},
    {"name": "Machine Rear Delt Fly", "muscle": "Rear Delts"},
    {"name": "Barbell Row", "muscle": "Rhomboids"},
    {"name": "Seated Cable Row", "muscle": "Rhomboids"},
    {"name": "Seated Row Machine", "muscle": "Rhomboids"},
    {"name": "Cable Lateral Raise", "muscle": "Side Delts"},
    {"name": "Lateral Raise", "muscle": "Side Delts"},
    {"name": "Shrug", "muscle": "Traps"},
    {"name": "Face Pull", "muscle": "Traps"},
    {"name": "Triceps Dip Machine", "muscle": "Triceps"},
    {"name": "Close-Grip Bench Press", "muscle": "Triceps"},
    {"name": "Triceps Pushdown", "muscle": "Triceps"},
    {"name": "Cable Triceps Pushdown", "muscle": "Triceps"},
    {"name": "Overhead Triceps Extension", "muscle": "Triceps"},
    {"name": "Incline Bench Press", "muscle": "Upper Chest"},
    {"name": "Hyperextensions", "muscle": "Hamstrings"}
]

preferred_order = [
    "Chest", "Upper Chest", "Lower Chest",
    "Back", "Lats", "Rhomboids", "Traps", "Erectors",
    "Shoulders", "Front Delts", "Side Delts", "Rear Delts",
    "Biceps", "Triceps", 
    "Quads", "Hamstrings", "Glutes", "Calves", "Adductors", "Abductors",
    "Abs", "Obliques"
]

app_settings = {
    "rpe_enabled": False,
    "timezone": "America/Edmonton",  # default to Edmonton
    "max_weight": 225
}


def summarize_muscles(sets, user_id):
    # Build master lookup
    muscle_map = {e["name"]: e["muscle"] for e in presaved_exercises}
    # Include DB-loaded custom exercises
    for e in get_all_custom_exercises(user_id):
        muscle_map[e["name"]] = e["muscle"]

    muscle_counts = {}
    for s in sets:
        exercise_name = s["exercise"]
        muscle = muscle_map.get(exercise_name, "Unknown")
        muscle_counts[muscle] = muscle_counts.get(muscle, 0) + 1

    return muscle_counts

def register_custom_exercise(name, muscle, presaved_exercises, user_id):
    for e in presaved_exercises:
        if e["name"] == name:
            e["muscle"] = muscle
            break
    else:
        presaved_exercises.append({"name": name, "muscle": muscle})

    # Persist in DB
    insert_custom_exercise(name, muscle, user_id)

# Get current user ID from session
def get_current_user_id():
    return session.get("user_id") or get_user_id_by_guest(session.get("guest_id"))

# Get user settings with fallback
def get_settings():
    user_id = get_current_user_id()
    return get_user_settings(user_id) or {
        "rpe_enabled": False,
        "timezone": "America/Edmonton",
        "max_weight": 225
    }

# Get current local date based on settings
def get_local_date_from_settings(settings):
    tz = pytz.timezone(settings.get("timezone", "UTC"))
    return datetime.now(tz).date().isoformat()

# Get timezone object from settings
def get_timezone_from_settings(settings):
    return pytz.timezone(settings.get("timezone", "UTC"))

# Sort muscle groups by preferred order
def sort_muscle_groups(exercises, preferred_order):
    muscles = set(e["muscle"] for e in exercises)
    return sorted(muscles, key=lambda m: preferred_order.index(m) if m in preferred_order else float("inf"))

# Expand sets in a routine to a flat list
def expand_routine_sets(routine_sets):
    expanded = []
    for s in routine_sets:
        for _ in range(s["sets"]):
            expanded.append({
                "id": s.get("id"),
                "exercise": s["exercise"],
                "sets": 1
            })
    return expanded

# Advance to next set in routine session
def advance_routine():
    routine = session.get("active_routine")
    if routine:
        routine["current_index"] += 1
        session["active_routine"] = routine

# Discard a routine in session and delete it
def discard_routine_session(routine_id):
    delete_routine(routine_id)
    session.pop("new_routine", None)
    flash("Routine discarded.", "danger")
    return redirect(url_for("premade"))

def handle_create_routine_post():
    user_id = get_current_user_id()
    all_exercises = presaved_exercises + get_all_custom_exercises(user_id)
    action = request.form.get("action")

    if action == "add":
        return handle_routine_add(user_id, all_exercises)
    elif action == "save":
        return handle_routine_save()
    elif action == "discard":
        rid = session.get("new_routine", {}).get("id")
        if rid:
            return discard_routine_session(rid)
    return redirect(url_for("create_routine"))


def handle_routine_add(user_id, all_exercises):
    if "new_routine" not in session:
        name = request.form.get("routine_name", "").strip()
        if not name:
            flash("Give your routine a name first!", "danger")
            return redirect(url_for("create_routine"))

        rid = insert_routine(name, user_id)
        session["new_routine"] = {"id": rid, "name": name}
        flash(f"Routine '{name}' created!", "success")
        return redirect(url_for("create_routine"))

    rid = session["new_routine"]["id"]
    exercise = request.form.get("exercise")

    if not exercise:
        flash("Please select an exercise.", "danger")
        return redirect(url_for("create_routine"))

    if exercise == "__custom__":
        name = request.form.get("custom_name", "").strip()
        muscle = request.form.get("custom_muscle", "").strip()
        if not name or not muscle:
            flash("Please fill in both name and muscle group for custom exercise.", "danger")
            return redirect(url_for("create_routine"))
        register_custom_exercise(name, muscle, all_exercises, user_id)
        exercise = name

    sets_count = int(request.form.get("sets", 1))
    insert_routine_set(rid, exercise, sets_count, user_id)
    flash(f"Added {sets_count}× {exercise}", "success")
    return redirect(url_for("create_routine"))


def handle_routine_save():
    if "new_routine" not in session:
        flash("No routine in progress.", "warning")
        return redirect(url_for("create_routine"))

    rid = session["new_routine"]["id"]
    order = request.form.get("order", "")
    ids = [int(x) for x in order.split(",") if x.strip().isdigit()]
    for index, set_id in enumerate(ids):
        update_routine_set_position(set_id, index)

    name = session["new_routine"]["name"]
    flash(f"Routine “{name}” saved!", "success")
    session.pop("new_routine", None)
    return redirect(url_for("premade"))


def render_create_routine_form():
    settings = get_settings()
    user_id = get_current_user_id()
    all_exercises = presaved_exercises + get_all_custom_exercises(user_id)
    muscle_groups = sort_muscle_groups(all_exercises, preferred_order)
    current = session.get("new_routine")
    current_sets = get_sets_for_routine(current["id"]) if current else []

    return render_template(
        "create_routine.html",
        exercises=all_exercises,
        muscle_groups=muscle_groups,
        current_routine=current,
        current_sets=current_sets,
        settings=settings
    )

def handle_edit_routine_post(routine_id):
    user_id = get_current_user_id()
    action = request.form.get("action")

    if action == "add":
        return handle_edit_add_exercise(routine_id, user_id)
    elif action == "delete":
        set_id = int(request.form.get("set_id"))
        delete_routine_set(set_id)
        flash("Exercise removed from routine.", "warning")
        return redirect(url_for("edit_routine", routine_id=routine_id))
    elif action == "update":
        set_id = int(request.form.get("set_id"))
        new_sets = int(request.form.get("new_sets", 1))
        update_routine_set_count(set_id, new_sets)
        flash("Set count updated.", "success")
        return redirect(url_for("edit_routine", routine_id=routine_id))

    return redirect(url_for("edit_routine", routine_id=routine_id))


def handle_edit_add_exercise(routine_id, user_id):
    exercise = request.form.get("exercise")
    if exercise == "__custom__":
        name = request.form.get("custom_name", "").strip()
        muscle = request.form.get("custom_muscle", "").strip()
        if not name or not muscle:
            flash("Custom exercise name and muscle are required.", "danger")
            return redirect(url_for("edit_routine", routine_id=routine_id))

        register_custom_exercise(name, muscle, presaved_exercises, user_id)
        exercise = name

    sets = int(request.form.get("sets", 1))
    insert_routine_set(routine_id, exercise, sets, user_id)
    flash(f"Added {sets}× {exercise}", "success")
    return redirect(url_for("edit_routine", routine_id=routine_id))


def render_edit_routine_form(routine_id):
    settings = get_settings()
    user_id = get_current_user_id()
    all_exercises = presaved_exercises + get_all_custom_exercises(user_id)
    muscle_groups = sort_muscle_groups(all_exercises, preferred_order)
    routine_sets = get_sets_for_routine(routine_id)

    return render_template("edit_routine.html",
                           routine_sets=routine_sets,
                           routine_id=routine_id,
                           settings=settings,
                           exercises=all_exercises,
                           muscle_groups=muscle_groups)

def handle_edit_program(program_id):
    user_id = get_current_user_id()
    program = get_program_by_id(program_id)
    all_routines = get_all_routines(user_id)
    current_routines = get_program_routines(program_id)

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        days = int(request.form.get("days", 3))
        loop = request.form.get("loop") == "on"

        if not name or days < 1 or days > 10:
            flash("Invalid input.", "danger")
            return redirect(url_for("edit_program", program_id=program_id))

        update_program_metadata(program_id, name, days, loop)
        delete_program(program_id)

        for i in range(days):
            routine_id = request.form.get(f"routine_day_{i}")
            if routine_id != "rest":
                insert_program_routine(program_id, i, int(routine_id))

        flash("Program updated!", "success")
        return redirect(url_for("view_programs"))

    return render_template("edit_program.html",
                           program=program,
                           routines=current_routines,
                           all_routines=all_routines,
                           settings=get_settings())
