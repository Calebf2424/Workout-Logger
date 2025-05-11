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
    {"name": "Leg Curl", "muscle": "Hamstrings"},
    {"name": "Lying Leg Curl Machine", "muscle": "Hamstrings"},
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
    "timezone": "America/Edmonton"  # default to Edmonton
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
