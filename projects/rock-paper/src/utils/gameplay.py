class GamePlay():

    def __init__(self, player_choice, computer_choice):
        """_summary_

        :param player_choice: _description_
        :type player_choice: _type_
        :param computer_choice: _description_
        :type computer_choice: _type_
        """
        self.player_choice = player_choice.lower()
        self.computer_choice = computer_choice.lower()
        self.selection = []
        self.selection.append(self.player_choice)
        self.selection.append(self.computer_choice)
    
    def find_winner(self):
        if self.selection[0] == self.selection[1]:
            return "tie"
        elif "rock" in self.selection and "scisors" in self.selection:
            return "rock"
        elif "rock" in self.selection and "paper" in self.selection:
            return "paper"
        elif "paper" in self.selection and "scisors" in self.selection:
            return "scisors"