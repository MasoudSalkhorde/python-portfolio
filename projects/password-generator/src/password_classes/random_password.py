import random
import string
from src.password_classes.password_generator import PasswordGenerator

class RandomGenerator(PasswordGenerator):
    """Subclass of PasswordGenerator to generate random passwords using letters, signs, and numbers.
    """
    def __init__(self):
        super().__init__()
        self.numbers = "0123456789"
        self.letters = string.ascii_letters
        self.symbols = string.punctuation

    def generate(self, length: int = 16, use_numbers: bool = False, use_symbols: bool = False) -> str:
        """Generates a random password using letters, signs, and numbers.

        :param length: Length of the password, defaults to 16
        :type length: int, optional
        :param use_numbers: User preference to include numbers in the password, defaults to False
        :type use_numbers: bool, optional
        :param use_symbols: User preference to include symbols in the password, defaults to False
        :type use_symbols: bool, optional
        """
        if length < 1:
            raise ValueError("Password length must be at least 1")

        # CASE 1: letters only
        if not use_numbers and not use_symbols:
            chars = random.sample(self.letters, length)
            self._password = self._shuffle(''.join(chars))
            return self._password

        # Always include at least 1 letter if numbers or symbols are enabled
        char_count = random.choice(range(1, length))
        remaining = length - char_count
        chars = list(random.sample(self.letters, char_count))

        # CASE 2: letters + numbers
        if use_numbers and not use_symbols:
            chars += random.choices(self.numbers, k=remaining)
            self._password = self._shuffle(''.join(chars))
            return self._password

        # CASE 3: letters + symbols
        if not use_numbers and use_symbols:
            chars += random.sample(self.symbols, remaining)
            self._password = self._shuffle(''.join(chars))
            return self._password

        # CASE 4: letters + numbers + symbols
        # remaining here is for numbers + symbols
        if remaining < 2:
            # edge case if length is very small
            raise ValueError("Length too small to include letters, numbers, and symbols")

        num_count = random.choice(range(1, remaining))
        sym_count = remaining - num_count

        chars += random.choices(self.numbers, k=num_count)
        chars += random.sample(self.symbols, sym_count)

        self._password = self._shuffle(''.join(chars))
        return self._password