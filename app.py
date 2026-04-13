import random
import os
import streamlit as st
from dotenv import load_dotenv

from logic_utils import (
    ai_coach_suggestion,
    check_guess,
    get_range_for_difficulty,
    parse_guess,
    update_possible_range,
    update_score,
)

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

st.set_page_config(page_title="Glitchy Guesser", page_icon="🎮")

st.title("🎮 Game Glitch Investigator")

st.sidebar.header("Settings")

difficulty = st.sidebar.selectbox(
    "Difficulty",
    ["Easy", "Normal", "Hard"],
    index=1,
)

attempt_limit_map = {
    "Easy": 6,
    "Normal": 8,
    "Hard": 5,
}
attempt_limit = attempt_limit_map[difficulty]

low, high = get_range_for_difficulty(difficulty)

st.sidebar.caption(f"Range: {low} to {high}")
st.sidebar.caption(f"Attempts allowed: {attempt_limit}")

if (
    "difficulty" not in st.session_state
    or st.session_state.difficulty != difficulty
):
    st.session_state.difficulty = difficulty
    st.session_state.secret = random.randint(low, high)
    st.session_state.attempts = 0
    st.session_state.score = 0
    st.session_state.status = "playing"
    st.session_state.history = []
    st.session_state.possible_low = low
    st.session_state.possible_high = high
    st.session_state.last_outcome = ""

if "secret" not in st.session_state:
    st.session_state.secret = random.randint(low, high)

if "attempts" not in st.session_state:
    st.session_state.attempts = 0

if "score" not in st.session_state:
    st.session_state.score = 0

if "status" not in st.session_state:
    st.session_state.status = "playing"

if "history" not in st.session_state:
    st.session_state.history = []

if "possible_low" not in st.session_state:
    st.session_state.possible_low = low

if "possible_high" not in st.session_state:
    st.session_state.possible_high = high

if "last_outcome" not in st.session_state:
    st.session_state.last_outcome = ""

st.subheader("Make a guess")

st.info(
    f"Guess a number between {low} and {high}. "
    f"Attempts left: {attempt_limit - st.session_state.attempts}"
)

with st.expander("Developer Debug Info"):
    st.write("Secret:", st.session_state.secret)
    st.write("Attempts:", st.session_state.attempts)
    st.write("Score:", st.session_state.score)
    st.write("Difficulty:", difficulty)
    st.write("Possible range:", (st.session_state.possible_low, st.session_state.possible_high))
    st.write("Last outcome:", st.session_state.last_outcome)
    st.write("History:", st.session_state.history)

raw_guess = st.text_input(
    "Enter your guess:",
    key=f"guess_input_{difficulty}"
)

col1, col2, col3 = st.columns(3)
with col1:
    submit = st.button("Submit Guess 🚀")
with col2:
    new_game = st.button("New Game 🔁")
with col3:
    show_hint = st.checkbox("Show hint", value=True)

with st.sidebar.expander("AI Coach", expanded=False):
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    st.caption("Optional: set GEMINI_API_KEY to enable Gemini.")
    ai_enabled = st.checkbox("Enable AI Coach", value=bool(api_key))
    ai_button = st.button("Get AI suggestion")
    if ai_button:
        attempts_left = attempt_limit - st.session_state.attempts
        suggested, advice, confidence, source, reason = ai_coach_suggestion({
            "api_key": api_key if ai_enabled else "",
            "low": int(st.session_state.possible_low),
            "high": int(st.session_state.possible_high),
            "history": list(st.session_state.history),
            "last_outcome": st.session_state.last_outcome,
            "attempts_used": int(st.session_state.attempts),
            "attempts_left": int(attempts_left),
        })
        st.write(f"Suggestion: {suggested}" if suggested is not None else "Suggestion: (none)")
        if advice:
            st.write(advice)
        st.caption(f"source={source} confidence={confidence:.2f}")
        if source == "fallback" and ai_enabled and api_key:
            st.caption(f"fallback_reason={reason}")

if new_game:
    st.session_state.attempts = 0
    st.session_state.secret = random.randint(low, high)
    st.session_state.score = 0
    st.session_state.status = "playing"
    st.session_state.history = []
    st.session_state.possible_low = low
    st.session_state.possible_high = high
    st.session_state.last_outcome = ""
    st.success("New game started.")
    st.rerun()

if st.session_state.status != "playing":
    if st.session_state.status == "won":
        st.success("You already won. Start a new game to play again.")
    else:
        st.error("Game over. Start a new game to try again.")
    st.stop()

if submit:
    ok, guess_int, err = parse_guess(raw_guess)

    if not ok:
        st.session_state.history.append(raw_guess)
        st.error(err)
    else:
        st.session_state.attempts += 1
        st.session_state.history.append(guess_int)

        outcome = check_guess(guess_int, st.session_state.secret)
        st.session_state.last_outcome = outcome
        st.session_state.possible_low, st.session_state.possible_high = update_possible_range(
            st.session_state.possible_low,
            st.session_state.possible_high,
            guess_int,
            outcome,
        )
        if outcome == "Win":
            message = "🎉 Correct!"
        elif outcome == "Too High":
            message = "📉 Go LOWER!"
        else:
            message = "📈 Go HIGHER!"

        if show_hint:
            st.warning(message)

        st.session_state.score = update_score(
            current_score=st.session_state.score,
            outcome=outcome,
            attempt_number=st.session_state.attempts,
        )

        if outcome == "Win":
            st.balloons()
            st.session_state.status = "won"
            st.success(
                f"You won! The secret was {st.session_state.secret}. "
                f"Final score: {st.session_state.score}"
            )
        else:
            if st.session_state.attempts >= attempt_limit:
                st.session_state.status = "lost"
                st.error(
                    f"Out of attempts! "
                    f"The secret was {st.session_state.secret}. "
                    f"Score: {st.session_state.score}"
                )

st.divider()
