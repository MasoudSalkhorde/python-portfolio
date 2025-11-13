def provide_hint(guess, target):
    """Provides a hint based on the player's guess compared to the target number."""
    if guess < target:
        return "Too low!"
    elif guess > target:
        return "Too high!"
    else:
        return "Correct!"