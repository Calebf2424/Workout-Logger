from flask import Flask, render_template, request, redirect, url_for, flash, session # type: ignore
from datetime import date, datetime, timedelta
from database import *
from data import *

app = Flask(__name__)
app.secret_key = "added"

create_sets_table()
create_custom_exercise_table()
clear_custom_exercises() 
create_planned_routines_table()
create_routine_sets_table()

#home page
@app.route("/")
def index():
    return render_template("index.html")

#page for adding sets to todays workout
@app.route("/add-workout", methods=["GET", "POST"])
def add_workout():
    if request.method == "POST":
        exercise = request.form.get("exercise")
        if exercise == "__custom__":
            name = request.form.get("custom_name")
            muscle = request.form.get("custom_muscle")
            exercise = name
            # Add to in-memory presaved_exercises
            register_custom_exercise(name, muscle, presaved_exercises)

        reps = request.form.get("reps")
        weight = request.form.get("weight")
        rpe = request.form.get("rpe") if app_settings["rpe_enabled"] else None
        log_date = date.today().isoformat()

        insert_set(exercise, int(reps), int(weight), float(rpe) if rpe else None, log_date, None)
        flash("Set added!")
        return redirect(url_for("add_workout"))

    all_exercises = presaved_exercises + get_all_custom_exercises()
    muscle_groups = sorted(
        set(e["muscle"] for e in all_exercises),
        key=lambda x: preferred_order.index(x) if x in preferred_order else float("inf")
    )
    return render_template("add.html", exercises=all_exercises, muscle_groups=muscle_groups, settings=app_settings)

#history
@app.route("/history", methods=["GET", "POST"])
def history():
    # Determine chosen_date from POST (form) or GET (query param)
    if request.method == "POST":
        chosen_date = request.form.get("date")
    else:
        chosen_date = request.args.get("date")

    if chosen_date:
        sets = get_specific_day(chosen_date)
        muscle_counts = summarize_muscles(sets)

        dt = date.fromisoformat(chosen_date)
        prev_date = (dt - timedelta(days=1)).isoformat()
        next_date = (dt + timedelta(days=1)).isoformat()

        display_date = f"{dt.strftime('%B')} {dt.day}, {dt.year}"

        return render_template(
            "history.html",
            sets=sets,
            chosen_date=chosen_date,
            prev_date=prev_date,
            next_date=next_date,
            display_date=display_date,
            muscle_counts=muscle_counts,
            settings=app_settings
        )

    # No date chosen yet
    return render_template("history.html", sets=None, chosen_date=None)

#to be added later, shows progress in certain exercises
@app.route("/progress")
def progress():
    return render_template("progress.html")

#summary of workout for the day when choosing to end the workout
@app.route("/summary")
def summary():
    today = date.today().isoformat()
    sets = get_specific_day(today)
    muscle_counts = summarize_muscles(sets)
    
    return render_template("summary.html", sets=sets, today=today, muscle_counts=muscle_counts, settings=app_settings)

@app.route("/settings", methods=["GET", "POST"])
def settings():
    if request.method == "POST":
        app_settings["rpe_enabled"] = request.form.get("rpe_enabled") == "on"
        app_settings["dark_mode"] = request.form.get("dark_mode") == "on"
        return redirect(url_for("index"))

    return render_template("settings.html", settings=app_settings)

#temp for testing
@app.route("/delete-db")
def delete_db():
    clear_database()
    return redirect(url_for("index"))

#delete a set
@app.route("/delete-set/<int:set_id>", methods=["POST"])
def delete_set_route(set_id):
    origin = request.form.get("origin")
    date_param = request.form.get("date")
    delete_set(set_id)

    if origin == "summary":
        return redirect(url_for("summary") + "#exercises")
    elif origin == "history" and date_param:
        return redirect(url_for("history", date=date_param))
    else:
        return redirect(url_for("index"))

