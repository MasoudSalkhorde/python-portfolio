from abc import ABC, abstractmethod
import random

class PasswordGenerator(ABC):
    """Base class for password generators.
    """
    def __init__(self):
        self._password = ""

    @abstractmethod
    def generate(self, *args, **kwargs) -> str:
        """This is to be implemented by subclasses to generate a password."""
        pass
    
    def _shuffle(self, text: str) -> str:
        """Shuffles the Password string

        :param text: The text to shuffle
        :return: The shuffled text
        """
        return ''.join(random.sample(text, len(text)))
    
    def get_password(self) -> str:
        """The most recently generated password
        :return: Password string
        """
        return self._password
    
    def __str__(self):
        return self._password
