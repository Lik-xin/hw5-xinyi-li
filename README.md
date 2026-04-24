# Week 5: Reusable AI Skill

**Full Name:** Xinyi Li  
**Skill Name:** `meeting-overlap-planner`

## Video

Replace the placeholder below with your final walkthrough video link:

`VIDEO_LINK_HERE`

## What The Skill Does

This skill finds overlapping meeting windows across multiple participants using:

- participant time zones
- recurring weekday availability windows
- a target date range
- a required meeting duration

It is designed for cases where the user wants exact meeting-slot math across time zones and daylight-saving rules.

## Why I Chose It

I chose this skill because it is narrow, reusable, and script-heavy in a meaningful way. A model can help interpret the user's scheduling request, but it should not be trusted to do timezone conversion, interval overlap, and DST-aware slot generation by prose alone.

The Python script is genuinely load-bearing because it handles:

- timezone validation
- daylight-saving-aware local-to-UTC conversion
- overlap intersection across participants
- candidate-slot generation
- structured validation errors

## Folder Structure

```text
hw5-xinyi-li/
├─ .agents/
│  └─ skills/
│     └─ meeting-overlap-planner/
│        ├─ SKILL.md
│        ├─ references/
│        │  └─ input-format.md
│        └─ scripts/
│           └─ meeting_overlap.py
├─ demo_cases/
│  ├─ cautious_case.json
│  ├─ edge_case.json
│  └─ normal_case.json
└─ README.md
```

## How To Use It

Ask the agent to use the `meeting-overlap-planner` skill when you have participant availability and need deterministic candidate slots.

Example agent prompt:

```text
Use the meeting-overlap-planner skill. Find a 45-minute overlap for these participants and show the final slots in each person's local time.
```

The script can also be run directly:

```bash
python3 .agents/skills/meeting-overlap-planner/scripts/meeting_overlap.py --input demo_cases/normal_case.json
```

## What The Script Does

The Python script:

1. validates the input JSON
2. checks time zones using the IANA timezone database
3. expands each participant's recurring weekday windows over the requested date range
4. converts local availability windows into UTC
5. intersects the available windows across all participants
6. generates meeting slots at a fixed step size
7. returns the slots in UTC and in every participant's local time

## Demo Prompts

Use these three prompts in the coding assistant demo:

### 1. Normal Case

```text
Use the meeting-overlap-planner skill on demo_cases/normal_case.json and summarize the best meeting options.
```

### 2. Edge Case

```text
Use the meeting-overlap-planner skill on demo_cases/edge_case.json. Explain whether any overlap exists and why.
```

### 3. Cautious / Limited Case

```text
Use the meeting-overlap-planner skill on demo_cases/cautious_case.json. If the request is outside the skill limits, explain the limitation instead of guessing.
```

## What Worked Well

- The skill is easy to describe and trigger because the name is specific.
- The script provides deterministic results that would be error-prone in prose.
- The output is practical for a real workflow because it shows every slot in local time for each participant.

## Remaining Limitations

- It uses recurring weekday availability, not live calendar integration.
- It does not model holidays, travel schedules, or personal preferences.
- It assumes same-day availability windows rather than overnight shifts.
- It only finds candidate slots; it does not book meetings.
