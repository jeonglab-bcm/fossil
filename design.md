# Design: fossil

The locked system. Every Hallmark run reads this first and pages share it. Change it on purpose; the file is the rule.

## System
- Genre: modern-minimal
- Shape of the first page: Index-First (`site/index.html`)
- Theme: Dose (by request, https://www.usehallmark.com/themes/dose/) · dose: white
- Axes: light/grotesk-sans/chromatic-green · posture: committed

## Tokens
`site/tokens.css` is the source of truth. The roles:
```css
:root {
  --color-paper: oklch(97.6% 0.011 88);  --color-paper-2: oklch(96.5% 0.02 160);  --color-paper-3: oklch(93% 0.036 160);
  --color-ink: oklch(21% 0.025 170);  --color-ink-2: oklch(31% 0.02 170);  --color-muted: oklch(49% 0.024 165);  --color-rule: oklch(86.5% 0.022 140);
  --color-accent: oklch(50% 0.13 160);  --color-accent-deep: oklch(42% 0.11 162);  --color-accent-soft: oklch(88% 0.08 160);  --color-accent-ink: oklch(99% 0.006 160);  --color-focus: oklch(45% 0.14 160);
  --color-surface: oklch(99.5% 0.005 88);  --p-mon … --p-sun: the plastic tints;  --light, --glint;  --texture-opacity: 0.06;
  --font-display: "Schibsted Grotesk", ui-sans-serif, sans-serif;  --font-body: "Instrument Sans", ui-sans-serif, sans-serif;  --font-outlier: "DM Mono", ui-monospace, monospace;
  --radius-card: 14px;  --radius-input: 10px;  --radius-pill: 999px;  --rule-hair: 1px;  --shadow-lift: (see tokens.css);
}
```
The spacing scale, the type scale, the easings and the durations are the scaffold's and live in `site/tokens.css`. `site/base.css` holds the Floor's base rules; `site/site.css` holds the shared parts (edge-aligned `.topbar`, `.surface`, `table.record`, `.stamp`, `.plastic`, `.btn`, the ink-band `.foot`, the paper's fibre wash).

## Pages
- Every page links the Google Fonts for Schibsted Grotesk 700, Instrument Sans 400/500 and DM Mono 400/500, then its own stylesheet, whose first lines are the Hallmark stamp and which imports `tokens.css`, `base.css` and `site.css` (from a subfolder: `../tokens.css` and so on).
- Chrome on every page: the edge-aligned top bar (wordmark `fossil` linking home, two or three plain links) and the ink-band footer with one plain closing sentence and a line of mint links.
- Surfaces: warm paper with a faint fibre wash, window light only in a hero, lifted white surfaces (14px, `--shadow-lift`) for figures and tables, plastic tints only as bands, never as a signal.
- Labels: DM Mono, pharmacy-label style (white, 10px radius, a dashed tear-off stub). Verdicts are `.stamp` with `data-v` agrees (green) or partly, differs, running (grey). Never red or amber.
- Voice: a pharmacist's plainness about recovering research fossils: digging old papers back up and getting their figures back. Short, concrete, dated sentences in everyday words (“Fig. 5 came back the same.”, “We dig up old papers and get their figures back.”), never a methods pitch (“redraw and compare”). No dashes, no middle-dot strings, no eyebrows, no explanations the reader did not ask for.
- The front page names no problems found in a paper; those belong on its results and code-analysis pages. No publisher or rights footer.

## Controls
- Primary: green moulded key (`.btn--primary`) · 10px radius · 52px tall · sinks 3px on press · one per page
- Secondary: clear key (`.btn`) · same radius and height

## Motion
- Character: still. Window light does not drift; only state moves (a key sinks, an underline darkens).

## Exports
`site/tokens.css` in this project.
