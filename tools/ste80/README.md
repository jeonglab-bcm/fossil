# STE80 checker

`ste_check.py` is copied unchanged from the STE80 Humanizer skill
([Dodaios/ste80-humanizer](https://github.com/Dodaios/ste80-humanizer), `scripts/ste_check.py`, commit ace4484,
MIT licence, © 2026 Dodaios; its Pass 1 catalog is adapted from blader/humanizer, see `THIRD_PARTY_NOTICES.md`).

`tools/ai_review.py` uses it to check the AI review's text. The prompt in `ai_review.py` carries a short version of
the skill's writing rules (Pass 1 AI tells, Pass 2 sentence structure at 80% of ASD-STE100). The checker is a
heuristic: its notes go to the CI log and `ai-review.json`, never to the PR comment, and they never fail the check.
