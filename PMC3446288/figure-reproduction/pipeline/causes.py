"""Causes of every result that is not exact (imported by make_notes.py). Numbers are from the run of
2026-11-18/19 (output/comparison.json, output/hypotheses.json); a rerun that changes them fails the check."""

H = lambda h, t, r: {"hypothesis": h, "test": t, "result": r}
EV = ["figure-reproduction/output/comparison.json", "figure-reproduction/output/hypotheses.json"]

DB = H("The junction database is smaller because today's annotation dumps differ from the paper's",
       "Rebuild with the stated rule from the 2007-2020 UCSC mm9 dumps: 5,093,205 junctions against 5,574,728",
       "supported")
TOPHAT_SAME = H("Our TopHat arm differs from the paper's", "Count junctions in the authors' GEO TopHat 1.0.14 alignments: "
                "101,174, 110,119, 109,899 and 139,105 against Table S1's TopHat-only + Both of 101,176, 110,115, 109,893 and 139,103",
                "rejected")
PTC_FP = H("Our false-positive gene filter removes too many PTC calls", "Count PTC+ evident junctions without it: 1,794 in BMM "
           "and 4,334 in liver, still far below 4,047 and 14,387 (hypotheses.json)", "rejected")
PTC_ANNOT = H("Exons the paper found in TROMER (an EST transcriptome with no mouse data online) are unannotated for us, so "
              "their junctions are excluded instead of called", "Count junctions excluded as unannotated: 7,431 to 26,659 per "
              "sample against the paper's 2,665 to 7,768 (1.7 to 4.0 times); 2,864 evident BMM junctions against a PTC+ gap "
              "of 2,908, and 8,511 against 10,941 in liver. TopHat-only junctions give 3 PTC+ calls against 1,328 and 2,888. "
              "This is an upper bound only: nothing shows those junctions would be PTC+", "inconclusive")
PTC_DIST = H("Our PTC rule or translation differs from the paper's", "Run it on the paper's own events (Additional files 8 "
             "and 9): 45 of 50 exclusion events are called PTC+ and 42 of those give the printed distance; the 5 not called "
             "(10%) cannot account for a shortfall of 72 to 76%", "rejected")

def C(cat, summary, hyps, status="open", evidence=EV):
    return {"category": cat, "summary": summary, "evidence": evidence, "hypotheses": hyps, "status": status}

PTC_CAUSE = C("unknown", "We call fewer PTC+ junctions than the paper: 28% of its count in BMM (1,139 against 4,047) and 24% "
              "in liver (3,446 against 14,387); counts built on them come back at 24% to 77% of the paper's. Our PTC rule and "
              "the false-positive filter do not explain the gap. Junctions we must exclude as unannotated (no TROMER) are numerous "
              "enough to explain it, but that is not shown.",
              [PTC_DIST, PTC_FP, PTC_ANNOT])

