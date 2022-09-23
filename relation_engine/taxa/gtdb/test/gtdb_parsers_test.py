from io import StringIO
from pytest import raises

from relation_engine.taxa.gtdb.parsers import GTDBNodeProvider, GTDBEdgeProvider

from relation_engine.test.testing_helpers import assert_exception_correct


def test_node_provider():
    bacnames = StringIO("\n".join([
        "RS_GCF_000566285.1	d__Bacteria;p__Proteobacteria;c__Gammaproteobacteria;"
        + "o__Enterobacterales;f__Enterobacteriaceae;g__Escherichia;s__Escherichia coli",
        "RS_GCF_003460375.1	d__Bacteria;p__Proteobacteria;c__Gammaproteobacteria;"
        + "o__Enterobacterales;f__Enterobacteriaceae;g__Escherichia;s__Escherichia coli"
    ]))
    arcnames = StringIO("\n".join([
        "RS_GCF_000979375.1	d__Archaea;p__Halobacteriota;c__Methanosarcinia;o__Methanosarcinales;"
        + "f__Methanosarcinaceae;g__Methanosarcina;s__Methanosarcina mazei",
        "RS_GCF_000970165.1	d__Archaea;p__Halobacteriota;c__Methanosarcinia;o__Methanosarcinales;"
        + "f__Methanosarcinaceae;g__Methanosarcina;s__Methanosarcina mazei"
    ]))

    res = list(GTDBNodeProvider(bacnames, arcnames))

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
        {
            'id': 'd:Archaea',
            'rank': 'domain',
            'scientific_name': 'Archaea',
            'species_or_below': False
        },
        {
            'id': 'p:Halobacteriota',
            'rank': 'phylum',
            'scientific_name': 'Halobacteriota',
            'species_or_below': False
        },
        {
            'id': 'c:Methanosarcinia',
            'rank': 'class',
            'scientific_name': 'Methanosarcinia',
            'species_or_below': False
        },
        {
            'id': 'o:Methanosarcinales',
            'rank': 'order',
            'scientific_name': 'Methanosarcinales',
            'species_or_below': False
        },
        {
            'id': 'f:Methanosarcinaceae',
            'rank': 'family',
            'scientific_name': 'Methanosarcinaceae',
            'species_or_below': False
        },
        {
            'id': 'g:Methanosarcina',
            'rank': 'genus',
            'scientific_name': 'Methanosarcina',
            'species_or_below': False
        },
        {
            'id': 's:Methanosarcina_mazei',
            'rank': 'species',
            'scientific_name': 'Methanosarcina mazei',
            'species_or_below': True
        },
        {
            'id': 'RS_GCF_000979375.1',
            'rank': 'genome',
            'scientific_name': 'Methanosarcina mazei',
            'species_or_below': True
        },
        {
            'id': 'RS_GCF_000970165.1',
            'rank': 'genome',
            'scientific_name': 'Methanosarcina mazei',
            'species_or_below': True
        },
    ]


def test_node_provider_fail():
    lin = StringIO("\n".join([
        "RS_GCF_000566285.1	d__Bacteria;p__Proteobacteria;c__Gammaproteobacteria;"
        + "o__Enterobacterales;f__Enterobacteriaceae;g__Escherichia;s__Escherichia coli",
        "RS_GCF_003460375.1	d__Bacteria;p__Proteobacteria;c__Gammaproteobacteria;"
        + "o__Enterobacterales;f__Enterobacteriaceae;g__Escherichia;x__Escherichia coli"
    ]))
    _node_provider_fail(
        lin,
        StringIO(""),
        "Lineage d__Bacteria;p__Proteobacteria;c__Gammaproteobacteria;o__Enterobacterales;"
        + "f__Enterobacteriaceae;g__Escherichia;x__Escherichia coli does not end with species"
    )
    lin = StringIO("\n".join([
        "RS_GCF_000566285.1	d__Bacteria;p__Proteobacteria;c__Gammaproteobacteria;"
        + "o__Enterobacterales;f__Enterobacteriaceae;g__Escherichia;j__Escherichia coli",
        "RS_GCF_003460375.1	d__Bacteria;p__Proteobacteria;c__Gammaproteobacteria;"
        + "o__Enterobacterales;f__Enterobacteriaceae;g__Escherichia;s__Escherichia coli"
    ]))
    _node_provider_fail(
        StringIO(""),
        lin,
        "Lineage d__Bacteria;p__Proteobacteria;c__Gammaproteobacteria;o__Enterobacterales;"
        + "f__Enterobacteriaceae;g__Escherichia;j__Escherichia coli does not end with species"
    )


