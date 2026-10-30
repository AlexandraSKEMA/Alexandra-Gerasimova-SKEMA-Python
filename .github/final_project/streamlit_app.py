# Streamlit version of Survive the Quarter (group A)
import csv
import os
import random
from datetime import date

import streamlit as st

BASE_FOLDER = os.path.dirname(os.path.abspath(__file__))
SCENARIO_FILE = os.path.join(BASE_FOLDER, "scenarios_A.csv")
RESULTS_FILE = os.path.join(BASE_FOLDER, "results.csv")
START_BUDGET = 10000
START_REPUTATION = 50
MAX_REPUTATION = 100
DAYS = 10
STREAK_LENGTH = 3
STREAK_BONUS = 500

st.set_page_config(page_title="Survive the Quarter", page_icon="🥐")


# Read the CSV: each scenario is (situation, [option_A, option_B, option_C]),
# each option is a tuple (text, budget_change, reputation_change, feedback)
@st.cache_data
def load_scenarios():
    scenarios = []
    with open(SCENARIO_FILE, newline="", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f, delimiter=","):
            try:
                options = [(row["Option" + L], int(row["Budget" + L]),
                            int(row["Reputation" + L]), row["Feedback" + L]) for L in "ABC"]
                scenarios.append((row["Scenario"], options))
            except (KeyError, ValueError, TypeError):
                pass  # skip a broken row
    return scenarios


def apply_choice(budget, reputation, option):
    return budget + option[1], min(MAX_REPUTATION, reputation + option[2])


def check_streak(streak, reputation_change):
    streak = streak + 1 if reputation_change > 0 else 0
    if streak == STREAK_LENGTH:
        return 0, STREAK_BONUS
    return streak, 0


def get_title(budget, reputation):
    score = reputation + budget // 200
    if score < 95:
        return score, "Eternal Intern"
    if score < 120:
        return score, "Growth Hacker"
    if score < 140:
        return score, "CMO Material"
    return score, "Viral Legend"


def save_result(name, budget, reputation, title):
    try:
        with open(RESULTS_FILE, "a", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow([name, budget, reputation, title, date.today().isoformat()])
    except OSError:
        pass


# ---- state changes (called by the buttons) ----
def start_game(name):
    scenarios = load_scenarios()
    order = random.sample(scenarios, min(DAYS, len(scenarios)))
    st.session_state.update(name=name or "Player", budget=START_BUDGET, rep=START_REPUTATION,
                            day=1, history=[], streak=0, order=order, fired="",
                            last=None, phase="day")


def choose(i):
    situation, options = st.session_state.order[st.session_state.day - 1]
    option = options[i]
    budget, rep = apply_choice(st.session_state.budget, st.session_state.rep, option)
    st.session_state.streak, bonus = check_streak(st.session_state.streak, option[2])
    budget += bonus
    st.session_state.history.append((option[2], st.session_state.day, option[0]))
    st.session_state.budget, st.session_state.rep = budget, rep
    if budget <= 0:
        st.session_state.fired = "your budget hit zero"
    elif rep <= 0:
        st.session_state.fired = "your reputation hit zero"
    st.session_state.last = (i, option, bonus)
    st.session_state.phase = "feedback"


def next_day():
    s = st.session_state
    if s.fired or s.day >= len(s.order):
        title = "Fired" if s.fired else get_title(s.budget, s.rep)[1]
        save_result(s.name, s.budget, s.rep, title)
        s.phase = "end"
    else:
        s.day += 1
        s.phase = "day"


def show_gauges():
    s = st.session_state
    c1, c2 = st.columns(2)
    c1.metric("Budget", f"{s.budget} EUR")
    c2.metric("Reputation", f"{s.rep}/{MAX_REPUTATION}")
    st.progress(max(0.0, min(1.0, s.rep / MAX_REPUTATION)))


# ---- screens ----
if "phase" not in st.session_state:
    st.session_state.phase = "start"
s = st.session_state

st.title("Survive the Quarter")

if s.phase == "start":
    st.write("You are the new marketing manager of Croissant Rocket, croissants delivered by drone. "
             "Ten days, two gauges, and one way to get fired: let either of them hit zero.")
    name = st.text_input("What is your name?", max_chars=30)
    if st.button("Start the quarter", type="primary"):
        try:
            start_game(name.strip())
            st.rerun()
        except OSError:
            st.error("Cannot open scenarios_A.csv. Put it next to this file.")

elif s.phase == "day":
    situation, options = s.order[s.day - 1]
    st.subheader(f"Day {s.day} of {len(s.order)}")
    show_gauges()
    st.info(situation)
    for i, letter in enumerate("ABC"):
        st.button(f"{letter}: {options[i][0]}", key=f"opt{i}", on_click=choose, args=(i,),
                  use_container_width=True)

elif s.phase == "feedback":
    situation, options = s.order[s.day - 1]
    i, option, bonus = s.last
    st.subheader(f"Day {s.day} of {len(s.order)}")
    show_gauges()
    st.info(situation)
    st.write(f"You chose **{'ABC'[i]}: {option[0]}**")
    st.write(option[3])
    st.write(f"Budget **{option[1]:+d} EUR**, Reputation **{option[2]:+d}**")
    if bonus:
        st.success(f"Streak bonus! Budget +{bonus} EUR")
    last_day = bool(s.fired) or s.day >= len(s.order)
    st.button("See the result" if last_day else "Next day", on_click=next_day, type="primary")

else:  # end
    if s.fired:
        st.error(f"You are fired: {s.fired}.")
        st.write(f"Budget: {s.budget} EUR, reputation: {s.rep}/{MAX_REPUTATION}")
    else:
        score, title = get_title(s.budget, s.rep)
        st.balloons()
        st.success("Quarter survived!")
        st.write(f"Budget left: {s.budget} EUR, reputation: {s.rep}/{MAX_REPUTATION}")
        st.write(f"Final score: **{score}**")
        st.write(f"{s.name}, your title: **{title}**")
    best, worst = max(s.history), min(s.history)
    st.write(f"Best move: day {best[1]}, “{best[2]}” ({best[0]:+d})")
    st.write(f"Worst move: day {worst[1]}, “{worst[2]}” ({worst[0]:+d})")
    st.button("Play again", on_click=lambda: s.update(phase="start"))
