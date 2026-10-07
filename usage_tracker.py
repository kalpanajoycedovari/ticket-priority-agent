"""
usage_tracker.py

Keeps a note of every call made to the AI model: how many tokens went in,
how many came out, and how many seconds it took.
"""

calls = []


def reset():
    """Clears the notes, so a new run starts from zero."""
    calls.clear()


def note_a_call(name, response, seconds):
    """Writes down one call. The response from Groq already holds the token counts."""
    usage = response.usage
    calls.append({
        "call": name,
        "tokens_in": usage.prompt_tokens,
        "tokens_out": usage.completion_tokens,
        "seconds": round(seconds, 2),
    })


def summary():
    """Adds up every call made since the last reset."""
    tokens_in = sum(c["tokens_in"] for c in calls)
    tokens_out = sum(c["tokens_out"] for c in calls)
    seconds = round(sum(c["seconds"] for c in calls), 2)

    if seconds > 0:
        speed = round(tokens_out / seconds, 1)
    else:
        speed = 0

    return {
        "number_of_calls": len(calls),
        "tokens_in": tokens_in,
        "tokens_out": tokens_out,
        "seconds": seconds,
        "output_tokens_per_second": speed,
    }
