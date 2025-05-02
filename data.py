#exercises on left associated muscle groups on right
presaved_exercises = [
    {"name": "Bench Press", "muscle": "Chest"},
    {"name": "Barbell Squat", "muscle": "Legs"},
    {"name": "Shoulder Press", "muscle": "Shoulders"},
]

def summarize_muscles(sets):
    muscle_map = {e["name"]: e["muscle"] for e in presaved_exercises}

    muscle_counts = {}
    for s in sets:
        exercise_name = s[1]

        # Try to match a presaved exercise first
        muscle = muscle_map.get(exercise_name)

        # If not found, try to extract from "(Muscle)"
        if not muscle and "(" in exercise_name and ")" in exercise_name:
            muscle = exercise_name.split("(")[-1].split(")")[0].strip()

        if not muscle:
            muscle = "Unknown"

        muscle_counts[muscle] = muscle_counts.get(muscle, 0) + 1

    return muscle_counts

