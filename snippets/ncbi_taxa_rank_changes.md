Figure out how NCBI taxa ranks change over time.

```
~/SCIENCE/taxonomy/ncbi$ ipython
Python 3.9.6 (default, Jul  3 2021, 17:50:42) 
Type 'copyright', 'credits' or 'license' for more information
IPython 7.30.0 -- An enhanced Interactive Python. Type '?' for help.

In [1]: from collections import defaultdict
In [2]: import re
In [3]: import shutil

In [4]: taxdumps = !ls taxdmp*

In [5]: len(taxdumps)
Out[5]: 93

In [6]: taxdumps[0:2]
Out[6]: ['taxdmp_2014-08-01.zip', 'taxdmp_2014-09-01.zip']

In [7]: taxdumps[-2:]
Out[7]: ['taxdmp_2022-06-01.zip', 'taxdmp_2022-07-01.zip']

In [9]: def ncbi_tax_ranks(files):
   ...:     ranks = defaultdict(set)
   ...:     for f in files:
   ...:         print(f)
   ...:         shutil.unpack_archive(f, 'temp')
   ...:         with open('temp/nodes.dmp') as nodes:
   ...:             for line in nodes:
   ...:                 rank = re.split(r'\s\|\s?', line)[2].strip()
   ...:                 ranks[f].add(rank)
   ...:     return ranks
   ...: 

In [10]: ranks = ncbi_tax_ranks(taxdumps)
taxdmp_2014-08-01.zip
*snip*
taxdmp_2022-07-01.zip

In [13]: def print_rank_changes(ranks):
    ...:     rsort = sorted(ranks.keys())
    ...:     file = rsort[0]
    ...:     print(file, sorted(ranks[file]))
    ...:     for nextfile in rsort[1:]:
    ...:         added = ranks[nextfile] - ranks[file]
    ...:         removed = ranks[file] - ranks[nextfile]
    ...:         if added or removed:
    ...:             print(nextfile)
    ...:             if added:
    ...:                 print('Added:', sorted(added))
    ...:             if removed:
    ...:                 print('Removed:', sorted(removed))
    ...:         file = nextfile
    ...: 
    ...: 
    ...: 

In [14]: print_rank_changes(ranks)
taxdmp_2014-08-01.zip ['class', 'family', 'forma', 'genus', 'infraclass', 'infraorder', 'kingdom', 'no rank', 'order', 'parvorder', 'phylum', 'species', 'species group', 'species subgroup', 'subclass', 'subfamily', 'subgenus', 'subkingdom', 'suborder', 'subphylum', 'subspecies', 'subtribe', 'superclass', 'superfamily', 'superkingdom', 'superorder', 'superphylum', 'tribe', 'varietas']
taxdmp_2017-06-01.zip
Added: ['cohort']
taxdmp_2019-03-01.zip
Added: ['subcohort']
taxdmp_2019-05-01.zip
Added: ['section', 'series', 'subsection']
taxdmp_2020-07-01.zip
Added: ['biotype', 'clade', 'forma specialis', 'genotype', 'isolate', 'morph', 'pathogroup', 'serogroup', 'serotype', 'strain', 'subvariety']
taxdmp_2021-09-01.zip
Removed: ['subvariety']
```