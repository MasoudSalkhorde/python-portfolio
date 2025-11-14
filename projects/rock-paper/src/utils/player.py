import random

CHOICES = ['rock', 'paper', 'scisors']


class Player:
    def __init__(self):
        self.score = 0
        
    def user_choice(self):
        return input("What is your choice? ")
    
    def random_choice(self):
        return random.choice(CHOICES)
    
    def win(self):
        self.score += 1