def _node_provider_fail(bac, arc, expected):
    with raises(Exception) as got:
        list(GTDBNodeProvider(bac, arc))
    assert_exception_correct(got.value, ValueError(expected))


def test_edge_provider():
    bacnames = StringIO("\n".join([
        "RS_GCF_000566285.1	d__Bacteria;p__Proteobacteria;c__Gammaproteobacteria;"
        + "o__Enterobacterales;f__Enterobacteriaceae;g__Escherichia;s__Escherichia coli",
        "RS_GCF_003460375.1	d__Bacteria;p__Proteobacteria;c__Gammaproteobacteria;"
        + "o__Enterobacterales;f__Enterobacteriaceae;g__Escherichia;s__Escherichia coli"
    ]))
    arcnames = StringIO("\n".join([
        "RS_GCF_000979375.1	d__Archaea;p__Halobacteriota;c__Methanosarcinia;o__Methanosarcinales;"
        + "f__Methanosarcinaceae;g__Methanosarcina;s__Methanosarcina mazei",
        "RS_GCF_000970165.1	d__Archaea;p__Halobacteriota;c__Methanosarcinia;o__Methanosarcinales;"
        + "f__Methanosarcinaceae;g__Methanosarcina;s__Methanosarcina mazei"
    ]))

    res = list(GTDBEdgeProvider(bacnames, arcnames))

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
        {
            'from': 'p:Halobacteriota',
            'id': 'p:Halobacteriota',
            'to': 'd:Archaea'
        },
        {
            'from': 'c:Methanosarcinia',
            'id': 'c:Methanosarcinia',
            'to': 'p:Halobacteriota'
        },
        {
            'from': 'o:Methanosarcinales',
            'id': 'o:Methanosarcinales',
            'to': 'c:Methanosarcinia'
        },
        {
            'from': 'f:Methanosarcinaceae',
            'id': 'f:Methanosarcinaceae',
            'to': 'o:Methanosarcinales'
        },
        {
            'from': 'g:Methanosarcina',
            'id': 'g:Methanosarcina',
            'to': 'f:Methanosarcinaceae'
        },
        {
            'from': 's:Methanosarcina_mazei',
            'id': 's:Methanosarcina_mazei',
            'to': 'g:Methanosarcina'
        },
        {
            'from': 'RS_GCF_000979375.1',
            'id': 'RS_GCF_000979375.1',
            'to': 's:Methanosarcina_mazei'
        },
        {
            'from': 'RS_GCF_000970165.1',
            'id': 'RS_GCF_000970165.1',
            'to': 's:Methanosarcina_mazei'
        },
    ]


def test_edge_provider_fail():
    lin = StringIO("\n".join([
        "RS_GCF_000566285.1	d__Bacteria;p__Proteobacteria;c__Gammaproteobacteria;"
        + "o__Enterobacterales;f__Enterobacteriaceae;g__Escherichia;s__Escherichia coli",
        "RS_GCF_003460375.1	d__Bacteria;p__Proteobacteria;c__Gammaproteobacteria;"
        + "o__Enterobacterales;f__Enterobacteriaceae;g__Escherichia;y__Escherichia coli"
    ]))
    _edge_provider_fail(
        lin,
        StringIO(""),
        "Lineage d__Bacteria;p__Proteobacteria;c__Gammaproteobacteria;o__Enterobacterales;"
        + "f__Enterobacteriaceae;g__Escherichia;y__Escherichia coli does not end with species"
    )
    lin = StringIO("\n".join([
        "RS_GCF_000566285.1	d__Bacteria;p__Proteobacteria;c__Gammaproteobacteria;"
        + "o__Enterobacterales;f__Enterobacteriaceae;g__Escherichia;l__Escherichia coli",
        "RS_GCF_003460375.1	d__Bacteria;p__Proteobacteria;c__Gammaproteobacteria;"
        + "o__Enterobacterales;f__Enterobacteriaceae;g__Escherichia;s__Escherichia coli"
    ]))
    _edge_provider_fail(
        StringIO(""),
        lin,
        "Lineage d__Bacteria;p__Proteobacteria;c__Gammaproteobacteria;o__Enterobacterales;"
        + "f__Enterobacteriaceae;g__Escherichia;l__Escherichia coli does not end with species"
    )


def _edge_provider_fail(bac, arc, expected):
    with raises(Exception) as got:
        list(GTDBEdgeProvider(bac, arc))
    assert_exception_correct(got.value, ValueError(expected))
