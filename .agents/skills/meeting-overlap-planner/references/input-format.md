# Input Format

The `meeting-overlap-planner` script expects JSON with the following fields.

## Top-Level Fields

| Field | Type | Required | Notes |
|---|---|---|---|
| `start_date` | string | yes | `YYYY-MM-DD` |
| `end_date` | string | yes | `YYYY-MM-DD` |
| `meeting_duration_minutes` | integer | yes | Must be positive |
| `slot_step_minutes` | integer | no | Defaults to 15 |
| `max_results` | integer | no | Defaults to 5, capped at 20 |
| `participants` | list | yes | At least 2 participants |

## Participant Fields

Each participant must have:

| Field | Type | Required | Notes |
|---|---|---|---|
| `name` | string | yes | Display name |
| `timezone` | string | yes | IANA timezone like `America/New_York` |
| `availability` | list | yes | At least 1 weekday window |

## Availability Window Fields

Each availability object must contain:

| Field | Type | Required | Notes |
|---|---|---|---|
| `day` | string | yes | `Mon`, `Tue`, `Wed`, `Thu`, `Fri`, `Sat`, or `Sun` |
| `start` | string | yes | `HH:MM` in 24-hour time |
| `end` | string | yes | `HH:MM` in 24-hour time |

The script assumes same-day windows only, so `start` must be earlier than `end`.

## Example

```json
{
  "start_date": "2026-05-04",
  "end_date": "2026-05-08",
  "meeting_duration_minutes": 45,
  "slot_step_minutes": 15,
  "max_results": 5,
  "participants": [
    {
      "name": "Alice",
      "timezone": "America/New_York",
      "availability": [
        {"day": "Mon", "start": "09:00", "end": "17:00"},
        {"day": "Tue", "start": "09:00", "end": "17:00"},
        {"day": "Wed", "start": "09:00", "end": "17:00"}
      ]
    },
    {
      "name": "Ben",
      "timezone": "Europe/London",
      "availability": [
        {"day": "Mon", "start": "13:00", "end": "18:00"},
        {"day": "Tue", "start": "13:00", "end": "18:00"},
        {"day": "Wed", "start": "13:00", "end": "18:00"}
      ]
    }
  ]
}
```
