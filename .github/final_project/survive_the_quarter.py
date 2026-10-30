# My name is Alexandra Gerasimova, my group letter is A (DESMI Python CL01).

#description:
# Separator: Comma
#Column	Description
# 1. ID	Unique scenario number
# 2. Scenario	Description of the situation
# 3. OptionA, B, C	Three possible decisions
# 4. BudgetA, B, C	Budget change for each decision (EUR)
# 5. ReputationA, B, C	Reputation change for each decision (points)
# 6. FeedbackA, B, C	Feedback explaining the consequences

# What happens? — Steps of one day
#One day represents one business decision made by the player.
#    1. The game loads the next scenario from the CSV file.
#    2. The player reads the business situation.
#    3. Three possible decisions (A, B, C) are displayed.
#    4. The player selects one option.
#    5. The game retrieves the corresponding budget and reputation changes.
#    6. The budget and reputation gauges are updated.
#    7. The game displays feedback explaining the consequences of the decision.
#    8. The day number increases, and the player's decision and updated statistics are saved in results.csv.
#    9. The next scenario is presented.
# This process repeats until all scenarios have been completed.

#3. What comes out? — Output
#What the player sees at the end:
#- Final budget (EUR).
#- Final reputation score.
#- Total number of days played.
#- A summary of the decisions made.
#- Final feedback or an overall performance message.

# 4. What could go wrong? — Potential problems and solutions
# Potential problem	How to handle it
# 1. Missing CSV file	Check whether the file exists before loading it. If missing, display an error message and stop the game safely.
# 2. Invalid player input	Accept only A, B or C. If the player enters something else, ask them to try again without changing the gauges.
# 3. Budget or reputation falls below zero	Prevent negative values by setting the minimum gauge value to zero, or display a game-over message if the budget reaches zero.
# 4. Invalid numbers in the CSV	Check that budget and reputation fields contain valid integers. If a value is invalid, report the problematic scenario and do not apply the decision.
# 5. Missing or incorrect CSV columns	Validate the column names before starting the game. If required columns are missing, display a clear error message.
# 6. Results file cannot be saved	Handle file-writing errors, inform the player and avoid losing the game state.

import csv
import os
import random
from datetime import date
 
# Settings of the game (change them here, not inside the code)
# Files are looked for next to this script, whatever folder the terminal is in
BASE_FOLDER = os.path.dirname(os.path.abspath(__file__))
SCENARIO_FILE = os.path.join(BASE_FOLDER, "scenarios_A.csv")
RESULTS_FILE = os.path.join(BASE_FOLDER, "results.csv")
START_BUDGET = 10000
START_REPUTATION = 50
MAX_REPUTATION = 100
DAYS = 10
STREAK_LENGTH = 3
STREAK_BONUS = 500
 
 
# Read the scenario file and turn every row into a scenario.
# A scenario is (situation, [option_A, option_B, option_C]) and each option
# is a tuple: (text, budget_change, reputation_change, feedback)
def load_scenarios(filename):
    scenarios = []
    try:
        with open(filename, newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f, delimiter=",")
            for row in reader:
                try:
                    options = []
                    for letter in "ABC":
                        option = (
                            row["Option" + letter],
                            int(row["Budget" + letter]),
                            int(row["Reputation" + letter]),
                            row["Feedback" + letter],
                        )
                        options.append(option)
                    scenarios.append((row["Scenario"], options))
                except (KeyError, ValueError, TypeError):
                    # one bad row should not kill the whole game
                    print("Skipping a broken row (ID:", row.get("ID"), ")")
    except (FileNotFoundError, OSError):
        print("Cannot open", filename)
    return scenarios
 
 
# Ask for A, B or C until the answer is valid. Lowercase is accepted.
def ask_choice():
    answer = input("Your choice (A, B or C): ").strip().upper()
    while answer not in ("A", "B", "C"):
        answer = input("Please type A, B or C: ").strip().upper()
    return answer
 
 
# Apply one option to the gauges and return the new values (a tuple).
# Reputation can never go above 100.
def apply_choice(budget, reputation, option):
    text, budget_change, reputation_change, feedback = option
    budget = budget + budget_change
    reputation = min(MAX_REPUTATION, reputation + reputation_change)
    return budget, reputation
 
 
