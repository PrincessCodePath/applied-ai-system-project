# 🎮 Game Glitch Investigator: The Impossible Guesser

## Setup

```bash
pip install -r requirements.txt
```

## Run the game

```bash
python -m streamlit run app.py
```

## AI Enhancement: AI Coach (optional)

The app includes an AI Coach that suggests the next guess and explains why, based on your remaining range, guess history, and recent higher/lower hints.

It works without an API key (fallback suggestion), but to enable Gemini suggestions set:

```bash
export GEMINI_API_KEY="your_key_here"
```

## Design and Architecture

### Main components
- **UI**: Streamlit app (`app.py`)
- **Game logic**: parsing guesses, checking outcomes, scoring (`logic_utils.py`)
- **AI Coach**: suggestion + advice (Gemini when available, otherwise fallback) (`logic_utils.py`)
- **Guardrails**: range validation, JSON parsing checks, and fallback reasons (Gemini errors like 429, invalid output, repeats)
- **Testing**: `pytest` tests for core logic (`tests/test_game_logic.py`)

### Data flow (input → process → output)
- Player enters a guess in Streamlit.
- The app validates and records the guess in `st.session_state` (history, attempts, last outcome).
- The game logic updates the outcome and narrows the possible range.
- If the player clicks **Get AI suggestion**, the AI Coach uses:
  - the current possible range
  - guess history + last outcome
  - Gemini (if key + quota allow), otherwise a deterministic fallback
- The app displays a suggestion and explanation, plus `source=gemini` or `source=fallback` with `fallback_reason`.

### System diagram

