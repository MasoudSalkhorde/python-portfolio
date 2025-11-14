from src.utils.player import Player
from src.utils.gameplay import GamePlay

CHOICES = ['rock', 'paper', 'scisors']

player = Player()
computer = Player()

print("Welcome to the game!\n")
counter = 1

while player.score < 3 and computer.score < 3:

    print(f'This is the {counter} round of the game.\n')
    
    user_choice = player.user_choice()
    if user_choice in CHOICES:
        
        computer_choice = computer.random_choice()
        manager = GamePlay(user_choice, computer_choice)
        print(f'\nThe computer chose: {computer_choice}\n')

        if manager.find_winner() == "tie":
            print('This is a tie!\n')
            counter += 1
            continue
        elif manager.find_winner() == user_choice:
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
else:
    print("You won!")

    
    
    