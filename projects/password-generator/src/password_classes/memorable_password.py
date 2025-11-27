import random
from nltk.corpus import words as nltk_words
from src.password_classes.password_generator import PasswordGenerator

class MemorableGenerator(PasswordGenerator):
    """Subclass of PasswordGenerator to generate memorable passwords using words from the NLTK words corpus.
    """
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

    def generate(self, num_words=4, separator="Hyphen", use_full_words=True, capitalized=True) -> str:
        """Generates a memorable password

        :param num_words: The number of words included in the password, defaults to 4
        :type num_words: int, optional
        :param separator: The separator used to separete the words in the password, defaults to "Hyphen"
        :type separator: str, optional
        :param use_full_words: User's choice to use full words, defaults to True
        :type use_full_words: bool, optional
        :param capitalized: User's choice to capatilize the words, defaults to True
        :type capitalized: bool, optional
        :return: A memorable password
        """
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
