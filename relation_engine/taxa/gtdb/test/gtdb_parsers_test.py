from io import StringIO
from pytest import raises

from relation_engine.taxa.gtdb.parsers import GTDBNodeProvider, GTDBEdgeProvider

from relation_engine.test.testing_helpers import assert_exception_correct


def test_node_provider():
    names = StringIO("\n".join([
        "RS_GCF_000566285.1	d__Bacteria;p__Proteobacteria;c__Gammaproteobacteria;"
        + "o__Enterobacterales;f__Enterobacteriaceae;g__Escherichia;s__Escherichia coli",
        "RS_GCF_003460375.1	d__Bacteria;p__Proteobacteria;c__Gammaproteobacteria;"
        + "o__Enterobacterales;f__Enterobacteriaceae;g__Escherichia;s__Escherichia coli"
    ]))

    res = list(GTDBNodeProvider(names))

    assert res == [
        {
            "id": "d:Bacteria",
            "rank": "domain",
            "scientific_name": "Bacteria",
            "species_or_below": False
        },
        {
            "id": "p:Proteobacteria",
            "rank": "phylum",
            "scientific_name": "Proteobacteria",
            "species_or_below": False
        },
        {
            "id": "c:Gammaproteobacteria",
            "rank": "class",
            "scientific_name": "Gammaproteobacteria",
            "species_or_below": False
        },
        {
            "id": "o:Enterobacterales",
            "rank": "order",
            "scientific_name": "Enterobacterales",
            "species_or_below": False
        },
        {
            "id": "f:Enterobacteriaceae",
            "rank": "family",
            "scientific_name": "Enterobacteriaceae",
            "species_or_below": False
        },
        {
            "id": "g:Escherichia",
            "rank": "genus",
            "scientific_name": "Escherichia",
            "species_or_below": False
        },
        {
            "id": "s:Escherichia_coli",
            "rank": "species",
            "scientific_name": "Escherichia coli",
            "species_or_below": True
        },
        {
            "id": "RS_GCF_000566285.1",
            "rank": "genome",
            "scientific_name": "Escherichia coli",
            "species_or_below": True
        },
        {
            "id": "RS_GCF_003460375.1",
            "rank": "genome",
            "scientific_name": "Escherichia coli",
            "species_or_below": True
        },
    ]


def test_node_provider_fail():
    names = StringIO("\n".join([
        "RS_GCF_000566285.1	d__Bacteria;p__Proteobacteria;c__Gammaproteobacteria;"
        + "o__Enterobacterales;f__Enterobacteriaceae;g__Escherichia;s__Escherichia coli",
        "RS_GCF_003460375.1	d__Bacteria;p__Proteobacteria;c__Gammaproteobacteria;"
        + "o__Enterobacterales;f__Enterobacteriaceae;g__Escherichia;x__Escherichia coli"
    ]))

    with raises(Exception) as got:
        list(GTDBNodeProvider(names))
    assert_exception_correct(got.value, ValueError(
        "Lineage d__Bacteria;p__Proteobacteria;c__Gammaproteobacteria;o__Enterobacterales;"
        + "f__Enterobacteriaceae;g__Escherichia;x__Escherichia coli does not end with species"))


def test_edge_provider():
    names = StringIO("\n".join([
        "RS_GCF_000566285.1	d__Bacteria;p__Proteobacteria;c__Gammaproteobacteria;"
        + "o__Enterobacterales;f__Enterobacteriaceae;g__Escherichia;s__Escherichia coli",
        "RS_GCF_003460375.1	d__Bacteria;p__Proteobacteria;c__Gammaproteobacteria;"
        + "o__Enterobacterales;f__Enterobacteriaceae;g__Escherichia;s__Escherichia coli"
    ]))

    res = list(GTDBEdgeProvider(names))

    assert res == [
        {
            "id": "p:Proteobacteria",
            "from": "p:Proteobacteria",
            "to": "d:Bacteria"
        },
        {
            "id": "c:Gammaproteobacteria",
            "from": "c:Gammaproteobacteria",
            "to": "p:Proteobacteria"
        },
        {
            "id": "o:Enterobacterales",
            "from": "o:Enterobacterales",
            "to": "c:Gammaproteobacteria"
        },
        {
            "id": "f:Enterobacteriaceae",
            "from": "f:Enterobacteriaceae",
            "to": "o:Enterobacterales"
        },
        {
            "id": "g:Escherichia",
            "from": "g:Escherichia",
            "to": "f:Enterobacteriaceae"
        },
        {
            "id": "s:Escherichia_coli",
            "from": "s:Escherichia_coli",
            "to": "g:Escherichia"
        },
        {
            "id": "RS_GCF_000566285.1",
            "from": "RS_GCF_000566285.1",
            "to": "s:Escherichia_coli"
        },
        {
            "id": "RS_GCF_003460375.1",
            "from": "RS_GCF_003460375.1",
            "to": "s:Escherichia_coli"
        },
    ]


def test_edge_provider_fail():
    names = StringIO("\n".join([
        "RS_GCF_000566285.1	d__Bacteria;p__Proteobacteria;c__Gammaproteobacteria;"
        + "o__Enterobacterales;f__Enterobacteriaceae;g__Escherichia;s__Escherichia coli",
        "RS_GCF_003460375.1	d__Bacteria;p__Proteobacteria;c__Gammaproteobacteria;"
        + "o__Enterobacterales;f__Enterobacteriaceae;g__Escherichia;y__Escherichia coli"
    ]))

    with raises(Exception) as got:
        list(GTDBEdgeProvider(names))
    assert_exception_correct(got.value, ValueError(
        "Lineage d__Bacteria;p__Proteobacteria;c__Gammaproteobacteria;o__Enterobacterales;"
        + "f__Enterobacteriaceae;g__Escherichia;y__Escherichia coli does not end with species"))
