from io import StringIO
from pytest import raises

from relation_engine.taxa.ncbi.parsers import NCBINodeProvider, NCBIEdgeProvider, NCBIMergeProvider

from relation_engine.test.testing_helpers import assert_exception_correct

SIMPLE_NAMES = "\n".join([
        " \t  62  |  nerf herder  | Herdere le nerfe  \t  |  synonym    \t  |",
        " \t 62  |  \t  l. skywalkerii   |    |   scientific name   \t  | ",
        " \t 62  |  \t  scum and villany \t   |    | \t   type material   \t  | ",
        "     63   |    \t    c. bacca  \t   |   |  scientific name  \t   | "
])


def test_node_provider_trivial():
    # A basic test to show the parser is working for simple cases.
    names = StringIO(SIMPLE_NAMES)

    nodes = StringIO("\n".join([
        "62	|	44	|	species   	|		|	8	|	0	|	8	|	0	|	0	|	0	|	0	|0	|		|",
        " 63	|	44	|	strain   	|		|	6	|	0	|	11	|	0	|	0	|	0	|	0	|0	|		|",
    ]))

    res = list(NCBINodeProvider(names, nodes))

    assert res == [
        {
            'id':                         "62",
            'scientific_name':            "l. skywalkerii",
            'rank':                       "species",
            'strain':                     False,
            'species_or_below':           True,
            'aliases':                    [
                {"category": "synonym", "name": "nerf herder"},
                {"category": "type material", "name": "scum and villany"},
                ],
            'ncbi_taxon_id':              62,
            'gencode':                    8,
        },
        {
            'id':                         "63",
            'scientific_name':            "c. bacca",
            'rank':                       "strain",
            'strain':                     False,
            'species_or_below':           True,
            'aliases':                    [],
            'ncbi_taxon_id':              63,
            'gencode':                    11,
        }
    ]


