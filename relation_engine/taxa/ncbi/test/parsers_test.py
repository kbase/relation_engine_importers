from io import StringIO
from pytest import raises

from relation_engine.taxa.ncbi.parsers import NCBINodeProvider

from relation_engine.test.testing_helpers import assert_exception_correct


def test_node_provider_trivial():
    # A basic test to show the parser is working for simple cases.
    names = StringIO("\n".join([
        " \t  62  |  nerf herder  | Herdere le nerfe  \t  |  synonym    \t  |",
        " \t 62  |  \t  l. skywalkerii   |    |   scientific name   \t  | ",
        " \t 62  |  \t  scum and villany \t   |    | \t   type material   \t  | ",
        "     63   |    \t    c. bacca  \t   |   |  scientific name  \t   | "
    ]))

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
        # TODO this node will not get marked as a strain, which is a bug that will be
        # corrected shortly
        " 72	|	71	|	no rank   	|		|	6	|	0	|	11	|	0	|	0	|	0	|	0	|0	|		|",
        # TODO also a bug; the parser will be updated to throw an error on an unknown rank
        " 73	|	44	|	fake rank   	|		|	6	|	0	|	11	|	0	|	0	|	0	|	0	|0	|		|",
        " 74	|	44	|	no rank   	|		|	6	|	0	|	11	|	0	|	0	|	0	|	0	|0	|		|",
    ]))

    res = list(NCBINodeProvider(names, nodes))

    assert res == [
        {
            'id':                         "62",
            'scientific_name':            "l. skywalkerii",
            'rank':                       "species",
            'strain':                     False,
            'aliases':                    [{"category": "synonym", "name": "nerf herder"}],
            'ncbi_taxon_id':              62,
            'gencode':                    8,
        },
        {
            'id':                         "63",
            'scientific_name':            "c. bacca",
            'rank':                       "strain",
            'strain':                     False,
            'aliases':                    [],
            'ncbi_taxon_id':              63,
            'gencode':                    11,
        },
        {
            'id':                         "67",
            'scientific_name':            "sciname67",
            'rank':                       "no rank",
            'strain':                     True,
            'aliases':                    [],
            'ncbi_taxon_id':              67,
            'gencode':                    12,
        },
        {
            'id':                         "68",
            'scientific_name':            "sciname68",
            'rank':                       "no rank",
            'strain':                     True,
            'aliases':                    [],
            'ncbi_taxon_id':              68,
            'gencode':                    11,
        },
        {
            'id':                         "69",
            'scientific_name':            "sciname69",
            'rank':                       "subspecies",
            'strain':                     False,
            'aliases':                    [],
            'ncbi_taxon_id':              69,
            'gencode':                    11,
        },
        {
            'id':                         "70",
            'scientific_name':            "sciname70",
            'rank':                       "no rank",
            'strain':                     True,
            'aliases':                    [],
            'ncbi_taxon_id':              70,
            'gencode':                    11,
        },
        {
            'id':                         "71",
            'scientific_name':            "sciname71",
            'rank':                       "forma",
            'strain':                     False,
            'aliases':                    [],
            'ncbi_taxon_id':              71,
            'gencode':                    11,
        },
        {
            'id':                         "72",
            'scientific_name':            "sciname72",
            'rank':                       "no rank",
            'strain':                     False,
            'aliases':                    [],
            'ncbi_taxon_id':              72,
            'gencode':                    11,
        },
        {
            'id':                         "73",
            'scientific_name':            "sciname73",
            'rank':                       "fake rank",
            'strain':                     False,
            'aliases':                    [],
            'ncbi_taxon_id':              73,
            'gencode':                    11,
        },
        {
            'id':                         "74",
            'scientific_name':            "sciname74",
            'rank':                       "no rank",
            'strain':                     False,
            'aliases':                    [],
            'ncbi_taxon_id':              74,
            'gencode':                    11,
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

    with raises(Exception) as got:
        list(NCBINodeProvider(names, nodes))
    assert_exception_correct(got.value, ValueError("Node 62 has 2 scientific names"))