CAUSES = {
 "text.junction_db": C("data_unavailable", "5,093,205 junctions against 5,574,728 (-8.6%): the rule is the paper's, the annotation "
                       "versions are today's. The paper's 2011 RefSeq and Ensembl dumps are not available.",
                       [DB, H("Exons on either strand inside a RefSeq gene", "Same rule ignoring strand: 6,805,197 (+22%)", "rejected")],
                       "explained"),
 "fig1a": C("unknown", "Mapped reads agree within 2% in BMM WT (8,114,319 against 8,240,605) but liver maps 99% against 88%, and "
            "more reads fall in introns and between genes than in the paper. How the paper classed reads is not stated.",
            [H("The paper counted exons of all five repositories, not RefSeq only", "Classify against all repositories: BMM WT "
               "exonic 5,699,829, intergenic 368,148 against the paper's 5,124,062 and 718,984; RefSeq only gives 4,962,814 and "
               "918,963; the paper lies between", "rejected"),
             H("A read-quality filter (reads with N) removed liver reads", "Share of reads with an N: 4.9% and 5.0% in the liver "
               "runs, far less than the 11% gap in mapping frequency", "rejected"),
             H("Truncated reads are counted twice", "Count reads, not alignments, in the total", "rejected")]),
 "text.mapping": C("unknown", "More reads map than in the paper (92% against 84%), mostly in liver, and truncation recovers about "
                   "twice as many; the junction share (24.7% against 28%) and the TopHat-only share (8 to 16% against 11 to 16%) "
                   "are close. 252,921 unique junctions against 323,474.",
                   [DB, TOPHAT_SAME, H("A read-quality filter explains the higher mapping", "Reads with an N: 5% in liver", "rejected")]),
 "text.truncation": C("undocumented_setting", "We recover 1.46 to 1.97 million reads per sample by truncation against 0.72 to "
                      "0.79 million. The paper does not say whether it trimmed both ends at each step or how it counted a read "
                      "whose two halves map.",
                      [H("The paper counted only truncated reads that land on junctions", "Sum of junction hits of truncated reads: "
                         "289,514 in BMM WT against 781,275", "rejected"),
                       H("The paper ran only the first step (65 nt)", "Reads recovered at 65 nt: 460,065 in BMM WT against 781,275",
                         "rejected")]),
 "text.tmm": C("unknown", "Normalising each tissue's WT and KO pair gives the paper's structure (each pair multiplies to 1.000), but "
               "the factors differ: BMM 0.980 and 1.020 against 0.998 and 1.002; liver 0.794 and 1.260 against 1.188 and 0.841.",
               [H("TMM over all four samples", "edgeR on the four-sample matrix: 1.39, 1.42, 0.57, 0.90; pairs do not multiply to 1",
                  "rejected"),
                H("TMM within each tissue", "Pairs multiply to 1.000, as the paper's do", "supported"),
                H("edgeR 1.6.12 reported the reciprocal factor", "Reciprocal liver factors 1.260 and 0.794 have the paper's order "
                  "(WT above KO) but not its values; BMM's would then reverse", "inconclusive")]),
 "tableS1": C("data_unavailable", "BMM totals are within 4% (130,518 against 135,307) and Both is close; liver finds far fewer "
              "database-only junctions (41,032 against 89,890), so the liver totals are 26% lower. The TopHat arm is the "
              "authors' own.", [TOPHAT_SAME, DB,
              H("Junctions only our truncated reads find are the difference", "Liver DB-only junctions are fewer, not more, "
                "although truncation recovers more reads", "rejected")]),
 "tableS2": PTC_CAUSE,
 "text.ptc_filters": C("data_unavailable", "Without TROMER we exclude 1.7 to 4.0 times as many junctions as unannotated; the "
                       "paper gives no threshold for its false-positive gene filter, and ours removes 251 and 269 genes against "
                       "118 and 190.", [PTC_ANNOT, PTC_FP, PTC_DIST]),
 "fig2a": C("unknown", "All junctions in BMM come back within 7% (up, unregulated and down 14,145, 70,924, 12,020 against "
            "14,056, 72,499, 11,311) and common up within 2% (2,226 against 2,257); liver is 8% low for up and 14% low for down. "
            "The PTC+ rows are 13% to 54% of the paper's, from the PTC calls (see Table S2), and 'common unregulated' counts "
            "junctions the paper did not count as common.",
            [PTC_DIST, PTC_FP, PTC_ANNOT]),
 "text.fig2": PTC_CAUSE,
 "text.core_targets": PTC_CAUSE,
 "fig3a": C("unknown", "Regulation of canonical and AS junctions agrees in BMM to 2 points (AS up 33% against 35%); the "
            "PTC+ share of up-regulated AS junctions is about half the paper's (20% against 47%; liver 24% against 45%), from the PTC calls.",
            [PTC_DIST, PTC_FP, PTC_ANNOT]),
 "text.fig3": C("undocumented_setting", "With no read cutoff, as the Fig. 3b caption says, we count 48,787 AS junctions in BMM "
                "against about 10,000; with three reads we count 9,633 (BMM) but 19,240 in liver against 33,164. The NMD shares "
                "follow from the PTC calls.",
                [H("The counts use the three-read cutoff", "BMM 9,633 and liver 19,240 with three reads (hypotheses.json)", "inconclusive"),
                 H("No read cutoff, as the caption says", "BMM 48,787 and liver 82,709 against about 10,000 and 35,000", "rejected"),
                 PTC_ANNOT]),
 "fig3b": C("undocumented_setting", "AS junction counts depend on the read cutoff the caption says was not used: without one we "
            "find 1.5 to 3.7 times as many per sample; with three reads per sample, 5,783 and 8,190 in BMM against 8,107 and 9,447. Slopes are "
            "lower (BMM AS 0.26 against 0.35); liver KO has the steepest slope, as in the paper.",
            [H("Three reads per sample", "BMM 5,783 and 8,190, liver 9,001 and 16,703 against 8,107, 9,447, 25,390, 31,041", "rejected"),
             H("No cutoff", "26,452 to 63,812 per sample", "rejected")]),
 "table1": C("undocumented_setting", "We find fewer regulated events with the three-read evidence rule (BMM ES 275 against 730) "
             "and far more without it (2,255). The share of ES events that are PTC+ comes back (BMM 37% against 38%), the other "
             "classes' PTC+ shares are lower (PTC calls), and MXE is rare under our stricter rule.",
             [H("No read cutoff for events", "BMM ES 2,255, A5SS 619 against 730 and 130", "rejected"),
              H("Three reads in WT or KO", "BMM ES 275, A5SS 139 against 730 and 130", "rejected"), PTC_ANNOT]),
 "text.examples": C("undocumented_setting", "Tmem183a comes back (dPSI 49% and 57% against 51% and 54%) and Srsf9 rises in liver "
                    "(45%, against the paper's -40%, which for a PTC-upon-inclusion event has the wrong sign). Mgea5, Rps12 and "
                    "Smg5 are not called as the class the paper names; the paper does not give their junctions (Mgea5's are in "
                    "Additional file 9, but its skipped exon is not a single annotated exon in today's tables).",
                    [H("The events are present but in another class", "Mgea5 junctions from Additional file 9 are in our table; "
                       "no SES event is formed", "inconclusive"),
                     H("Soat2 fold change differs from read counting against Cufflinks", "BMM 12.8 against 8.4; liver 4.12 against "
                       "4.2", "inconclusive")]),
 "tableS5": C("undocumented_setting", "Gene fold changes of the 25 factors agree to about 10% (BMM Srsf6 1.32 against 1.31, Ptbp2 "
              "4.39 against 4.38); the canonical fold changes need the paper's 'major up-regulated PTC-eliciting event' per gene, "
              "which we find for fewer genes (PTC calls), so most are missing.",
              [H("Gene fold change from reads in the longest RefSeq model in place of Cufflinks", "Within 10% for most factors", "supported"),
               PTC_ANNOT], "explained"),
 "text.tableS5": C("unknown", "We find a PTC+ event for 8 of the liver factors against 19, and 5 of them are deregulated "
                   "more than 1.5-fold (all down). The count follows from the PTC calls.", [PTC_ANNOT, PTC_FP, PTC_DIST]),
 "tableS7": PTC_CAUSE,
 "tableS8": PTC_CAUSE,
 "fig5.a": C("undocumented_setting", "The curves have the paper's shape (exons high, introns low) but the event groups are smaller "
             "and differently composed, and the score cannot tell ours from a curve shifted by 3 nt.",
             [H("Wrong groups drawn", "PTC+ and PTC- swapped scores 38.7%, inclusion events 32.9%, ours 40.4%", "inconclusive"),
              PTC_ANNOT, PTC_FP]),
 "fig5.b": C("undocumented_setting", "Inclusion events: ours scores below the exclusion events drawn in their place, so the "
             "comparison cannot confirm this panel.", [H("Wrong groups drawn", "Exclusion events in place of inclusion score 39.8%, "
             "ours 31.4%", "rejected"), PTC_ANNOT, PTC_FP]),
 "fig5.counts": C("undocumented_setting", "Fewer SES events in most groups (liver exclusion PTC+ 310 against 439, unregulated 1,845 "
                  "against 3,494), more in the inclusion groups (97 and 171 against 64 and 162); RefSeq exons 180,246 unique internal exons against 274,281.",
                  [H("RefSeq exons counted with repeats across transcripts", "All refGene exons: 447,279, internal unique 180,246", "rejected"),
                   PTC_ANNOT, PTC_FP]),
 "figS4": C("undocumented_setting", "As Fig. 5: fewer BMM events in most groups.", [PTC_ANNOT, PTC_FP,
            H("RefSeq exons counted with repeats", "447,279 and 180,246, neither 274,281", "rejected")]),
 "text.conservation": C("undocumented_setting", "The direction of every comparison but one comes back (regulated introns more "
                        "conserved than unregulated, PTC- introns above PTC+ for exclusion); the P values are larger than the "
                        "paper's 2.2e-16 with our smaller groups, and PTC- inclusion introns are not above PTC+ in liver.",
                        [H("Smaller groups give larger P", "Liver exclusion against unregulated P = 1.4e-14 with 506 and 1,845 events", "supported"),
                         PTC_ANNOT], "explained"),
 "fig6": C("unknown", "Our curves fall with expression as the paper's do, but our PTC+ fraction lies well below the paper's "
           "at every expression level (the PTC calls), so no curve lies within 3 px.", [PTC_ANNOT, PTC_FP, PTC_DIST]),
 "text.fig6": C("data_unavailable", "Low-expressed junctions are enriched in PTC+ and KO lies above WT, as in the paper; liver lies "
                "below BMM in the two lowest bins (1 and 2 RPKM) and above it from 3 RPKM up.", [PTC_ANNOT, PTC_FP, PTC_DIST]),
 "fig7a": C("undocumented_setting", "Our curves lie below the paper's (no pixel within 3 px): the random-exon baseline (which exons, which "
            "window) is described in one sentence.", [H("Random RefSeq exons for every curve", "Moves all curves together; the gap "
            "between PTC+ and normal stops stays", "inconclusive"),
            H("Positions outside the stop's exon kept", "Not kept, as the caption says; the dip after the normal stop remains", "rejected")]),
 "figS5": PTC_CAUSE,
 "fig7b": C("unknown", "The codon shares come back within 0.02 for 18 of 18 bars and UGA is preferred in both tissues "
            "(Fisher P 0.0065 and 4e-14); there are fewer junctions (196 and 504 against 497 and 670), from the PTC calls.",
            [PTC_ANNOT, PTC_FP, PTC_DIST]),
 "figS2.a": C("data_unavailable", "Today's RefSeq has more short 3' UTRs in the first bin (2,135 against about 600); after 100 nt "
              "our bars fall as the paper's do but run 10 to 20% lower, 13 of 42 bins within tolerance.", [H("Distance measured to the end of the stop codon or its start", "A 3-nt shift "
              "moves few genes between 50-nt bins", "rejected"), H("RefSeq version", "refGene regenerated in 2020 holds 21,619 "
              "coding models against 21,470", "inconclusive")]),
 "figS2.b": C("data_unavailable", "Same RefSeq version; the bars agree within tolerance in 35 of 52 bins and the cut at about 46 nt "
              "comes back.", [H("RefSeq version", "995 genes with a stop in the penultimate exon; the paper's bars sum to about the same", "inconclusive"),
              H("Distance convention (a shift of 2 nt)", "Our bin 20 peaks (71) where the paper's dips (34.5) and its bin 18 peaks "
                "(59.6); a 2-nt shift would line these up, but it would break the 42 of 45 exact PTC distances, which use the "
                "same convention", "inconclusive")]),
 "port.ptc_distance": C("unknown", "58 of 76 events give the printed distance. Of the 18 misses, 5 lose their annotated start or "
                        "have no coding model in today's tables, 7 are not called PTC+ (Arih2, Il4ra, Prpf38b, Rps9, Scaf1, Tra2b, "
                        "Phkg2) and 6 give another distance (Luc7l, Rabggtb, Srsf6, Abhd10, Hsf1, Prei4); that these come from "
                        "changed annotation is not shown.",
                        [H("A distance convention", "42 of 45 exclusion events called PTC+ equal the printed value exactly", "rejected"),
                         H("Annotation version", "5 of the 18 misses are ambiguous CDS or no model in today's tables; the other 13 "
                           "are not traced to an annotation change", "inconclusive")]),
 "text.go_core": None,
}
