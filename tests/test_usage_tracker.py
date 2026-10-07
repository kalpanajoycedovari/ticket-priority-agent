"""
Tests for usage_tracker.py. A pretend response stands in for Groq,
so no AI call is made.
"""

from types import SimpleNamespace

import pytest

import usage_tracker


def pretend_response(tokens_in, tokens_out):
    return SimpleNamespace(
        usage=SimpleNamespace(prompt_tokens=tokens_in, completion_tokens=tokens_out)
    )


def test_summary_adds_up_every_call():
    usage_tracker.reset()
    usage_tracker.note_a_call("decision", pretend_response(1000, 500), 5.0)
    usage_tracker.note_a_call("rewrite", pretend_response(200, 50), 1.0)

    result = usage_tracker.summary()

    assert result["number_of_calls"] == 2
    assert result["tokens_in"] == 1200
    assert result["tokens_out"] == 550
    assert result["seconds"] == 6.0
    assert result["output_tokens_per_second"] == pytest.approx(91.7, abs=0.1)


def test_summary_with_no_calls_does_not_crash():
    usage_tracker.reset()
    result = usage_tracker.summary()
    assert result["number_of_calls"] == 0
    assert result["output_tokens_per_second"] == 0
