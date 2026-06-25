"""Domain enumerations for swimming meet models."""

from enum import Enum


class Gender(Enum):
    """Competition gender category."""

    MALE = "male"
    FEMALE = "female"
    MIXED = "mixed"


class Stroke(Enum):
    """Swimming stroke or event type."""

    FREESTYLE = "freestyle"
    BACKSTROKE = "backstroke"
    BREASTSTROKE = "breaststroke"
    BUTTERFLY = "butterfly"
    INDIVIDUAL_MEDLEY = "individual_medley"
    FREESTYLE_RELAY = "freestyle_relay"
    MEDLEY_RELAY = "medley_relay"
