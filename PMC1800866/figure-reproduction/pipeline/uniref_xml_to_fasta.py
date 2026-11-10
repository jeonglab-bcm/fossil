#!/usr/bin/env python3
"""Stream a UniRef XML release (gzip) to FASTA: one record per cluster, its representative sequence.
Usage: uniref_xml_to_fasta.py uniref100.xml.gz > uniref100.fasta"""
import gzip
import sys
import xml.etree.ElementTree as ET

NS = "{http://uniprot.org/uniref}"
out = sys.stdout
n = 0
for event, el in ET.iterparse(gzip.open(sys.argv[1]), events=("end",)):
    if el.tag == NS + "entry":
        seq = el.find(f"{NS}representativeMember/{NS}sequence")
        if seq is not None and seq.text:
            s = "".join(seq.text.split())
            out.write(f">{el.get('id')}\n")
            for i in range(0, len(s), 80):
                out.write(s[i:i + 80] + "\n")
            n += 1
        el.clear()
print(f"{n} sequences", file=sys.stderr)
