---
name: meeting-overlap-planner
description: Finds overlapping meeting windows across multiple participants using their time zones, date range, working windows, and required meeting duration. Use when the user wants deterministic timezone conversion, DST-aware overlap calculations, or a shortlist of feasible meeting slots. Do not use for open-ended scheduling advice without concrete participant availability.
---

# Meeting Overlap Planner

Use this skill when a user needs exact meeting overlap calculations across time zones and date ranges. The script is essential because timezone conversion, daylight-saving changes, interval intersection, and candidate-slot generation must be computed deterministically.

## When To Use

- The user provides participant names, time zones, and availability windows.
- The user wants a list of overlapping meeting slots.
- The request depends on precise timezone math or DST-aware conversion.
- The user wants the answer shown in each participant's local time.

## When Not To Use

- The user only wants general scheduling advice.
- The user has not provided usable participant availability or time zones.
- The user wants calendar booking or invitation sending. This skill does not integrate with calendars.
- The user wants the model to guess preferences, holidays, or travel schedules.

## Expected Inputs

The script expects JSON with this shape:

```json
{
  "start_date": "2026-05-04",
  "end_date": "2026-05-06",
  "meeting_duration_minutes": 45,
  "slot_step_minutes": 15,
  "max_results": 5,
  "participants": [
    {
      "name": "Alice",
      "timezone": "America/New_York",
      "availability": [
        {"day": "Mon", "start": "09:00", "end": "17:00"},
        {"day": "Tue", "start": "09:00", "end": "17:00"}
      ]
    }
  ]
}
```

Availability is recurring by weekday. Supported weekday values are `Mon`, `Tue`, `Wed`, `Thu`, `Fri`, `Sat`, and `Sun`.

If the user gives natural-language availability, first normalize it into this JSON structure before running the script.

## Workflow

1. Check whether the user gave:
   - a start date and end date
   - a meeting duration
   - at least two participants
   - one valid IANA timezone per participant
   - at least one availability window per participant
2. If the request is missing required details, ask a short follow-up instead of guessing.
3. Write the normalized JSON to a temp file or pipe it to the script.
4. Run:

```bash
python3 .agents/skills/meeting-overlap-planner/scripts/meeting_overlap.py --input path/to/input.json
```

5. Read the script output and present:
   - a short summary
   - the candidate meeting slots
   - any warnings or validation notes

## Output Format

Default script output is a text report with:

- a summary section
- any warnings
- candidate meeting slots in UTC
- the same slots converted into each participant's local time

The script can also return JSON using `--output-format json`.

## Important Checks

- Do not invent time zones. If the timezone is ambiguous, ask the user.
- Do not assume availability on weekends unless it is provided.
- Do not guess holidays or business-day rules.
- If there are no overlaps, say so clearly instead of forcing a result.
- If the date range is too large or the input is invalid, report the limitation and stop.

## Limits

- Maximum date range: 31 days
- Maximum participants: 20
- Maximum results returned: 20
- This skill finds candidate windows only. It does not reserve meetings or check real calendars.

## Reference

For the full input schema and examples, see [references/input-format.md](references/input-format.md).