def test_node_provider_complex():
    # Test the more complex operations of the provider, mostly around strain determination
    names = StringIO("\n".join([
        " \t  62  |  nerf herder  | Herdere le nerfe  \t  |  synonym    \t  |",
        " \t 62  |  \t  l. skywalkerii   |    |   scientific name   \t  | ",
        "     63   |    \t    c. bacca  \t   |   |  scientific name  \t   | ",
        "     67   |    \t    sciname67  \t   |   |  scientific name  \t   | ",
        "     68   |    \t    sciname68  \t   |   |  scientific name  \t   | ",
        "     69   |    \t    sciname69  \t   |   |  scientific name  \t   | ",
        "     70   |    \t    sciname70  \t   |   |  scientific name  \t   | ",
        "     71   |    \t    sciname71  \t   |   |  scientific name  \t   | ",
        "     72   |    \t    sciname72  \t   |   |  scientific name  \t   | ",
        "     73   |    \t    sciname73  \t   |   |  scientific name  \t   | ",
        "     74   |    \t    sciname74  \t   |   |  scientific name  \t   | ",
    ]))

    nodes = StringIO("\n".join([
        "62	|	44	|	species   	|		|	8	|	0	|	8	|	0	|	0	|	0	|	0	|0	|		|",
        " 63	|	44	|	strain   	|		|	6	|	0	|	11	|	0	|	0	|	0	|	0	|0	|		|",
        "67	|	62	|	no rank   	|		|	8	|	0	|	12	|	0	|	0	|	0	|	0	|0	|		|",
        " 68	|	67	|	no rank   	|		|	6	|	0	|	11	|	0	|	0	|	0	|	0	|0	|		|",
        " 69	|	62	|	subspecies   	|		|	6	|	0	|	11	|	0	|	0	|	0	|	0	|0	|		|",
        " 70	|	69	|	no rank   	|		|	6	|	0	|	11	|	0	|	0	|	0	|	0	|0	|		|",
        " 71	|	62	|	forma   	|		|	6	|	0	|	11	|	0	|	0	|	0	|	0	|0	|		|",
        " 72	|	71	|	clade   	|		|	6	|	0	|	11	|	0	|	0	|	0	|	0	|0	|		|",
        " 73	|	72	|	no rank   	|		|	6	|	0	|	11	|	0	|	0	|	0	|	0	|0	|		|",
        " 74	|	44	|	no rank   	|		|	6	|	0	|	11	|	0	|	0	|	0	|	0	|0	|		|",
    ]))

    res = list(NCBINodeProvider(names, nodes))

    assert res == [
        {
            'id':                         "62",
            'scientific_name':            "l. skywalkerii",
            'rank':                       "species",
            'strain':                     False,
            'species_or_below':           True,
            'aliases':                    [{"category": "synonym", "name": "nerf herder"}],
            'ncbi_taxon_id':              62,
            'gencode':                    8,
        },
        {
            'id':                         "63",
            'scientific_name':            "c. bacca",
            'rank':                       "strain",
            'strain':                     False,
            'species_or_below':           True,
            'aliases':                    [],
            'ncbi_taxon_id':              63,
            'gencode':                    11,
        },
        {
            'id':                         "67",
            'scientific_name':            "sciname67",
            'rank':                       "no rank",
            'strain':                     True,
            'species_or_below':           True,
            'aliases':                    [],
            'ncbi_taxon_id':              67,
            'gencode':                    12,
        },
        {
            'id':                         "68",
            'scientific_name':            "sciname68",
            'rank':                       "no rank",
            'strain':                     True,
            'species_or_below':           True,
            'aliases':                    [],
            'ncbi_taxon_id':              68,
            'gencode':                    11,
        },
        {
            'id':                         "69",
            'scientific_name':            "sciname69",
            'rank':                       "subspecies",
            'strain':                     False,
            'species_or_below':           True,
            'aliases':                    [],
            'ncbi_taxon_id':              69,
            'gencode':                    11,
        },
        {
            'id':                         "70",
            'scientific_name':            "sciname70",
            'rank':                       "no rank",
            'strain':                     True,
            'species_or_below':           True,
            'aliases':                    [],
            'ncbi_taxon_id':              70,
            'gencode':                    11,
        },
        {
            'id':                         "71",
            'scientific_name':            "sciname71",
            'rank':                       "forma",
            'strain':                     False,
            'species_or_below':           True,
            'aliases':                    [],
            'ncbi_taxon_id':              71,
            'gencode':                    11,
        },
        {
            'id':                         "72",
            'scientific_name':            "sciname72",
            'rank':                       "clade",
            'strain':                     True,
            'species_or_below':           True,
            'aliases':                    [],
            'ncbi_taxon_id':              72,
            'gencode':                    11,
        },
        {
            'id':                         "73",
            'scientific_name':            "sciname73",
            'rank':                       "no rank",
            'strain':                     True,
            'species_or_below':           True,
            'aliases':                    [],
            'ncbi_taxon_id':              73,
            'gencode':                    11,
        },
        {
            'id':                         "74",
            'scientific_name':            "sciname74",
            'rank':                       "no rank",
            'strain':                     False,
            'species_or_below':           False,
            'aliases':                    [],
            'ncbi_taxon_id':              74,
            'gencode':                    11,
        },
    ]


_NON_SPECIES_RANKS = [
    "superkingdom",
    "kingdom",
    "subkingdom",
    "superphylum",
    "phylum",
    "subphylum",
    "infraphylum",
    "superclass",
    "class",
    "subclass",
    "infraclass",
    "cohort",
    "subcohort",
    "superorder",
    "order",
    "suborder",
    "infraorder",
    "parvorder",
    "superfamily",
    "family",
    "subfamily",
    "tribe",
    "subtribe",
    "genus",
    "subgenus",
    "section",
    "subsection",
    "series",
    "subseries",
    "species group",
    "species subgroup",
]


