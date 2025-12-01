# 🐐 Monty Hall Simulation

A Python-based statistical simulation of the famous **Monty Hall Problem**. This project runs thousands of randomized trials to empirically prove the counter-intuitive probability that switching doors doubles your chances of winning.

[Image of 3 doors: 1 Car, 2 Goats]

## ❓ What is the Monty Hall Problem?

Based on the TV game show *Let's Make a Deal* and named after its host, Monty Hall, the problem is a famous probability puzzle:

1.  There are **3 doors**. Behind one is a **Car** (prize); behind the other two are **Goats**.
2.  You pick a door (e.g., Door 1).
3.  The host, who knows what is behind the doors, opens another door (e.g., Door 3) which has a **Goat**.
4.  The host asks you: **"Do you want to switch to Door 2?"**

### The Paradox

Most people intuitively feel the odds are 50/50. However, probability theory states:

  * **Staying** gives you a $\frac{1}{3}$ ($\approx 33.3\%$) chance of winning.
  * **Switching** gives you a $\frac{2}{3}$ ($\approx 66.6\%$) chance of winning.

This simulation proves this math through brute-force trials.

-----

## 🚀 Features

  * **Configurable Trials:** Run anywhere from 10 to 1,000,000+ simulations to see the Law of Large Numbers in action.
  * **Strategy Comparison:** Automatically runs both "Always Stay" and "Always Switch" strategies side-by-side.
  * **Visual Output:** Generates clear text summaries (and optionally supports Matplotlib graphs).
  * **Performance:** Optimized using Python sets for fast lookup and random selection.

-----

## 📂 Project Structure

```text
monty-hall-simulation/
│
├── src/
│   ├── __init__.py
│   ├── simulation.py    # Core logic (door setup, switching logic)
│   └── visualizer.py    # (Optional) Graphing utilities
│
├── main.py              # Entry point for the CLI
├── requirements.txt     # Dependencies (e.g., matplotlib)
└── README.md
```

-----

## 🛠️ Installation

1.  **Clone the repository:**

    ```bash
    git clone https://github.com/masoudsalkhorde/python-projects/monty-hall-simulation.git
    cd monty-hall-simulation
    ```

2.  **Install dependencies (optional):**
    If you plan to use visualization/graphs:

    ```bash
    pip install matplotlib
    ```

-----

## 💻 Usage

### Command Line Interface

You can run the simulation directly from the terminal. The default runs 1,000 trials.

```bash
python main.py
```

**Custom Number of Trials:**
Pass the number of iterations as an argument to improve accuracy.

```bash
python main.py --trials 100000
```

### Example Output

```text
--- Monty Hall Simulation Results (100,000 trials) ---

Strategy: ALWAYS STAY
Wins:   33,315
Losses: 66,685
Win Rate: 33.31%

Strategy: ALWAYS SWITCH
Wins:   66,648
Losses: 33,352
Win Rate: 66.65%

Conclusion: Switching was 2.00x more effective than staying.
```

## 🤝 Contributing
Contributions are welcome!

Fork the Project

Create your Feature Branch (git checkout -b feature/NewFeature)

Commit your Changes (git commit -m 'Add NewFeature')

Push to the Branch (git push origin feature/NewFeature)

Open a Pull Request

## 📄 License
Distributed under the MIT License. See LICENSE for more information.