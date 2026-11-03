#!/usr/bin/env python3
"""Extract RelEx's relation restriction terms from Fundel et al.'s supplementary page.

The page (http://www.bio.ifi.lmu.de/publications/RelEx/, now 404) survives as a 2014 Wayback
capture, which fetch_inputs.sh downloads and checks. It lists 175 word stems, one per line, as
"stem:word1|word2|...". They expand to 1,048 distinct words, the number Fundel et al. report.
The list is not redistributed here.

Usage: extract_terms.py RELEX_PAGE.html OUT.txt
"""

import html
import re
import sys

page = open(sys.argv[1], encoding="latin-1").read()
seg = page[page.find("Relation restriction terms"):]
seg = re.sub(r"<br\s*/?>|</br>", "\n", seg, flags=re.I)
seg = html.unescape(re.sub(r"<[^>]+>", "", seg))
lines = [l.strip() for l in seg.splitlines() if re.match(r"^[\w\-]+:[^ ]", l.strip())]
lines = [l for l in lines if not l.startswith("word-stem:")]
words = {w.strip().lower() for l in lines for w in l.split(":", 1)[1].split("|") if w.strip()}
if len(lines) != 175 or len(words) != 1048:
    raise SystemExit(f"expected 175 stems and 1,048 terms, found {len(lines)} and {len(words)}")
open(sys.argv[2], "w").write("\n".join(lines) + "\n")
print(f"{len(lines)} stems, {len(words)} terms")