# Edit a set
@app.route("/edit-set/<int:set_id>", methods=["GET", "POST"])
def edit_set_route(set_id):
    if request.method == "POST":
        # Parse submitted form values
        reps = int(request.form["reps"])
        weight = int(request.form["weight"])

        # Only grab RPE if enabled
        if app_settings["rpe_enabled"]:
            rpe_raw = request.form.get("rpe")
            rpe = float(rpe_raw) if rpe_raw else None
        else:
            rpe = None

        # Where we came from (summary/history) and date if history
        origin     = request.form.get("origin")
        date_param = request.form.get("date")

        # Update in the DB
        update_set(set_id, reps, weight, rpe)

        # Redirect back, anchoring to #exercises if from summary
        if origin == "summary":
            return redirect(url_for("summary") + "#exercises")
        else:
            return redirect(url_for("history", date=date_param))

    # GET -> render the edit form
    origin     = request.args.get("origin")
    date_param = request.args.get("date")
    set_data   = get_set_by_id(set_id)

    return render_template(
        "edit.html",
        set_data=set_data,
        origin=origin,
        date_param=date_param,
        settings=app_settings
    )

#premade workout routes
#everything below for premade routines
#landing page
@app.route("/premade", methods=["GET", "POST"])
def premade():
    if request.method == "POST":
        action = request.form.get("action")

        if action == "create":
            return redirect(url_for("create_routine"))
        elif action.startswith("start_"):
            routine_id = int(action.replace("start_", ""))
            return redirect(url_for("start_routine", routine_id=routine_id))
        elif action.startswith("edit_"):
            routine_id = int(action.replace("edit_", ""))
            return redirect(url_for("edit_routine", routine_id=routine_id))
        elif action.startswith("delete_"):
            routine_id = int(action.replace("delete_", ""))
            delete_routine(routine_id)
            return redirect(url_for("premade"))
        
    routines = get_all_routines()
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

    return render_template("workout_mode.html",
                           exercise=exercise,
                           set_number=set_number,
                           index=index + 1,  # for 1-based display
                           total=len(sets),
                           settings=app_settings)

@app.route("/complete-set", methods=["POST"])
def complete_set():
    routine = session.get("active_routine")
    if not routine:
        flash("No active workout.")
        return redirect(url_for("premade"))

    idx = routine["current_index"]
    current = routine["sets"][idx]

    exercise = current["exercise"]
    reps     = int(request.form["reps"])
    weight   = float(request.form["weight"])
    rpe      = float(request.form["rpe"]) if request.form.get("rpe") else None

    log_date = date.today().isoformat()
    insert_set(exercise, reps, weight, rpe, log_date, None)

    routine["current_index"] = idx + 1
    session["active_routine"] = routine

    return redirect(url_for("workout_mode"))

@app.route("/create-routine", methods=["GET", "POST"])
def create_routine():
    # 1) Combine presets + custom
    all_exercises = presaved_exercises + get_all_custom_exercises()

    if request.method == "POST":
        action = request.form.get("action")

        # — Add one exercise to the new routine —
        if action == "add":
            # If routine not yet created, create it
            if "new_routine" not in session:
                name = request.form.get("routine_name", "").strip()
                if not name:
                    flash("Give your routine a name first!", "danger")
                    return redirect(url_for("create_routine"))
                rid = insert_routine(name)
                session["new_routine"] = {"id": rid, "name": name}

            # Insert the selected exercise + set count
            rid = session["new_routine"]["id"]
            exercise  = request.form.get("exercise")
            sets_count = int(request.form.get("sets", 1))
            insert_routine_set(rid, exercise, sets_count)

            flash(f"Added {sets_count}× {exercise}", "success")
            return redirect(url_for("create_routine"))

        # — Save and finish the routine —
        elif action == "save":
            if "new_routine" in session:
                name = session["new_routine"]["name"]
                flash(f"Routine “{name}” saved!", "success")
                session.pop("new_routine", None)
            return redirect(url_for("premade"))
        elif action == "discard":
            if "new_routine" in session:
                rid = session["new_routine"]["id"]
                delete_routine(rid)  # <- remove routine + sets
                session.pop("new_routine", None)
            flash("Routine discarded.", "danger")
            return redirect(url_for("premade"))

    # 2) On GET, or after POST redirect, show form plus any already-added sets
    current = session.get("new_routine")
    current_sets = []
    if current:
        current_sets = get_sets_for_routine(current["id"])

    return render_template(
                            "create_routine.html",
                            exercises=all_exercises,
                            muscle_groups=sorted(
                                set(e["muscle"] for e in all_exercises),
                                key=lambda m: preferred_order.index(m) if m in preferred_order else float('inf')
                            ),
                            current_routine=current,
                            current_sets=current_sets,
                            settings=app_settings
    )