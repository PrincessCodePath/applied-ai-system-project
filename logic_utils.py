def get_range_for_difficulty(difficulty: str):
    """Return (low, high) inclusive range for a given difficulty."""
    if difficulty == "Easy":
        return 1, 20
    if difficulty == "Normal":
        return 1, 100
    if difficulty == "Hard":
        return 1, 50
    return 1, 100


def parse_guess(raw: str):
    """
    Parse user input into an int guess.

    Returns: (ok: bool, guess_int: int | None, error_message: str | None)
    """
    if raw is None:
        return False, None, "Enter a guess."

    if raw == "":
        return False, None, "Enter a guess."

    try:
        if "." in raw:
            value = int(float(raw))
        else:
            value = int(raw)
    except Exception:
        return False, None, "That is not a number."

    return True, value, None


def check_guess(guess, secret):
    """
    Compare guess to secret and return outcome: "Win", "Too High", or "Too Low".
    """
    if guess == secret:
        return "Win"
    if guess > secret:
        return "Too High"
    return "Too Low"


def update_score(current_score: int, outcome: str, attempt_number: int):
    """Update score based on outcome and attempt number."""
    if outcome == "Win":
        points = 100 - 10 * (attempt_number + 1)
        if points < 10:
            points = 10
        return current_score + points

    if outcome == "Too High":
        if attempt_number % 2 == 0:
            return current_score + 5
        return current_score - 5

    if outcome == "Too Low":
        return current_score - 5

    return current_score


def update_possible_range(low: int, high: int, guess: int, outcome: str):
    if outcome == "Too Low":
        return max(low, guess + 1), high
    if outcome == "Too High":
        return low, min(high, guess - 1)
    return low, high


def heuristic_suggestion(low: int, high: int, guess_history):
    tried = {g for g in guess_history if isinstance(g, int)}
    if low > high:
        return None, "Range is inconsistent. Start a new game."

    mid = (low + high) // 2
    if mid not in tried:
        return mid, f"Try {mid}. It's the middle of the remaining range ({low}–{high})."

    for step in range(1, (high - low) + 1):
        up = mid + step
        down = mid - step
        if up <= high and up not in tried:
            return up, f"Try {up}. It moves away from repeats and stays in ({low}–{high})."
        if down >= low and down not in tried:
            return down, f"Try {down}. It moves away from repeats and stays in ({low}–{high})."

    return None, "You've tried everything in the current range."


def repetition_note(guess_history, last_outcome):
    ints = [g for g in guess_history if isinstance(g, int)]
    if len(ints) < 3:
        return ""
    recent = ints[-3:]
    if len(set(recent)) == 1:
        return "You’ve guessed the same number multiple times. Try something different."
    if last_outcome == "Too Low" and max(recent) <= min(recent):
        return ""
    if last_outcome == "Too Low" and recent[-1] <= recent[-2] <= recent[-3]:
        return "You keep guessing low after a 'go higher' hint. Increase your guess more."
    if last_outcome == "Too High" and recent[-1] >= recent[-2] >= recent[-3]:
        return "You keep guessing high after a 'go lower' hint. Decrease your guess more."
    return ""


def ai_coach_suggestion(query_context: dict):
    api_key = query_context.get("api_key")
    low = query_context.get("low")
    high = query_context.get("high")
    history = query_context.get("history") or []
    last_outcome = query_context.get("last_outcome") or ""

    note = repetition_note(history, last_outcome)
    fallback_guess, fallback_text = heuristic_suggestion(low, high, history)
    fallback = (fallback_guess, (note + " " + fallback_text).strip())

    if not api_key:
        return fallback_guess, fallback[1], 0.0, "fallback", "missing_api_key"

    try:
        import google.generativeai as genai
    except Exception:
        return fallback_guess, fallback[1], 0.0, "fallback", "missing_google_generativeai"

    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-2.5-flash")
        prompt = f"""
You are helping a player in a number guessing game.
Return JSON only with keys: suggested_guess (int), advice (string), confidence (number 0-1).

Game state:
- allowed_range: {low} to {high}
- attempts_used: {query_context.get("attempts_used")}
- attempts_left: {query_context.get("attempts_left")}
- last_outcome: {last_outcome}
- guess_history: {history}

Guidelines:
- Suggested guess must be within allowed_range.
- Avoid repeating a previous integer guess.
- If the player keeps guessing too low after "Too Low", tell them to increase more (same for Too High).
"""
        resp = model.generate_content(prompt)
        text = (resp.text or "").strip()
    except Exception as exc:
        return fallback_guess, fallback[1], 0.0, "fallback", f"gemini_error: {exc}"

    import json
    def _extract_json(s: str):
        start = s.find("{")
        end = s.rfind("}")
        if start == -1 or end == -1 or end <= start:
            return None
        return s[start:end + 1]

    try:
        data = json.loads(text)
    except Exception:
        extracted = _extract_json(text)
        if not extracted:
            return fallback_guess, fallback[1], 0.0, "fallback", "invalid_json"
        try:
            data = json.loads(extracted)
        except Exception:
            return fallback_guess, fallback[1], 0.0, "fallback", "invalid_json"

    suggested = data.get("suggested_guess")
    advice = (data.get("advice") or "").strip()
    confidence = data.get("confidence")
    if not isinstance(suggested, int) or suggested < low or suggested > high:
        return fallback_guess, fallback[1], 0.0, "fallback", "suggested_out_of_range"
    if suggested in {g for g in history if isinstance(g, int)}:
        return fallback_guess, fallback[1], 0.0, "fallback", "suggested_repeats_history"
    if not isinstance(confidence, (int, float)):
        confidence = 0.5
    confidence = max(0.0, min(1.0, float(confidence)))

    if note and note.lower() not in advice.lower():
        advice = (note + " " + advice).strip()

    return suggested, advice or fallback[1], confidence, "gemini", ""
