# HYTEK Tools Development Rules

## Project Purpose

HYTEK Tools is an open-source toolkit for reading, validating, comparing, converting, and synchronizing HY-TEK swimming meet files.

This project is designed as a reusable library first.

Applications (CLI, GUI, TeamUnify synchronization, REST API) are built on top of the library.

---

# Core Principles

1. Preserve data.

Never discard unknown bytes or unknown records.

Every parser must preserve all original information even if fields are not yet decoded.

2. Read before Write.

Implement parsers first.

Implement writers only after the parser has complete unit tests.

3. Common Object Model.

Every file format must map into the same Python object model.

HY3

CL2

SD3

↓

Meet

↓

Team

↓

Swimmer

↓

Event

↓

Relay

↓

Result

4. TeamUnify is NOT part of the parser.

Parsers only understand HY-TEK formats.

Synchronization belongs in a separate package.

---

# Python Standards

Python 3.13+

Use dataclasses whenever possible.

Every public method must have type hints.

Avoid inheritance unless it significantly improves clarity.

Prefer composition over inheritance.

No global state.

No mutable default arguments.

Use pathlib instead of os.path.

Use logging instead of print().

---

# Project Structure

src/

    hytek_tools/

        models/

        parsers/

        writers/

        validators/

        utils/

        cli/

tests/

docs/

samples/

lab/

---

# Models

Models represent swimming—not file formats.

Required models:

Meet

Team

Swimmer

Event

Relay

Result

Record

A parser converts bytes into models.

A writer converts models into bytes.

---

# Parser Rules

Parsers should:

Be deterministic

Never modify data

Never discard unknown records

Preserve raw record bytes

Produce immutable model objects whenever practical

---

# Writer Rules

Writers should:

Produce identical output when nothing changes

Preserve unknown bytes

Only rewrite fields that changed

Never reorder records unless explicitly required

---

# Validation Rules

Validation should never modify files.

Validation returns findings.

Examples:

Duplicate swimmer

Invalid DOB

Duplicate event

Unknown record

Missing nickname

Missing TeamUnify identity

---

# TeamUnify Rules

TeamUnify support belongs in:

hytek_tools/teamunify/

Never inside parsers.

TeamUnify responsibilities:

Roster parser

ID Card generator

Identity matching

Validation

Synchronization

---

# ID Card Specification

Format:

MMDDYYFFFMLLLL

Where:

MMDDYY = birthdate

FFF = first three letters of first name

M = middle initial

If no middle initial:

Use *

LLLL = first four letters of last name

If fewer than four:

Pad with *

Examples

072112AARJCHYN

062218MAR*ANDR

040508PHADLE**

---

# Testing

Every parser change requires tests.

Every bug requires a regression test.

Target:

90%+ parser coverage.

Use real sample files whenever possible.

---

# Documentation

Every record type gets documentation.

Document:

Purpose

Field offsets

Lengths

Known values

Confidence level

Unknown fields

Never leave undocumented magic numbers.

---

# Coding Style

Prefer readability over cleverness.

Small functions.

Single