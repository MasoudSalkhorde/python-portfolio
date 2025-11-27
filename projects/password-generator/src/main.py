from src.password_classes.random_password import RandomGenerator
from src.password_classes.pin_password import PinGenerator
from src.password_classes.memorable_password import MemorableGenerator


def str_to_bool(value: str) -> bool:
    """Takes a string and returns a boolean
    """
    value = value.strip().lower()
    return value in ("true", "t", "yes", "y", "1")


def passkey_generator():
    print("Hi, welcome to the Password Generator Application!\n")

    passkey_type = input(
        "Please select one of these passkey options:\n"
        "  - Random\n"
        "  - Pin\n"
        "  - Memorable\n\n"
        "Your choice: "
    )

    choice = passkey_type.strip().lower()

    if choice.startswith("random"):
        char_num = int(input("\nHow many characters should be included in your password? "))
        has_num = str_to_bool(input("Do you want to include numbers? (True/False or Yes/No): "))
        has_symbol = str_to_bool(input("Do you want to include symbols? (True/False or Yes/No): "))

        passkey = RandomGenerator()
        password = passkey.generate(length=char_num, use_numbers=has_num, use_symbols=has_symbol)
        print(f"\nYour password is: {password}")

    elif choice.startswith("pin"):
        char_num = int(input("\nHow many digits should be included in your PIN? "))
        passkey = PinGenerator()
        password = passkey.generate(length=char_num)
        print(f"\nYour PIN is: {password}")

    elif choice.startswith("memorable"):
        word_num = int(input("\nHow many words should be included in your password? "))
        has_full_words = str_to_bool(
            input("Do you want to use full words? (True/False or Yes/No): ")
        )

        separator = input(
            "Which separator do you want to use?\n"
            "  - Hyphen\n"
            "  - Underline\n"
            "  - Comma\n"
            "  - Pipe\n\n"
            "Your choice: "
        )

        separator = separator.strip().capitalize()

        capitalized = str_to_bool(
            input("Do you want to capitalize each word? (True/False or Yes/No): ")
        )

        passkey = MemorableGenerator()
        password = passkey.generate(
            num_words=word_num,
            separator=separator,
            use_full_words=has_full_words,
            capitalized=capitalized
        )

        print(f"\nYour memorable password is: {password}")

    else:
        print("\nInvalid choice. Please select Random, Pin, or Memorable.")


if __name__ == "__main__":
    passkey_generator()
