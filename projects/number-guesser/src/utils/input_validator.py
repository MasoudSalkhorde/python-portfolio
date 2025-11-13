def get_valid_input(start, end):
    """
    Prompts the user for input until a valid option is provided.

    Args:
        prompt (str): The message displayed to the user.
        start (int): The start of the valid input range.
        end (int): The end of the valid input range.
    """
    while True:
        try:
            user_input = int(input("Enter a number: "))
            if start <= user_input <= end:
                return user_input
            else:
                print(f"Input must be between {start} and {end}. Please try again.")
                continue
        except ValueError:
            print("Invalid input. Please enter a number.")
            continue
        
if __name__ == "__main__":
    valid_input = get_valid_input(1, 10)
    print(f"You entered a valid number: {valid_input}")
    