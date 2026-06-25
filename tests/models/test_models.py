"""Unit tests for core domain models."""

from datetime import date

import pytest

from hytek_tools.models import (
    Event,
    Gender,
    Meet,
    Record,
    Relay,
    RelayLeg,
    Result,
    Stroke,
    Swimmer,
    Team,
)


def test_swimmer_creation() -> None:
    swimmer = Swimmer(
        first_name="Alex",
        last_name="Rivera",
        middle_initial="J",
        nickname="Al",
        birth_date=date(2012, 7, 21),
        gender=Gender.MALE,
        team_code="FAST",
    )

    assert swimmer.first_name == "Alex"
    assert swimmer.last_name == "Rivera"
    assert swimmer.middle_initial == "J"
    assert swimmer.nickname == "Al"
    assert swimmer.birth_date == date(2012, 7, 21)
    assert swimmer.gender is Gender.MALE
    assert swimmer.team_code == "FAST"
    assert "Rivera" in repr(swimmer)


def test_swimmer_is_frozen() -> None:
    swimmer = Swimmer(first_name="Alex", last_name="Rivera")

    with pytest.raises(AttributeError):
        swimmer.first_name = "Bob"  # type: ignore[misc]


def test_team_creation() -> None:
    swimmers = (
        Swimmer(first_name="Alex", last_name="Rivera", team_code="FAST"),
        Swimmer(first_name="Sam", last_name="Lee", team_code="FAST"),
    )
    team = Team(code="FAST", name="Fast Swim Club", nickname="Fast", swimmers=swimmers)

    assert team.code == "FAST"
    assert team.name == "Fast Swim Club"
    assert team.nickname == "Fast"
    assert len(team.swimmers) == 2
    assert "FAST" in repr(team)


def test_event_creation() -> None:
    event = Event(
        number=11,
        distance=50,
        stroke=Stroke.FREESTYLE,
        gender=Gender.FEMALE,
        age_min=11,
        age_max=12,
        name="Girls 11-12 50 Free",
    )

    assert event.number == 11
    assert event.distance == 50
    assert event.stroke is Stroke.FREESTYLE
    assert event.gender is Gender.FEMALE
    assert event.age_min == 11
    assert event.age_max == 12
    assert event.name == "Girls 11-12 50 Free"
    assert "#11" in repr(event)


def test_relay_creation() -> None:
    legs = (
        RelayLeg(Swimmer(first_name="A", last_name="One"), leg=1, split_time="25.12"),
        RelayLeg(Swimmer(first_name="B", last_name="Two"), leg=2, split_time="26.01"),
        RelayLeg(Swimmer(first_name="C", last_name="Three"), leg=3, split_time="25.88"),
        RelayLeg(Swimmer(first_name="D", last_name="Four"), leg=4, split_time="24.99"),
    )
    relay = Relay(name="A", team_code="FAST", event_number=41, legs=legs)

    assert relay.name == "A"
    assert relay.team_code == "FAST"
    assert relay.event_number == 41
    assert len(relay.legs) == 4
    assert relay.legs[0].split_time == "25.12"
    assert "legs=4" in repr(relay)


def test_result_individual_creation() -> None:
    swimmer = Swimmer(first_name="Alex", last_name="Rivera", team_code="FAST")
    result = Result(
        event_number=11,
        swimmer=swimmer,
        time="28.45",
        seed_time="29.01",
        place=3,
        heat=2,
        lane=5,
        points=16.0,
    )

    assert result.event_number == 11
    assert result.swimmer is swimmer
    assert result.relay is None
    assert result.time == "28.45"
    assert result.seed_time == "29.01"
    assert result.place == 3
    assert result.heat == 2
    assert result.lane == 5
    assert result.points == 16.0
    assert result.is_dq is False
    assert result.is_scratch is False
    assert "place=3" in repr(result)


def test_result_relay_creation() -> None:
    relay = Relay(name="A", team_code="FAST", event_number=41)
    result = Result(event_number=41, relay=relay, time="2:01.34", place=1)

    assert result.swimmer is None
    assert result.relay is relay
    assert result.time == "2:01.34"
    assert result.place == 1


def test_result_dq_and_scratch_flags() -> None:
    swimmer = Swimmer(first_name="Alex", last_name="Rivera")
    dq = Result(event_number=11, swimmer=swimmer, is_dq=True)
    scratch = Result(event_number=11, swimmer=swimmer, is_scratch=True)

    assert dq.is_dq is True
    assert "DQ" in repr(dq)
    assert scratch.is_scratch is True
    assert "SCR" in repr(scratch)


def test_record_creation() -> None:
    swimmer = Swimmer(first_name="Jordan", last_name="Smith", gender=Gender.FEMALE)
    record = Record(
        record_type="meet",
        time="27.89",
        event_number=11,
        distance=50,
        stroke=Stroke.FREESTYLE,
        gender=Gender.FEMALE,
        swimmer=swimmer,
        date_set=date(2024, 6, 15),
        meet_name="Summer Championships",
    )

    assert record.record_type == "meet"
    assert record.time == "27.89"
    assert record.event_number == 11
    assert record.distance == 50
    assert record.stroke is Stroke.FREESTYLE
    assert record.gender is Gender.FEMALE
    assert record.swimmer is swimmer
    assert record.holder_name is None
    assert record.date_set == date(2024, 6, 15)
    assert record.meet_name == "Summer Championships"
    assert "meet" in repr(record)


def test_record_with_holder_name_only() -> None:
    record = Record(
        record_type="pool",
        time="24.10",
        holder_name="Legacy Holder",
    )

    assert record.swimmer is None
    assert record.holder_name == "Legacy Holder"
    assert "Legacy Holder" in repr(record)


def test_meet_creation() -> None:
    team = Team(
        code="FAST",
        name="Fast Swim Club",
        swimmers=(Swimmer(first_name="Alex", last_name="Rivera", team_code="FAST"),),
    )
    event = Event(
        number=11,
        distance=50,
        stroke=Stroke.FREESTYLE,
        gender=Gender.FEMALE,
        age_min=11,
        age_max=12,
    )
    result = Result(
        event_number=11,
        swimmer=team.swimmers[0],
        time="28.45",
        place=1,
    )
    record = Record(record_type="meet", time="27.89", swimmer=team.swimmers[0])

    meet = Meet(
        name="Summer Championships",
        start_date=date(2024, 6, 14),
        end_date=date(2024, 6, 16),
        location="Springfield",
        venue="Aquatic Center",
        teams=(team,),
        events=(event,),
        results=(result,),
        records=(record,),
    )

    assert meet.name == "Summer Championships"
    assert meet.start_date == date(2024, 6, 14)
    assert meet.end_date == date(2024, 6, 16)
    assert meet.location == "Springfield"
    assert meet.venue == "Aquatic Center"
    assert len(meet.teams) == 1
    assert len(meet.events) == 1
    assert len(meet.results) == 1
    assert len(meet.records) == 1
    assert "Summer Championships" in repr(meet)


def test_meet_defaults_are_empty_tuples() -> None:
    meet = Meet(name="Empty Meet")

    assert meet.teams == ()
    assert meet.events == ()
    assert meet.results == ()
    assert meet.records == ()
    assert meet.start_date is None
