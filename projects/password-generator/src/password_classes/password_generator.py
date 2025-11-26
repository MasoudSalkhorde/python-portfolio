from abc import ABC, abstractmethod
import random

class PasswordGenerator(ABC):
    def __init__(self):
        self._password = ""

    @abstractmethod
    def generate(self, *args, **kwargs):
        """Generate a password and store it in self._password"""
        pass
    
    def _shuffle(self, text):
        return ''.join(random.sample(text, len(text)))
    
    def get_password(self):
        return self._password
    
    def __str__(self):
        return self._password