# Show the header of one day: number, gauges, situation and the three options
def show_day(day, budget, reputation, situation, options):
    print()
    print("--- Day", day, "---")
    print("[Budget:", budget, "EUR | Reputation:", str(reputation) + "/" + str(MAX_REPUTATION) + "]")
    print(situation)
    for letter, option in zip("ABC", options):
        print(" ", letter + ":", option[0])
 
 
# Turn the final numbers into a score and a title
def get_title(budget, reputation):
    score = reputation + budget // 200
    if score < 95:
        title = "Eternal Intern"
    elif score < 120:
        title = "Growth Hacker"
    elif score < 140:
        title = "CMO Material"
    else:
        title = "Viral Legend"
    return score, title
 
 
# Feature (a): count reputation gains in a row.
# Returns (new_streak, bonus). After 3 gains in a row the bonus is 500 and the streak restarts.
def check_streak(streak, reputation_change):
    if reputation_change > 0:
        streak = streak + 1
    else:
        streak = 0
    if streak == STREAK_LENGTH:
        return 0, STREAK_BONUS
    return streak, 0
 
 
# Best and worst move = biggest and smallest reputation change.
# history holds one tuple per day: (reputation_change, day, option_text).
# Python compares tuples starting with the first element, so max() and min() work directly.
def best_and_worst(history):
    return max(history), min(history)
 
 
# Add one line to results.csv: name, budget, reputation, title, date
def save_result(name, budget, reputation, title):
    try:
        with open(RESULTS_FILE, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([name, budget, reputation, title, date.today().isoformat()])
        print("Saved in", RESULTS_FILE)
    except OSError:
        print("Could not write", RESULTS_FILE, "- your result was not saved.")
 
 
# Play the whole game
def main():
    scenarios = load_scenarios(SCENARIO_FILE)
    if len(scenarios) == 0:
        print("No scenario to play. Game stopped.")
        return
 
    name = input("What is your name? ").strip()
    if name == "":
        name = "Player"
 
    budget = START_BUDGET
    reputation = START_REPUTATION
    history = []
    streak = 0
    fired_reason = ""
 
    random.shuffle(scenarios)
    days_to_play = min(DAYS, len(scenarios))
 
    for day in range(1, days_to_play + 1):
        situation, options = scenarios[day - 1]
        show_day(day, budget, reputation, situation, options)
 
        letter = ask_choice()
        option = options["ABC".index(letter)]
        budget, reputation = apply_choice(budget, reputation, option)
 
        print(option[3])
        print("Budget", format(option[1], "+d"), "EUR, Reputation", format(option[2], "+d"))
        history.append((option[2], day, option[0]))
 
        # streak bonus: three reputation gains in a row give 500 EUR
        streak, bonus = check_streak(streak, option[2])
        if bonus > 0:
            budget = budget + bonus
            print("Streak bonus! Budget +" + str(bonus), "EUR")
 
        # game over: stop at once
        if budget <= 0:
            fired_reason = "your budget hit zero"
            break
        if reputation <= 0:
            fired_reason = "your reputation hit zero"
            break
 
    print()
    print("=" * 30)
    if fired_reason != "":
        title = "Fired"
        print("You are fired:", fired_reason + ".")
        print("Budget:", budget, "EUR, reputation:", str(reputation) + "/" + str(MAX_REPUTATION))
    else:
        score, title = get_title(budget, reputation)
        print("Quarter survived!")
        print("Budget left:", budget, "EUR, reputation:", str(reputation) + "/" + str(MAX_REPUTATION))
        print("Final score:", score)
        print(name + ", your title:", title)
 
    best, worst = best_and_worst(history)
    print(f'Best move: day {best[1]}, "{best[2]}" ({best[0]:+d})')
    print(f'Worst move: day {worst[1]}, "{worst[2]}" ({worst[0]:+d})')
 
    save_result(name, budget, reputation, title)
 
 
if __name__ == "__main__":
    try:
        main()
    except (EOFError, KeyboardInterrupt):
        print("\nGame interrupted. Bye!")