def test_node_provider_non_species_ranks():
    # test that non-species ranks are accepted and don't result in marking non hierarchical ranks
    # below them as strains.
    # This test duplicates the list of ranks from ranks.py, which it should - if someone screws
    # up ranks.py this test should fail. It will not if it just imports and uses the same
    # rank set.
    for rank in _NON_SPECIES_RANKS:
        names = StringIO("\n".join([
            "  \t 5  |  \t  name5   |    |   scientific name   \t  | ",
            "  \t 10  |  \t  name10   |    |   scientific name   \t  | ",
            "  \t 15  |  \t  name15   |    |   scientific name   \t  | ",
            "  \t 100  |  \t  name100   |    |   scientific name   \t  | ",
            "  \t 105  |  \t  name105   |    |   scientific name   \t  | ",
            "  \t 110  |  \t  name110   |    |   scientific name   \t  | ",
        ]))
        nodes = StringIO("\n".join([
            f" 5	|	1	|	{rank}   	|		|	8	|	0	|	1	|	0	|	0	|	0	|	0	|0	|		|",
            " 10	|	5	|	clade   	|		|	8	|	0	|	1	|	0	|	0	|	0	|	0	|0	|		|",
            " 15	|	10	|	no rank   	|		|	8	|	0	|	1	|	0	|	0	|	0	|	0	|0	|		|",
            " 100	|	678	|	varietas   	|		|	8	|	0	|	1	|	0	|	0	|	0	|	0	|0	|		|",
            " 105	|	100	|	no rank   	|		|	8	|	0	|	1	|	0	|	0	|	0	|	0	|0	|		|",
            " 110	|	105	|	clade   	|		|	8	|	0	|	1	|	0	|	0	|	0	|	0	|0	|		|",
        ]))

        res = list(NCBINodeProvider(names, nodes))

        assert res == [
            {
                'id':                         "5",
                'scientific_name':            "name5",
                'rank':                       rank,
                'strain':                     False,
                'species_or_below':           False,
                'aliases':                    [],
                'ncbi_taxon_id':              5,
                'gencode':                    1,
            },
            {
                'id':                         "10",
                'scientific_name':            "name10",
                'rank':                       "clade",
                'strain':                     False,
                'species_or_below':           False,
                'aliases':                    [],
                'ncbi_taxon_id':              10,
                'gencode':                    1,
            },
            {
                'id':                         "15",
                'scientific_name':            "name15",
                'rank':                       "no rank",
                'strain':                     False,
                'species_or_below':           False,
                'aliases':                    [],
                'ncbi_taxon_id':              15,
                'gencode':                    1,
            },
            {
                'id':                         "100",
                'scientific_name':            "name100",
                'rank':                       "varietas",
                'strain':                     False,
                'species_or_below':           True,
                'aliases':                    [],
                'ncbi_taxon_id':              100,
                'gencode':                    1,
            },
            {
                'id':                         "105",
                'scientific_name':            "name105",
                'rank':                       "no rank",
                'strain':                     True,
                'species_or_below':           True,
                'aliases':                    [],
                'ncbi_taxon_id':              105,
                'gencode':                    1,
            },
            {
                'id':                         "110",
                'scientific_name':            "name110",
                'rank':                       "clade",
                'strain':                     True,
                'species_or_below':           True,
                'aliases':                    [],
                'ncbi_taxon_id':              110,
                'gencode':                    1,
            },
        ]


_SPECIES_RANKS = [
    "species",
    "forma specialis",
    "subspecies",
    "varietas",
    "morph",
    "subvariety",
    "forma",
    "serogroup",
    "pathogroup",
    "serotype",
    "biotype",
    "genotype",
    "strain",
    "isolate",
]


def test_node_provider_species_and_below_ranks():
    # test that species ranks are accepted and result in marking non hierarchical ranks
    # below them as strains.
    # This test duplicates the list of ranks from ranks.py, which it should - if someone screws
    # up ranks.py this test should fail. It will not if it just imports and uses the same
    # rank set.
    for rank in _SPECIES_RANKS:
        names = StringIO("\n".join([
            "  \t 5  |  \t  name5   |    |   scientific name   \t  | ",
            "  \t 10  |  \t  name10   |    |   scientific name   \t  | ",
            "  \t 15  |  \t  name15   |    |   scientific name   \t  | ",
            "  \t 100  |  \t  name100   |    |   scientific name   \t  | ",
            "  \t 105  |  \t  name105   |    |   scientific name   \t  | ",
            "  \t 110  |  \t  name110   |    |   scientific name   \t  | ",
        ]))
        nodes = StringIO("\n".join([
            f" 5	|	1	|	{rank}   	|		|	8	|	0	|	1	|	0	|	0	|	0	|	0	|0	|		|",
            " 10	|	5	|	clade   	|		|	8	|	0	|	1	|	0	|	0	|	0	|	0	|0	|		|",
            " 15	|	10	|	no rank   	|		|	8	|	0	|	1	|	0	|	0	|	0	|	0	|0	|		|",
            " 100	|	678	|	tribe   	|		|	8	|	0	|	1	|	0	|	0	|	0	|	0	|0	|		|",
            " 105	|	100	|	no rank   	|		|	8	|	0	|	1	|	0	|	0	|	0	|	0	|0	|		|",
            " 110	|	105	|	clade   	|		|	8	|	0	|	1	|	0	|	0	|	0	|	0	|0	|		|",
        ]))

        res = list(NCBINodeProvider(names, nodes))

        assert res == [
            {
                'id':                         "5",
                'scientific_name':            "name5",
                'rank':                       rank,
                'strain':                     False,
                'species_or_below':           True,
                'aliases':                    [],
                'ncbi_taxon_id':              5,
                'gencode':                    1,
            },
            {
                'id':                         "10",
                'scientific_name':            "name10",
                'rank':                       "clade",
                'strain':                     True,
                'species_or_below':           True,
                'aliases':                    [],
                'ncbi_taxon_id':              10,
                'gencode':                    1,
            },
            {
                'id':                         "15",
                'scientific_name':            "name15",
                'rank':                       "no rank",
                'strain':                     True,
                'species_or_below':           True,
                'aliases':                    [],
                'ncbi_taxon_id':              15,
                'gencode':                    1,
            },
            {
                'id':                         "100",
                'scientific_name':            "name100",
                'rank':                       "tribe",
                'strain':                     False,
                'species_or_below':           False,
                'aliases':                    [],
                'ncbi_taxon_id':              100,
                'gencode':                    1,
            },
            {
                'id':                         "105",
                'scientific_name':            "name105",
                'rank':                       "no rank",
                'strain':                     False,
                'species_or_below':           False,
                'aliases':                    [],
                'ncbi_taxon_id':              105,
                'gencode':                    1,
            },
            {
                'id':                         "110",
                'scientific_name':            "name110",
                'rank':                       "clade",
                'strain':                     False,
                'species_or_below':           False,
                'aliases':                    [],
                'ncbi_taxon_id':              110,
                'gencode':                    1,
            },
        ]


