import random
from nltk.corpus import words as nltk_words
from src.password_classes.password_generator import PasswordGenerator

class MemorableGenerator(PasswordGenerator):
    def __init__(self):
        super().__init__()

        all_words = nltk_words.words()

        self.raw_words = all_words

        self.full_words = [
            w.lower()
            for w in all_words
            if w.isalpha() and len(w) >= 4
        ]

        self.separators = {
            "Hyphen": "-",
            "Underline": "_",
            "Comma": ",",
            "Pipe": "|",
        }

    def generate(self, num_words=4, separator="Hyphen", use_full_words=True, capitalized=True):
        sep = self.separators.get(separator, "-")

        word_list = self.full_words if use_full_words else self.raw_words

        if num_words < 1:
            raise ValueError("num_words must be at least 1")

        if num_words > len(word_list):
            raise ValueError(
                f"Requested {num_words} words, but only {len(word_list)} available"
            )

        chosen = random.sample(word_list, num_words)
        
        self._password = sep.join(chosen) if capitalized == False else sep.join([w.capitalize() for w in chosen])
        return self._password
