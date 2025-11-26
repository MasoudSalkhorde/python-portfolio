import random
from src.password_classes.password_generator import PasswordGenerator


class PinGenerator(PasswordGenerator):
    def __init__(self):
        super().__init__()
        self.numbers = "0123456789" 

    def generate(self, length=4):
        if length < 1:
            raise ValueError("PIN length must be at least 1")

        self._password = ''.join(
            random.choice(self.numbers) for _ in range(length)
        )

        return self._password
