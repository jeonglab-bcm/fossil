# Adjudication proposal: unresolved diagnostics (PMC4081021)

Proposed entries: `reports/adjudication-proposal.json` (36 entries: 25 for s001-pcbi-1003686, 11 for s002-pcbi-1003686-s002). The queue holds 36 `unresolved_diagnostic` items, not 44. Each entry's page, check and fingerprint are copied from `review-aid/review-queue.json`. They were also cross-checked against the `unresolved_checks` in each document's `verification.json`, and the two sets are identical.

**Real errors found: none.** Every flagged line and number was located in the source PDF, rendered at 3-4x (rotated for Tables 1 and 2) and compared with the build-output Markdown/CSV that the verifier reads. Each difference comes from the text layer, not from the transcription.

## Method

- I reproduced the verifier's primary number diff exactly (pymupdf lines minus exclusions vs. page Markdown + CSV) and the pypdf visitor-text diff, then printed the source context of every flagged token.
- Renders are in the session scratchpad (`adjudicate/p*.png`, `adjudicate/s*.png`). No file in the review directory was edited apart from these two reports.

## Parser artefacts behind the diagnostics

| Source / pages | Text-layer artefact | Visible source / transcription |
|---|---|---|
| s001 p1 (indep.) | `©` glyph decoded by pypdf as `/C223`, glued to `2014` | `© 2014` |
| s001 p2, p4 (indep.) | big-delimiter glyphs `/C16`–`/C19`; θ* asterisk as `/C3` | large brackets; `\theta^*` |
| s001 p2–p8, p14 (lines) | Symbol/AdvP fonts: `~` for =, `z` for +, `{` for −, `½…\x03` for [ ], `D` for \|, `h`/`j`/`Q`/`m`/`S` for θ/ξ/φ/μ/Σ, `w` for >, `[R` for ∈ℝ | LaTeX math matching the render term by term |
| s001 p5–p8, p11, p14 (indep.) | closing bracket glyph decoded by pypdf as `/C138` (13+13+9+28+2+3 tokens) | ordinary `]` |
| s001 p5 | decimal point encoded as `:` (`0:1 … 1:0`) | t = 0, 0.1, 0.2, 0.3, 0.5, 1.0 |
| s001 p6 | superscripts flattened (`½10{6,104`, `10{2:5,102:5`), `1:6` | [10^-6,10^4], [10^-2.5,10^2.5], ∼1.6 |
| s001 p9, p11 (rotated Tables 1, 2) | minus printed as `2` (`21.9534` = −1.9534; `25.2890` = −5.2890), `(104)`/`(103)` headers, `.10` for >10, ΔBIC as `DBIC`; CSV repeats the Scenario column and combines the scenario headers | all 24 + 9 rows checked cell by cell against the renders |
| s001 p15 | `Sˇpidlen` (spacing caron) | `Špidlen` |
| s002 p4, p6, p7 | superscript ranges flattened (`10−10, 1010`, `10−3, 103`, `102`, `101`); fraction numerators split from `\frac` | [10^-10,10^10], [10^-3,10^3], [10^-1,10^2], [10^-1,10^1]; LaTeX fractions match |
| s002 p9 | three table blocks each print ℓ(θ*)(10^4) and BIC (10^4) (6 × `104`); merged CSV has one header row | all three blocks use 10^4; all 27 data rows match |

## Notes for the coordinator (not errors)

- Source quirks that the transcription keeps as printed, confirmed in the renders:
  - s002 p4: x1 = [TrkA:NGF]/k3.
  - s002 p7: the unclosed `(` in the d[Ras:GTP]/dt numerator.
  - s001 p5: "NFG-induced" in the heading.
  - s001 p14: "1 nM NFG" in the Figure 6 caption.
- s001 p4 transcribes the printed italic "v_i" as `\nu_i`. The text layer gives Symbol-font `n` (ν), so this is consistent.
