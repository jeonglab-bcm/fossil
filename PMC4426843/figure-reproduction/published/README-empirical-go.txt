Instructions for Empirical GO Algorithm
---------------------------------------

The script empiricalGO.py generates the empirical distribution of the
number of miRNA target genes in GO terms and returns p-values for
enrichment.  Significance after Benjamini-Hochberg is indicated by *
for < 0.05 FDR and ** for < 0.01 FDR.

System Requirements:

Run from the command line on a machine with Python
(https://www.python.org/) installed.

Required Files:

This script requires reference to several public datasets, which must
be downloaded by the user.

(1) Input miRNA list, which is a text file containing only the names
of differentially expressed miRNAs, each on a separate line. For
example

hsa-miR-132-5p
hsa-miR-132-3p

(2) Ensembl formatted annotations of genes to GO terms. From
www.ensembl.org/biomart/martview/ select Ensembl Genes 75, species of
interest. In attributes select Ensembl Gene ID, Ensembl Transcript ID,
Associated Gene Name, GO Term Accession, GO Term Name, GO Term
Definition, GO domain.

(3) Output from miRanda target prediction run. This requires:

(3a) FASTA sequences for known mature miRNA from
http://www.mirbase.org/ftp.shtml filtered for species of interest

(3b) FASTA sequences for 3' UTR of genes from http://www.biomart.org/
select Sequence Retrieval, select 3' UTR, select headers Ensembl Gene
ID, Ensembl Transcript ID, Associated Gene Name. Remove entries with
Sequence Unavailable.

(3c) miRanda software from
http://www.microrna.org/microrna/getDownloads.do

To generate correct format for script input, please run as: 

miranda hsa-mature-miRNA.fa ensembl3utr.txt -quiet | grep '>>hsa' >
   miRandaPredictions.txt

(4) Gene synonym data from NCBI,
ftp://ftp.ncbi.nlm.nih.gov/gene/DATA/gene_info

(5) miRNA aliases for older versions of miRBase from
ftp://mirbase.org/pub/mirbase/CURRENT/aliases.txt

To Run:

python empirical.py -miRNA miRNA.txt -ontology hsa-ensembl-go.txt
   -miRanda miRandaPredictions.txt -synonyms gene_info -alias aliases.txt


Additional options are available:

-mode select 'basic' or 'multihit' for the improved algorithm taking
 into account convergence of multiple miRNAs on genes

-processors integer value for processors to be used in parallel

-iterations integer number of iterations to be run (note actual number
 run with be rounded to a multiple of processor count)

-add filename for a list of genes to be added as an extra functional
 category

-output specify output filename

-species specify 'human' or 'mouse'
