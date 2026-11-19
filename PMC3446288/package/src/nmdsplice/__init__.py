"""nmdsplice: RAINMAN rebuilt.

The junction-level method of Weischenfeldt J, Waage J, Tian G, et al. Mammalian tissues defective in
nonsense-mediated mRNA decay display highly aberrant splicing patterns. Genome Biology 13(5):R35
(2012). doi:10.1186/gb-2012-13-5-r35. The authors' RAINMAN scripts are lost; this package rebuilds,
from the paper's text and Additional file 1, the combinatorial exon-exon junction database, PTC
detection by the 50-nucleotide rule, TMM normalisation and fold changes, and the seven splice
classes with PSI and dPSI.
"""

from importlib import resources
from pathlib import Path

from .annotation import Gene, Transcript, read_genepred, refseq_genes
from .api import load_annotation, ptc_table, read_junctions, write_table
from .classes import Event, infer_events
from .fasta import Fasta
from .junctiondb import Junction, combinatorial_junctions, write_fasta
from .ptc import PTCResult, detect
from .quant import tmm_factors, upper_quartile_rpkm

__version__ = "0.1.0"

CITATION = ("Weischenfeldt J, Waage J, Tian G, et al. Mammalian tissues defective in nonsense-mediated "
            "mRNA decay display highly aberrant splicing patterns. Genome Biology 13(5):R35 (2012). "
            "doi:10.1186/gb-2012-13-5-r35")

__all__ = [
    "CITATION", "Event", "Fasta", "Gene", "Junction", "PTCResult", "Transcript", "combinatorial_junctions",
    "detect", "example_path", "infer_events", "load_annotation", "ptc_table", "read_genepred",
    "read_junctions", "refseq_genes", "tmm_factors", "upper_quartile_rpkm", "write_fasta", "write_table",
]


def example_path(name: str = "example_junctions.tsv") -> Path:
    """Path of a bundled example file or folder. See data/README.md."""
    path = resources.files(__name__) / "data" / name
    if not (path.is_file() or path.is_dir()):
        raise FileNotFoundError(f"no bundled example file {name!r}")
    return Path(str(path))
