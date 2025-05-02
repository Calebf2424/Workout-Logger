#exercises on left associated muscle groups on right
presaved_exercises = [
    {"name": "Hip Abduction Machine", "approx": "Legs", "precise": "Abductors"},
    {"name": "Crunch", "approx": "Core", "precise": "Abs"},
    {"name": "Ab Crunch Machine", "approx": "Core", "precise": "Abs"},
    {"name": "Cable Crunch", "approx": "Core", "precise": "Abs"},
    {"name": "Hanging Leg Raise", "approx": "Core", "precise": "Abs"},
    {"name": "Hip Adduction Machine", "approx": "Legs", "precise": "Adductors"},
    {"name": "Cable Adduction", "approx": "Legs", "precise": "Adductors"},
    {"name": "Hammer Curl", "approx": "Arms", "precise": "Biceps"},
    {"name": "Incline Dumbbell Curl", "approx": "Arms", "precise": "Biceps"},
    {"name": "Barbell Curl", "approx": "Arms", "precise": "Biceps"},
    {"name": "Cable Curl", "approx": "Arms", "precise": "Biceps"},
    {"name": "Preacher Curl Machine", "approx": "Arms", "precise": "Biceps"},
    {"name": "Standing Calf Raise", "approx": "Legs", "precise": "Calves"},
    {"name": "Seated Calf Raise", "approx": "Legs", "precise": "Calves"},
    {"name": "Standing Calf Raise Machine", "approx": "Legs", "precise": "Calves"},
    {"name": "Seated Calf Raise Machine", "approx": "Legs", "precise": "Calves"},
    {"name": "Pec Deck", "approx": "Chest", "precise": "Chest"},
    {"name": "Machine Chest Press", "approx": "Chest", "precise": "Chest"},
    {"name": "Smith Machine Bench Press", "approx": "Chest", "precise": "Chest"},
    {"name": "Bench Press", "approx": "Chest", "precise": "Chest"},
    {"name": "Chest Fly", "approx": "Chest", "precise": "Chest"},
    {"name": "Push-Up", "approx": "Chest", "precise": "Chest"},
    {"name": "Back Extension Machine", "approx": "Back", "precise": "Erectors"},
    {"name": "Deadlift", "approx": "Back", "precise": "Erectors"},
    {"name": "Machine Shoulder Press", "approx": "Shoulders", "precise": "Front Delts"},
    {"name": "Overhead Press", "approx": "Shoulders", "precise": "Front Delts"},
    {"name": "Front Raise", "approx": "Shoulders", "precise": "Front Delts"},
    {"name": "Hip Thrust", "approx": "Legs", "precise": "Glutes"},
    {"name": "Glute Kickback", "approx": "Legs", "precise": "Glutes"},
    {"name": "Standing Glute Kickback Machine", "approx": "Legs", "precise": "Glutes"},
    {"name": "Leg Curl", "approx": "Legs", "precise": "Hamstrings"},
    {"name": "Lying Leg Curl Machine", "approx": "Legs", "precise": "Hamstrings"},
    {"name": "Romanian Deadlift", "approx": "Legs", "precise": "Hamstrings"},
    {"name": "Pull-Up", "approx": "Back", "precise": "Lats"},
    {"name": "Lat Pulldown", "approx": "Back", "precise": "Lats"},
    {"name": "Assisted Pull-Up Machine", "approx": "Back", "precise": "Lats"},
    {"name": "Lat Pullover Machine", "approx": "Back", "precise": "Lats"},
    {"name": "Decline Bench Press", "approx": "Chest", "precise": "Lower Chest"},
    {"name": "Cable Woodchopper", "approx": "Core", "precise": "Obliques"},
    {"name": "Russian Twist", "approx": "Core", "precise": "Obliques"},
    {"name": "Rotary Torso Machine", "approx": "Core", "precise": "Obliques"},
    {"name": "Leg Press", "approx": "Legs", "precise": "Quads"},
    {"name": "Barbell Squat", "approx": "Legs", "precise": "Quads"},
    {"name": "Leg Extension Machine", "approx": "Legs", "precise": "Quads"},
    {"name": "Hack Squat", "approx": "Legs", "precise": "Quads"},
    {"name": "Smith Machine Squat", "approx": "Legs", "precise": "Quads"},
    {"name": "Reverse Pec Deck", "approx": "Shoulders", "precise": "Rear Delts"},
    {"name": "Bent-Over Lateral Raise", "approx": "Shoulders", "precise": "Rear Delts"},
    {"name": "Machine Rear Delt Fly", "approx": "Shoulders", "precise": "Rear Delts"},
    {"name": "Barbell Row", "approx": "Back", "precise": "Rhomboids"},
    {"name": "Seated Cable Row", "approx": "Back", "precise": "Rhomboids"},
    {"name": "Seated Row Machine", "approx": "Back", "precise": "Rhomboids"},
    {"name": "Cable Lateral Raise", "approx": "Shoulders", "precise": "Side Delts"},
    {"name": "Lateral Raise", "approx": "Shoulders", "precise": "Side Delts"},
    {"name": "Shrug", "approx": "Back", "precise": "Traps"},
    {"name": "Face Pull", "approx": "Back", "precise": "Traps"},
    {"name": "Triceps Dip Machine", "approx": "Arms", "precise": "Triceps"},
    {"name": "Close-Grip Bench Press", "approx": "Arms", "precise": "Triceps"},
    {"name": "Triceps Pushdown", "approx": "Arms", "precise": "Triceps"},
    {"name": "Cable Triceps Pushdown", "approx": "Arms", "precise": "Triceps"},
    {"name": "Overhead Triceps Extension", "approx": "Arms", "precise": "Triceps"},
    {"name": "Incline Bench Press", "approx": "Chest", "precise": "Upper Chest"},
    {"name": "Hyperextensions", "approx": "Legs", "precise": "Hamstrings"}

]

def summarize_muscles(sets, precise=True):
    # Map known exercises to their muscle group
    muscle_map = {
        e["name"]: (e["precise"] if precise else e["approx"])
        for e in presaved_exercises
    }

    muscle_counts = {}
    for s in sets:
        exercise_name = s[1]

        # Check if it's a known exercise
        muscle = muscle_map.get(exercise_name)

        # Handle custom format: "Name||Precise||" or "Name||||Approx"
        if not muscle and "||" in exercise_name:
            parts = exercise_name.split("||")
            # [0] is the name, [1] is precise, [3] is approx
            if precise and len(parts) > 1:
                muscle = parts[1].strip()
            elif not precise and len(parts) > 3:
                muscle = parts[3].strip()

        if not muscle:
            muscle = "Unknown"

        muscle_counts[muscle] = muscle_counts.get(muscle, 0) + 1

    return muscle_counts



