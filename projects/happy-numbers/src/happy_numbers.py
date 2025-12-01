def is_happy(n: int) -> bool:
    seen = set()  # hash set to store visited numbers

    while n != 1:
        if n in seen:
            return False  # loop detected → unhappy number

        seen.add(n)

        # compute next number (sum of squares of digits)
        n = sum(int(digit) ** 2 for digit in str(n))

    return True  # reached 1 → happy number

number_to_check = int(input("Please enter the number:\n"))

if is_happy(number_to_check):
    print("The number is a happy number")
else:
    print("This is not a happy number")