"""Settings of the CoLP rebuild. Each value says where it comes from (results_notes.json lists them as assumptions)."""

# Table 1B: the 13 locations and their GO terms (paper).
LOCATIONS = ["AT", "CC", "CT", "CY", "ER", "GL", "LS", "MT", "NO", "NU", "PX", "PM", "VU"]
LOC_TERMS = {"AT": "GO:0015629", "CC": "GO:0005938", "CT": "GO:0005813", "CY": "GO:0005829", "ER": "GO:0005783",
             "GL": "GO:0005794", "LS": "GO:0005764", "MT": "GO:0005739", "NO": "GO:0005730", "NU": "GO:0005634",
             "PX": "GO:0005777", "PM": "GO:0005886", "VU": "GO:0005773"}
PUBLISHED_TABLE1B = {"AT": 155, "CC": 41, "CT": 56, "CY": 308, "ER": 432, "GL": 222, "LS": 76, "MT": 419,
                     "NO": 128, "NU": 1731, "PX": 56, "PM": 1543, "VU": 85}

# Gold standard. The paper names six experimental codes; its 4570 proteins are those of Lee et al. 2008
# (Table S3), whose counts come back only from a 2007 release with every non-IEA code (found by search over
# 21 monthly releases from 2007 to 2012 and five code sets; see figure-reproduction/search/gold_standard_search.json).
GO_RELEASE = "2007-01-01"
CODES_STATED = {"EXP", "IDA", "IPI", "IMP", "IGI", "IEP"}
CODES_GOLD = CODES_STATED | {"TAS", "NAS", "IC", "ISS", "RCA", "ND"}

# Network (Table 1C). HPRD and Reactome from the Pathway Commons 2011 archive (Reactome complex
# co-membership as the physical links); Rual, Stelzl and Ewing from BioGRID by PubMed ID; Ramani's
# consolidated set without links supported by orthology alone. DIP needs a login and BIND is gone;
# Ramani's set carries 1,500 BIND links.
REACTOME_TYPES = {"IN_SAME_COMPONENT"}
Y2H_MS_PUBMED = {"RUAL2005": "PUBMED:16189514", "STELZL2005": "PUBMED:16169070", "EWING2007": "PUBMED:17353931"}
RAMANI_EXCLUDE = {"ORTHOLOGY"}

# Expression (Table 1D). Accessions are not printed; this mapping is rebuilt from the five cited studies.
CONDITIONS = ["normal", "low", "high"]
STUDIES = [
    {"id": "GSE5281", "series": "GSE5281", "file": "GSE5281_series_matrix.txt.gz", "platform": "GPL570",
     "condition": "normal", "select": r"\S+ control \d+"},
    {"id": "GSE5390", "series": "GSE5390", "file": "GSE5390_series_matrix.txt.gz", "platform": "GPL96",
     "condition": "normal", "select": r"brain_(healthy_)?control_sampleid_.*"},
    {"id": "GSE3185-GPL8300-low", "series": "GSE3185", "file": "GSE3185-GPL8300_series_matrix.txt.gz",
     "platform": "GPL8300", "condition": "low", "select": r"KHG-LG-.*", "subject_key": "GSE3185-LG-8300"},
    {"id": "GSE3185-GPL96-low", "series": "GSE3185", "file": "GSE3185-GPL96_series_matrix.txt.gz",
     "platform": "GPL96", "condition": "low", "select": r"KHG-LG-.*", "subject_key": "GSE3185-LG-96"},
    {"id": "GSE9885-GPL885-low", "series": "GSE9885", "file": "GSE9885_family.soft.gz", "platform": "GPL885",
     "condition": "low", "select": r"(PA|OL|FA)\d+", "two_colour": True, "subject_key": "GSE9885-LG"},
    {"id": "GSE3185-GPL8300-high", "series": "GSE3185", "file": "GSE3185-GPL8300_series_matrix.txt.gz",
     "platform": "GPL8300", "condition": "high", "select": r"KHG-HG-.*", "subject_key": "GSE3185-HG"},
    {"id": "GSE9885-GPL885-high", "series": "GSE9885", "file": "GSE9885_family.soft.gz", "platform": "GPL885",
     "condition": "high", "select": r"GL\d+", "two_colour": True, "subject_key": "GSE9885-GBM-885"},
    {"id": "GSE9885-GPL887-high", "series": "GSE9885", "file": "GSE9885_family.soft.gz", "platform": "GPL887",
     "condition": "high", "select": r"GL\d+", "two_colour": True, "subject_key": "GSE9885-GBM-887"},
    {"id": "GSE4271-GPL96", "series": "GSE4271", "file": "GSE4271-GPL96_series_matrix.txt.gz", "platform": "GPL96",
     "condition": "high", "select": r".*", "subject_key": "GSE4271"},
    {"id": "GSE4271-GPL97", "series": "GSE4271", "file": "GSE4271-GPL97_series_matrix.txt.gz", "platform": "GPL97",
     "condition": "high", "select": r".*", "subject_key": "GSE4271"},
]

# DC-kNN (Lee et al. 2008): k = 5, rho = 2 for human.
K = 5
RHO = 2.0
SEED = 20130506  # the paper's acceptance date; splits the gold standard for leave-two-out selection
THRESHOLD = 0.40  # possibility degree of a high-confidence location (paper)
ALPHA = 0.005  # high-confidence location: confidence above 99.5% of the gold-standard negatives (paper: P < 0.005)
