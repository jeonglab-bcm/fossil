# Design: fossil

The locked system. Every Hallmark run reads this first and pages share it. Change it on purpose; the file is the rule.

## System
- Genre: editorial
- Shape of the first page: Index-First (`site/index.html`); results pages Workbench; code-analysis pages Long Document
- Theme: Almanac (deal 1/3, seed independent-reproductions-published-computational-16b6·6a63c2a8·2026-10-28·r0)
- Axes: mid/grotesk-sans/chromatic-magenta · posture: restrained

## Tokens
`site/tokens.css` is the source of truth. The roles:
```css
:root {
  --color-paper: oklch(84% 0.012 245);  --color-paper-2: oklch(81% 0.012 245);  --color-paper-3: oklch(77% 0.012 245);
  --color-ink: oklch(16% 0.020 245);  --color-ink-2: oklch(24% 0.018 245);  --color-muted: oklch(38% 0.016 245);  --color-rule: oklch(73% 0.013 240);  --color-rule-2: oklch(32% 0.018 240);
  --color-accent: oklch(45% 0.180 350);  --color-accent-ink: oklch(97% 0.006 245);  --color-focus: oklch(46% 0.190 350);
  --color-sheet: oklch(93.5% 0.008 245);  --color-agree: oklch(43% 0.110 150);  --color-warn: oklch(47% 0.110 70);
  --font-display: "Hanken Grotesk", ui-sans-serif, system-ui, sans-serif;  --font-body: "Newsreader", ui-serif, Georgia, serif;  --font-outlier: "IBM Plex Mono", ui-monospace, monospace;
  --radius-card: 0;  --radius-pill: 2px;  --rule-hair: 1px;  --rule-bar: 2px;  --shadow-card: none;
}
```
The spacing scale, the type scale, the easings and the durations are the scaffold's and live in `site/tokens.css`. `site/base.css` holds the Floor's base rules; `site/site.css` holds the shared parts (slab nav, statement footer, sheet, `table.record`, `.verdict`, `.btn`, links).

## Pages
- Every page links the Google Fonts for Hanken Grotesk 500/600, Newsreader 400/500 (italic 400) and IBM Plex Mono 400/500, then its own stylesheet, whose first lines are the Hallmark stamp and which imports `tokens.css`, `base.css` and `site.css` (from a subfolder: `../tokens.css` and so on).
- Chrome on every page: the ink slab nav (wordmark `fossil` linking home, then the page's own place) and the statement footer.
- Surfaces: the slate paper, the pale sheet with a 2px ink rule at its head for tables and figures, hairlines between rows, at most one ink band a page. No cards, no shadows, square corners.
- Figures: Plex Mono, tabular, right-aligned in columns. Labels, captions and table heads: Newsreader 500 at `--text-sm` in `--color-muted`, sentence case, never tracked or uppercase.
- Verdicts: `.verdict` with `data-v` agrees, partly, differs or running; a mark and a word, never a pill. Per-figure verdicts live on the results pages; the front page carries one per paper.
- Copy: short, declarative, dated; no dashes, no middle-dot strings, no eyebrows. The front page names no problems found in a paper; those belong on its results and code-analysis pages.

## Controls
- Primary: magenta fill (`--color-accent`, `--color-accent-ink`) · 2px radius · 48px tall · one per page
- Secondary: hairline ink outline · same radius and height

## Motion
- Character: still. Only state moves (a link underline thickens, a control darkens). No reveal.

## Exports
`site/tokens.css` in this project.
