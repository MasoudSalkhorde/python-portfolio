# Happy Numbers Validator 🐍

![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)

A lightweight, efficient Python project to determine if a positive integer is a **Happy Number**. This tool can check individual numbers or generate a list of happy numbers within a specific range.

## 📖 What is a Happy Number?

In number theory, a happy number is a number which eventually reaches **1** when replaced by the sum of the square of each of its digits.



**The Process:**
1. Start with any positive integer.
2. Replace the number with the sum of the squares of its digits.
3. Repeat the process.
4. If the result is **1**, the number is **Happy**.
5. If the result loops endlessly in a cycle (that does not include 1), the number is **Unhappy** (or Sad).

**Example:** $19$ is a Happy Number.
1. $1^2 + 9^2 = 82$
2. $8^2 + 2^2 = 68$
3. $6^2 + 8^2 = 100$
4. $1^2 + 0^2 + 0^2 = 1$ (Happy!)

## ✨ Features

* **Single Check:** instantly validates if a specific input is happy.
* **Range Search:** Finds all happy numbers between `1` and `N`.
* **Cycle Detection:** Uses a Hash Set (O(1) lookups) to detect infinite loops efficiently, preventing the program from hanging on Unhappy numbers.
* **Input Validation:** Handles non-integer or negative inputs gracefully.

## 📂 Project Structure
```
happy-numbers/
│
├── src/
│   ├── happy_numbers.py
├── requirements.txt     # 
└── README.md
```

## 🚀 Installation

No external dependencies are required. This project runs on standard Python.

1. **Clone the repository:**
   ```bash
   git clone [https://github.com/masoudsalkhorde/python-projects/happy-numbers]
   cd src

1. **Run the script:**
python happy-numbers.py

## 🤝 Contributing
Contributions are welcome! If you have ideas for optimization or visualization:

1- Fork the Project

2- Create your Feature Branch (git checkout -b feature/AmazingFeature)

3- Commit your Changes (git commit -m 'Add some AmazingFeature')

4- Push to the Branch (git push origin feature/AmazingFeature)

5- Open a Pull Request

## 📄 License
Distributed under the MIT License. See LICENSE for more information.