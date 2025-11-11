from random import randint


number_to_guess = randint(1, 100)
attempts = 0
print("Welcome to the Number Guesser Game!")

while True:
    user_input = input("Please enter your guess (between 1 and 100) or type 'exit' to quit: ")
    
    if user_input.lower() == 'exit':
        print("Thank you for playing! Goodbye!")
        break
    
    try:
        guess = int(user_input)
        if guess < 1 or guess > 100:
            print("Your guess is out of bounds. Please try again.")
            continue
    except ValueError:
        print("Invalid input. Please enter a number between 1 and 100.")
        continue
    
    attempts += 1
    
    if guess < number_to_guess:
        print("Too low! Try again.")
    elif guess > number_to_guess:
        print("Too high! Try again.")
    else:
        print(f"Congratulations! You've guessed the number {number_to_guess} in {attempts} attempts.")
        break