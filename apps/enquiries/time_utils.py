from datetime import time


def get_time_choices():
    """
    Generate time choices in 30-minute increments from 11:00 to 23:59.
    Midnight (23:59) is considered the next day.

    Returns a list of tuples: [(time_object, display_string), ...]
    """
    choices = []

    # Generate 30-minute intervals from 11:00 to 23:30
    hour = 11
    minute = 0

    while hour < 24:
        current_time = time(hour, minute)
        display = current_time.strftime("%H:%M")
        choices.append((current_time, display))

        # Increment by 30 minutes
        minute += 30
        if minute == 60:
            minute = 0
            hour += 1

    # Add 23:59 as the final option (representing midnight of next day)
    choices.append((time(23, 59), "23:59 (next day)"))

    return choices





