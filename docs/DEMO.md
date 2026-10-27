# Three-minute Loom walkthrough

## Before recording

1. Complete the quickstart and run the offline tests.
2. Configure `.env` in a private editor. Close it before screen sharing.
3. Run both API modes and inspect the resulting JSON. `source` must be `openai`; check `policy.model`, `api_requests`, and `verdict`. An inconclusive or failed run is not a successful discovery.
4. Export a verified real run with `python -m worker.export <report-path>` and open `/report.html` on the local server.
5. Keep a second terminal ready for the exported `regression.py`. Run from the repository root so the fixture path resolves.
6. Share only the relevant application window. Close account dashboards and secret-bearing terminals.

## Recording sequence

**0:00–0:20 — Problem**
“I built BreakPoint to turn browser-testing findings into evidence. A policy explores the app, but an independent replay decides whether the failure is reproducible.”

**0:20–0:45 — The target**
Show the controlled cart. Explain that this is a seeded bug used to validate the system, not an unknown bug in a third-party website.

**0:45–1:30 — Your actual run**
Show the command or completed report, model/source label, observed states, and selected actions. If showing a recorded result, say so. Show the independent replay and final verdict. Do not describe an offline mock run as GPT.

**1:30–2:10 — Proof**
Open the before/after screenshots. Run the exported regression script: the buggy fixture should produce an assertion failure. Show the fixed-control result or its passing regression script.

**2:10–2:40 — Engineering**
Explain three decisions: validated actions instead of arbitrary execution; no fixture labels/source in model inputs; fresh-context replay with an independent business rule.

**2:40–3:00 — Scope**
“This prototype covers one cart contract. Next I’m expanding the benchmark with more bugs and clean controls so I can measure false positives and cost per confirmed finding.”

## Resume wording you can use now

Built a Python/Playwright browser-testing prototype with validated policy actions, fresh-context replay, trace capture, and executable regression exports; integrated an OpenAI Responses adapter and added a GitHub Actions workflow for offline acceptance checks.

Only say “validated in GitHub Actions” after the actual hosted workflow passes. Only add live AI discovery metrics after completing and reviewing those runs. The included workflow configuration alone is not a passing CI result.

## LinkedIn draft

I’m building BreakPoint, a browser-testing project focused on reproducible evidence.

The workflow is simple: a policy explores a controlled app, the worker records its actions, and a fresh browser context replays the sequence against an independent contract. A finding needs more than a model saying something looks wrong.

The prototype captures screenshots, browser traces, action logs, and an executable regression test. It also has a fixed control so I can check that verification passes when the bug is removed.

The next challenge is expanding beyond one cart scenario and measuring false positives, replay success, and cost.

[Add your public GitHub URL and Loom link before posting. Describe any live model results only after verifying them.]