def test_node_provider_fail_multiple_scientific_names():
    names = StringIO("\n".join([
        "  \t  62  |  nerf herder  | Herdere le nerfe  \t  |  synonym    \t  |",
        "  \t 62  |  \t  l. skywalkerii   |    |   scientific name   \t  | ",
        "  \t 62  |  \t  filius vaderii   |    |   scientific name   \t  | ",
        "     63   |    \t    c. bacca  \t   |    |  scientific name  \t   | "
    ]))

    nodes = StringIO("\n".join([
        " 62	|	44	|	species   	|		|	8	|	0	|	1	|	0	|	0	|	0	|	0	|0	|		|",
        " 63	|	44	|	strain   	|		|	8	|	0	|	1	|	0	|	0	|	0	|	0	|0	|		|",
    ]))

    fail_node_provider(names, nodes, ValueError("Node 62 has 2 scientific names"))


def test_node_provider_fail_unexpected_rank():
    names = StringIO(SIMPLE_NAMES)

    nodes = StringIO("\n".join([
        " 62	|	44	|	species   	|		|	8	|	0	|	1	|	0	|	0	|	0	|	0	|0	|		|",
        " 63	|	44	|	fake rank   	|		|	8	|	0	|	1	|	0	|	0	|	0	|	0	|0	|		|",
    ]))

    fail_node_provider(names, nodes, ValueError("Node 63 has an unexpected rank of fake rank"))


def fail_node_provider(names, nodes, expected):
    with raises(Exception) as got:
        list(NCBINodeProvider(names, nodes))
    assert_exception_correct(got.value, expected)


def test_edge_provider():
    nodes = StringIO("\n".join([
        "1	|	1	|	no rank	|		|	8	|	0|	1	|	0	|	0	|	0	|	0	|0	|		|",
        "62	 \t|	44	\t|	species   	|		|	8	|	0	|	8	|	0	|	0	|	0	|	0	|0	|		|",
        "\t 63	|\t	51	|	strain   	|		|	6	|	0	|	11	|	0	|	0	|	0	|	0	|0	|		|",
    ]))

    edges = list(NCBIEdgeProvider(nodes))

    assert edges == [
        {
            "id": "62",
            "from": "62",
            "to": "44"
        },
        {
            "id": "63",
            "from": "63",
            "to": "51"
        },
    ]


def test_merge_provider():
    merges = StringIO("\n".join([
        "  12	  |	  74109	 |",
        "30	|	29	|",
        "36	|	184914	|",
    ]))

    mrg = list(NCBIMergeProvider(merges))

    assert mrg == [
        {
            "id": "12",
            "from": "12",
            "to": "74109",
        },
        {
            "id": "30",
            "from": "30",
            "to": "29",
        },
        {
            "id": "36",
            "from": "36",
            "to": "184914",
        },
    ]
