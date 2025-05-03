from flask import Flask, render_template, request, redirect, url_for, flash # type: ignore
from datetime import date
from database import *
from data import presaved_exercises, summarize_muscles, register_custom_exercise, preferred_order

app = Flask(__name__)
app.secret_key = "added"

create_sets_table()
create_custom_exercise_table()

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
        rpe = request.form.get("rpe")
        log_date = date.today().isoformat()

        insert_set(exercise, int(reps), int(weight), float(rpe), log_date, None)
        flash("Set added!")
        return redirect(url_for("add_workout"))

    all_exercises = presaved_exercises + get_all_custom_exercises()
    muscle_groups = sorted(
        set(e["muscle"] for e in all_exercises),
        key=lambda x: preferred_order.index(x) if x in preferred_order else float("inf")
    )
    return render_template("add.html", exercises=all_exercises, muscle_groups=muscle_groups)

#view past workouts by chosen date
@app.route("/history", methods=["GET", "POST"])
def history():
    if request.method == "POST":
        chosen_date = request.form.get("date")
        sets = get_specific_day(chosen_date)
        muscle_counts = summarize_muscles(sets)
        return render_template("history.html", sets=sets, chosen_date=chosen_date, muscle_counts=muscle_counts)
    
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

    return render_template("summary.html", sets=sets, today=today, muscle_counts=muscle_counts)

@app.route("/settings", methods=["GET", "POST"])
def settings():
    if request.method == "POST":
        #will add optional settings later
        pass
        return render_template("settings.html")
    return render_template("settings.html")

#temp for testing
@app.route("/delete-db")
def delete_db():
    clear_database()
    return redirect(url_for("index"))