![image alt](https://github.com/PrincessCodePath/applied-ai-system-project/blob/main/assets/mermaid-ai-diagram-2026-04-13-084033.png)

## Bugs found

### Bug 1: Invalid input consumes an attempt

- Expected: If I type something that isn’t a number (like `abc`) and click submit, it should show an error and not count as an attempt.
- Actual: The game increases the attempt counter even when the input is invalid.
- Cause (code): In `app.py`, `st.session_state.attempts += 1` runs before `parse_guess(raw_guess)` validates the input, so invalid guesses still get counted.

![image alt](https://github.com/PrincessCodePath/applied-ai-system-project/blob/main/assets/Bug%201%20Invalid%20input.png)


### Bug 2: Attempts left starts one lower than expected

- Expected: On a new Normal game with 8 attempts allowed, it should show 8 attempts left before I submit anything.
- Actual: It shows 7 attempts left immediately.
- Cause (code): In `app.py`, attempts is initialized to 1 (`st.session_state.attempts = 1`), and the UI calculates attempts left as `attempt_limit - st.session_state.attempts`, so it starts one lower.

![image alt](https://github.com/PrincessCodePath/applied-ai-system-project/blob/main/assets/Bug%202%20Attempts%20left%20.png)

### Bug 3: New Game does not fully reset state after win/loss

- Expected: After I win or lose, clicking “New Game” should fully reset the game so I can play again (status back to playing, attempts reset, and score/history cleared).
- Actual: After winning/losing, clicking “New Game” can still leave the game stuck in the won/lost state or keep old score/history.
- Cause (code): In `app.py`, the `new_game` button only resets attempts and secret, but it doesn’t reset status, score, or history. The app also stops gameplay when `st.session_state.status != "playing"`.

![image alt](https://github.com/PrincessCodePath/applied-ai-system-project/blob/main/assets/Bug%203%20%E2%80%9CNew%20Game%E2%80%9D.png)

## AI debugging suggestions + critique

- **One correct suggestion (and why it was correct):**  
One correct suggestion was that the attempt counter issue was likely coming from how `attempts` was being initialized and updated. That ended up being correct because `attempts` was starting at `1`, and the UI was immediately subtracting from the attempt limit. That is why the game showed 7 attempts left instead of 8 at the start of a Normal game.
- **One incorrect or misleading suggestion (and why it was wrong):**  
One misleading part of the AI’s response was that it made it seem like the app would naturally continue where I left off every time I reopened it. That was not really true in my testing. `st.session_state` only keeps track of values during the current running session, so once the app is refreshed or restarted, the game does not reliably continue unless that behavior is built in on purpose.

## Fixes applied

Fixes implemented, what changed and why.

### **Fix 1 (Bug 1): Invalid input consumes an attempt**

- **What changed:** I moved the attempt counter update so it only happens after the input successfully parses into a number.
- **Why:** If the guess isn’t valid, it shouldn’t count as a real attempt. This keeps the attempt count fair and matches what the user expects.

### **Fix 2 (Bug 2): Attempts left starts one lower than expected**

- **What changed:** I changed the initial attempts value to start at 0 instead of 1.
- **Why:** The UI calculates “attempts left” as `attempt_limit - attempts`, so starting at 0 makes the first screen show the full amount (Normal starts at 8 attempts left).

### **Fix 3 (Bug 3): New Game does not fully reset state after win/loss**

- **What changed:** When “New Game” is clicked, I reset more state values (status back to playing, score reset, and history cleared) instead of only resetting the secret and attempts.
- **Why:** After a win/loss the app blocks gameplay unless status is “playing,” so the reset needs to fully restart the game, not partially keep the old state.

## Tests

```bash
pytest
```

## Demo

- Screenshot of a winning game after fixes:

![image alt](https://github.com/PrincessCodePath/applied-ai-system-project/blob/main/assets/fixed%20bug%201.png)

![image alt](https://github.com/PrincessCodePath/applied-ai-system-project/blob/main/assets/fixed%20bug%202.png)

![image alt](https://github.com/PrincessCodePath/applied-ai-system-project/blob/
main/assets/fixed%20bug%203.png)

## AI enhancements (intention + usage issues)

### Intention

The goal of the AI Coach feature is to help the player make smarter guesses using the information the game already provides (range, prior guesses, and higher/lower feedback). It also calls out unhelpful patterns like repeating the same guess or making tiny changes when the hint keeps saying to go higher/lower.

### How to use it

- Start the app.
- In the sidebar, open **AI Coach**.
- Click **Get AI suggestion** to get a suggested next guess and a short explanation.
- If `GEMINI_API_KEY` is set, it will try Gemini first. If not, it uses a deterministic fallback.

### Usage issue (quota limits)

Gemini sometimes returns a 429 quota/rate-limit error (free-tier limits). When that happens, the app shows `fallback_reason=gemini_error: 429 ...` and falls back to the built-in heuristic instead of crashing. This makes the feature reliable even when the API is temporarily unavailable. 

![image alt](https://github.com/PrincessCodePath/applied-ai-system-project/blob/main/assets/ai%20enhancements.png)

## Limitations / bias

The AI Coach is not always going to be right. If Gemini is available, it can still give suggestions that sound confident without actually being that helpful. When Gemini is not available, the fallback is just based on the remaining range and previous guesses, so it is much more limited and only works off the rules we built into it. I also noticed that even when the API key is set up correctly, the free-tier limits can still stop the AI feature from working.

## Misuse + how I prevent it

One issue is that a player could trust the AI Coach too much and assume it always knows the best next move. To help with that, the app checks Gemini’s response before using it and rejects suggestions that are invalid, out of range, or repeated. If that happens, it switches to a safer fallback suggestion instead. The point of the AI Coach is to support the player’s thinking, not make the decision for them.

## What surprised me

What surprised me most was how much rate limits actually matter. Even with a real Gemini key, the app can still hit a 429 error, so making the feature work well was not just about prompting. It also meant thinking about what happens when the API fails and making sure there was still a backup plan.

## AI collaboration (helpful + flawed)

One helpful thing the AI pointed out was that the attempts counter issue was probably coming from how attempts was being initialized and updated, and that ended up leading me to the fix. One thing it got wrong was making it seem like the app would automatically continue where I left off every time I reopened it. Streamlit state only lasts within the current session unless you build in a separate way to save it.
