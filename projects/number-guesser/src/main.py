from src.utils.input_validator import get_valid_input
from src.game_logic.number_generator import generate_number
from src.game_logic.hint_generator import provide_hint
from src.game_logic.scorer import Scorer

def main():
    score = Scorer()
    target_number = generate_number(1, 100)
    print("Welcome to the Number Guessing Game!")
    while True:
        user_input = get_valid_input(1, 100)
        hint = provide_hint(user_input, target_number)
        print(hint)
        if hint == "Correct!":
            print(f"Congratulations! Your final score is: {score.get_score()}")
            continue_the_game = input("Do you want to play again? (yes/no): ").strip().lower()
            if continue_the_game == 'yes':
                target_number = generate_number(1, 100)
                score = Scorer()
                print("New game started! Guess the new number.")
                continue
            else:   
                print("Thank you for playing! Goodbye!")
                break
        else:
            score.decrement_score(10)
            
            
if __name__ == "__main__":
    main()