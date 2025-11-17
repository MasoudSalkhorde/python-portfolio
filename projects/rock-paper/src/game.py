from src.utils.player import Player
from src.utils.gameplay import GamePlay

CHOICES = ['rock', 'paper', 'scisors']

player = Player()
computer = Player()

print("Welcome to the game!\n")
counter = 1

while True:

    print(f'This is the {counter} round of the game.\n')
    
    user_choice = player.user_choice()
    if user_choice in CHOICES:
        
        computer_choice = computer.random_choice()
        manager = GamePlay(user_choice, computer_choice)
        print(f'\nThe computer chose: {computer_choice}\n')
        result = manager.find_winner()
        if result == "tie":
            print('This is a tie!\n')
            counter += 1
            continue
        elif result == user_choice:
            player.win()
        else:
            computer.win()
        
        
        print(f'Your score is: {player.score}\n')
        print(f'Computer\'s score is {computer.score}\n')
        
        counter += 1
    
    else:
        print("\nInvalid input. Try again!\n")
        continue
    
    if computer.score == 3:
        print("Computer won!")
        to_continue = input("Do you want to play again? y/n: ")
        if to_continue == "y":
            counter = 1
            player.score = 0
            computer.score = 0
            continue
        else:
            print("Thank you for playting the game")
            break
    elif player.score ==3:
        print("You won!")
        to_continue = input("Do you want to play again? y/n: ")
        if to_continue == "y":
            counter = 1
            player.score = 0
            computer.score = 0
            continue
        else:
            print("Thank you for playting the game")
            break
    
    

