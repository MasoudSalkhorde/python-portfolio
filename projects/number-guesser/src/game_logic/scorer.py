class Scorer:
    def __init__(self, initial_score=100):
        self.score = initial_score

    def decrement_score(self, pentalty=10):
        self.score -= pentalty
        self.score = max(0, self.score)

    def get_score(self):
        return self.score