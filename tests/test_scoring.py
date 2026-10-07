"""
Tests for the four ways of scoring a ticket in brain.py.

Each test builds one small made-up ticket, runs one scoring function,
and checks the number that comes back. No AI calls are used.
"""

import pytest
import brain


def make_ticket(**changes):
    """A plain ticket with safe default values. Each test changes only what it needs."""
    ticket = {
        "pays_monthly": 500,
        "times_asked": 1,
        "monitoring_says": 2,
        "users_hit": 0,
        "cannot_work": False,
        "promised_hours": 24.0,
        "hours_left": 12.0,
        "already_late": False,
    }
    ticket.update(changes)
    return ticket


# ----- money -----

def test_money_score_is_the_monthly_payment():
    assert brain.score_by_money(make_ticket(pays_monthly=500)) == 500


def test_money_score_goes_up_20_percent_after_three_contacts():
    ticket = make_ticket(pays_monthly=500, times_asked=3)
    assert brain.score_by_money(ticket) == pytest.approx(600)


# ----- damage -----

def test_damage_score_counts_severity_and_users_hit():
    ticket = make_ticket(monitoring_says=3, users_hit=100)
    assert brain.score_by_damage(ticket) == pytest.approx(310)


def test_damage_score_adds_150_when_the_customer_cannot_work():
    ticket = make_ticket(monitoring_says=3, users_hit=100, cannot_work=True)
    assert brain.score_by_damage(ticket) == pytest.approx(460)


# ----- deadline -----

def test_deadline_score_is_over_1000_when_already_late():
    ticket = make_ticket(already_late=True, hours_left=-2.0)
    assert brain.score_by_deadline(ticket) == pytest.approx(1002)


def test_deadline_score_is_higher_when_less_time_is_left():
    plenty_of_time = make_ticket(hours_left=12.0)
    almost_out_of_time = make_ticket(hours_left=3.0)
    assert brain.score_by_deadline(almost_out_of_time) > brain.score_by_deadline(plenty_of_time)


# ----- fairness -----

def test_fairness_score_adds_30_for_each_time_the_customer_asked():
    ticket = make_ticket(times_asked=2, pays_monthly=500)
    assert brain.score_by_fairness(ticket) == pytest.approx(60)


def test_fairness_score_for_a_late_ticket_from_a_small_customer():
    ticket = make_ticket(times_asked=0, already_late=True, hours_left=-5.0, pays_monthly=100)
    # 0 for asking + 100 for late + 5 for hours late + 50 for paying under 200
    assert brain.score_by_fairness(ticket) == pytest.approx(155)
