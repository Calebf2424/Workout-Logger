#exercises on left associated muscle groups on right
presaved_exercises = [
    {"name": "Bench Press", "muscle": "Chest"},
    {"name": "Barbell Squat", "muscle": "Legs"},
    {"name": "Shoulder Press", "muscle": "Shoulders"},
]

def summarize_muscles(sets):
    # Create a name → muscle lookup
    muscle_map = {e["name"]: e["muscle"] for e in presaved_exercises}

    muscle_counts = {}
    for s in sets:
        exercise_name = s[1]  # index 1 = exercise name
        muscle = muscle_map.get(exercise_name, "Unknown")
        muscle_counts[muscle] = muscle_counts.get(muscle, 0) + 1

    return muscle_counts
