#!/usr/bin/env python3
"""Find overlapping meeting windows across time zones."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


WEEKDAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
WEEKDAY_TO_INDEX = {name: idx for idx, name in enumerate(WEEKDAYS)}
MAX_RANGE_DAYS = 31
MAX_PARTICIPANTS = 20
MAX_RESULTS = 20


@dataclass(frozen=True)
class AvailabilityWindow:
    day_index: int
    start_local: time
    end_local: time


@dataclass(frozen=True)
class Participant:
    name: str
    timezone_name: str
    timezone_obj: ZoneInfo
    availability: list[AvailabilityWindow]


class ValidationError(Exception):
    """Raised when the input payload is invalid."""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", help="Path to an input JSON file. Reads stdin if omitted.")
    parser.add_argument(
        "--output-format",
        choices=["text", "json"],
        default="text",
        help="Return a human-readable report or JSON.",
    )
    return parser.parse_args()


def load_payload(input_path: str | None) -> dict[str, Any]:
    if input_path:
        return json.loads(Path(input_path).read_text(encoding="utf-8"))
    return json.load(__import__("sys").stdin)


def parse_date(value: Any, field_name: str) -> date:
    if not isinstance(value, str):
        raise ValidationError(f"{field_name} must be a YYYY-MM-DD string.")
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise ValidationError(f"{field_name} must be a valid YYYY-MM-DD date.") from exc


def parse_time(value: Any, field_name: str) -> time:
    if not isinstance(value, str):
        raise ValidationError(f"{field_name} must be an HH:MM string.")
    try:
        return time.fromisoformat(value)
    except ValueError as exc:
        raise ValidationError(f"{field_name} must be a valid HH:MM time.") from exc


def ensure_positive_int(value: Any, field_name: str, default: int | None = None) -> int:
    if value is None:
        if default is None:
            raise ValidationError(f"{field_name} is required.")
        return default
    if not isinstance(value, int) or value <= 0:
        raise ValidationError(f"{field_name} must be a positive integer.")
    return value


def parse_availability(windows: Any, participant_name: str) -> list[AvailabilityWindow]:
    if not isinstance(windows, list) or not windows:
        raise ValidationError(f"{participant_name} must have at least one availability window.")

    parsed: list[AvailabilityWindow] = []
    for idx, window in enumerate(windows, start=1):
        if not isinstance(window, dict):
            raise ValidationError(f"{participant_name} availability item {idx} must be an object.")
        day = window.get("day")
        if day not in WEEKDAY_TO_INDEX:
            raise ValidationError(
                f"{participant_name} availability item {idx} has invalid day {day!r}. "
                f"Use one of {', '.join(WEEKDAYS)}."
            )
        start_local = parse_time(window.get("start"), f"{participant_name} availability start")
        end_local = parse_time(window.get("end"), f"{participant_name} availability end")
        if start_local >= end_local:
            raise ValidationError(
                f"{participant_name} availability item {idx} must have start earlier than end."
            )
        parsed.append(
            AvailabilityWindow(
                day_index=WEEKDAY_TO_INDEX[day],
                start_local=start_local,
                end_local=end_local,
            )
        )
    return parsed


def parse_participants(participants: Any) -> list[Participant]:
    if not isinstance(participants, list) or len(participants) < 2:
        raise ValidationError("participants must be a list with at least two participants.")
    if len(participants) > MAX_PARTICIPANTS:
        raise ValidationError(f"participants cannot exceed {MAX_PARTICIPANTS}.")

    parsed: list[Participant] = []
    for idx, raw in enumerate(participants, start=1):
        if not isinstance(raw, dict):
            raise ValidationError(f"Participant {idx} must be an object.")
        name = raw.get("name")
        timezone_name = raw.get("timezone")
        if not isinstance(name, str) or not name.strip():
            raise ValidationError(f"Participant {idx} must have a non-empty name.")
        if not isinstance(timezone_name, str) or not timezone_name.strip():
            raise ValidationError(f"{name} must have a non-empty timezone.")
        try:
            tz = ZoneInfo(timezone_name)
        except ZoneInfoNotFoundError as exc:
            raise ValidationError(f"{name} has invalid timezone {timezone_name!r}.") from exc

        availability = parse_availability(raw.get("availability"), name)
        parsed.append(
            Participant(
                name=name.strip(),
                timezone_name=timezone_name,
                timezone_obj=tz,
                availability=availability,
            )
        )
    return parsed


def validate_payload(payload: dict[str, Any]) -> tuple[date, date, int, int, int, list[Participant]]:
    start_date = parse_date(payload.get("start_date"), "start_date")
    end_date = parse_date(payload.get("end_date"), "end_date")
    if end_date < start_date:
        raise ValidationError("end_date must be on or after start_date.")
    date_span = (end_date - start_date).days + 1
    if date_span > MAX_RANGE_DAYS:
        raise ValidationError(f"Date range cannot exceed {MAX_RANGE_DAYS} days.")

    duration = ensure_positive_int(payload.get("meeting_duration_minutes"), "meeting_duration_minutes")
    step = ensure_positive_int(payload.get("slot_step_minutes"), "slot_step_minutes", default=15)
    max_results = ensure_positive_int(payload.get("max_results"), "max_results", default=5)
    max_results = min(max_results, MAX_RESULTS)
    participants = parse_participants(payload.get("participants"))
    return start_date, end_date, duration, step, max_results, participants


def daterange(start_date: date, end_date: date) -> list[date]:
    current = start_date
    days: list[date] = []
    while current <= end_date:
        days.append(current)
        current += timedelta(days=1)
    return days


def local_window_to_utc(target_date: date, participant: Participant, window: AvailabilityWindow) -> tuple[datetime, datetime]:
    start_dt = datetime.combine(target_date, window.start_local, participant.timezone_obj)
    end_dt = datetime.combine(target_date, window.end_local, participant.timezone_obj)
    return start_dt.astimezone(timezone.utc), end_dt.astimezone(timezone.utc)


def intersect_two_range_lists(
    left: list[tuple[datetime, datetime]],
    right: list[tuple[datetime, datetime]],
) -> list[tuple[datetime, datetime]]:
    intersections: list[tuple[datetime, datetime]] = []
    i = 0
    j = 0

    left_sorted = sorted(left)
    right_sorted = sorted(right)

    while i < len(left_sorted) and j < len(right_sorted):
        left_start, left_end = left_sorted[i]
        right_start, right_end = right_sorted[j]

        start = max(left_start, right_start)
        end = min(left_end, right_end)
        if start < end:
            intersections.append((start, end))

        if left_end <= right_end:
            i += 1
        else:
            j += 1

    return intersections


def expand_slots(
    overlap: tuple[datetime, datetime],
    duration_minutes: int,
    step_minutes: int,
) -> list[tuple[datetime, datetime]]:
    duration = timedelta(minutes=duration_minutes)
    step = timedelta(minutes=step_minutes)
    current_start, overlap_end = overlap
    slots: list[tuple[datetime, datetime]] = []
    while current_start + duration <= overlap_end:
        slots.append((current_start, current_start + duration))
        current_start += step
    return slots


def find_meeting_slots(
    start_date: date,
    end_date: date,
    duration_minutes: int,
    step_minutes: int,
    max_results: int,
    participants: list[Participant],
) -> dict[str, Any]:
    all_slots: list[dict[str, Any]] = []

    for target_date in daterange(start_date, end_date):
        overlapping_ranges: list[tuple[datetime, datetime]] | None = None
        skip_day = False

        for participant in participants:
            windows_for_day = [
                window for window in participant.availability if window.day_index == target_date.weekday()
            ]
            if not windows_for_day:
                skip_day = True
                break

            participant_ranges = [
                local_window_to_utc(target_date, participant, window) for window in windows_for_day
            ]

            if overlapping_ranges is None:
                overlapping_ranges = sorted(participant_ranges)
            else:
                overlapping_ranges = intersect_two_range_lists(overlapping_ranges, participant_ranges)
                if not overlapping_ranges:
                    skip_day = True
                    break

        if skip_day:
            continue

        if not overlapping_ranges:
            continue

        for overlap in overlapping_ranges:
            for start_utc, end_utc in expand_slots(overlap, duration_minutes, step_minutes):
                slot = {
                    "date": target_date.isoformat(),
                    "utc_start": start_utc.isoformat(),
                    "utc_end": end_utc.isoformat(),
                    "participants": {},
                }
                for participant in participants:
                    local_start = start_utc.astimezone(participant.timezone_obj)
                    local_end = end_utc.astimezone(participant.timezone_obj)
                    slot["participants"][participant.name] = {
                        "timezone": participant.timezone_name,
                        "local_start": local_start.isoformat(),
                        "local_end": local_end.isoformat(),
                    }
                all_slots.append(slot)
                if len(all_slots) >= max_results:
                    return {"slots": all_slots, "warnings": []}

    return {"slots": all_slots, "warnings": []}


def render_text(result: dict[str, Any], duration_minutes: int) -> str:
    slots = result["slots"]
    warnings = result["warnings"]
    lines = [
        "Meeting Overlap Planner",
        "=======================",
        f"Candidate slots found: {len(slots)}",
        f"Requested meeting duration: {duration_minutes} minutes",
    ]
    if warnings:
        lines.append("")
        lines.append("Warnings:")
        for warning in warnings:
            lines.append(f"- {warning}")

    if not slots:
        lines.append("")
        lines.append("No overlapping slots were found for the given constraints.")
        return "\n".join(lines)

    for idx, slot in enumerate(slots, start=1):
        lines.append("")
        lines.append(f"Option {idx}")
        lines.append(f"UTC: {slot['utc_start']} to {slot['utc_end']}")
        for participant_name, details in slot["participants"].items():
            lines.append(
                f"- {participant_name} ({details['timezone']}): "
                f"{details['local_start']} to {details['local_end']}"
            )
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    try:
        payload = load_payload(args.input)
        start_date, end_date, duration, step, max_results, participants = validate_payload(payload)
        result = find_meeting_slots(
            start_date=start_date,
            end_date=end_date,
            duration_minutes=duration,
            step_minutes=step,
            max_results=max_results,
            participants=participants,
        )
        if args.output_format == "json":
            print(json.dumps(result, indent=2))
        else:
            print(render_text(result, duration))
        return 0
    except ValidationError as exc:
        error_payload = {"error": str(exc)}
        if args.output_format == "json":
            print(json.dumps(error_payload, indent=2))
        else:
            print(f"Validation error: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
