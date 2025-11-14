class GamePlay():

    def __init__(self, player, computer):
        self.player = player.lower()
        self.computer = computer.lower()
        self.selection = []
        self.selection.append(self.player)
        self.selection.append(self.computer)
    
    def find_winner(self):
        if self.selection[0] == self.selection[1]:
            return "tie"
        elif "rock" in self.selection and "scisors" in self.selection:
            return "rock"
        elif "rock" in self.selection and "paper" in self.selection:
            return "paper"
        elif "payper" in self.selection and "scisors" in self.selection:
            return "scisors"