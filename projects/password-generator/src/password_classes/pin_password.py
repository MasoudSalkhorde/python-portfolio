import random
from src.password_classes.password_generator import PasswordGenerator


class PinGenerator(PasswordGenerator):
    """Subclass of PasswordGenerator to generate pin passwords using integer numbers.
    """
    def __init__(self):
        super().__init__()
        self.numbers = "0123456789" 

    def generate(self, length=4) -> str:
        """Generates a PIN password

        :param length: Number of digits in the password, defaults to 4
        :type length: int, optional
        :return: A pin password
        """
        if length < 1:
            raise ValueError("PIN length must be at least 1")

        self._password = ''.join(
            random.choice(self.numbers) for _ in range(length)
        )

        return self._password
