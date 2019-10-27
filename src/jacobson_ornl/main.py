"""
This is a quick & temporary script for loading the Dan Jacobson/ORNL group's gene and phenotype network data into arangodb.

Running this requires a set of source files provided by the ORNL group.
"""
import json
import requests
import os

_VERT_PATH = 'aranet2-aragwas-MERGED-AMW-v2_091319_nodeTable.csv'
_DB_NAME = 'prod'
_ADB_URL = 'http://localhost:8530'
_PHENO_VERT_NAME = 'djornl_phenotype'
_GENE_VERT_NAME = 'djornl_gene'

# Gene to phenotype associations
_PHENO_ASSN_PATH = 'aragwas_subnet_phenoassociations_AMW_083019.tsv'
_EDGE_PHENO_ASSN = 'djornl_pheno_assn'

# Gene to gene domain co-occurence with least likelihood score
_DOMAIN_CO_OCCUR_PATH = 'aranetv2_subnet_AT-DC_anno_AF_082919.tsv'
_EDGE_DOMAIN_CO_OCCUR = 'djornl_domain_co_occur'

# Gene to gene coexpression
_GENE_COEXPR_PATH = 'aranetv2_subnet_AT-CX_top10percent_anno_AF_082919.tsv'
_EDGE_GENE_COEXPR = 'djornl_gene_coexpr'

# Gene to gene high throughput protein-protein interaction
_PPI_HITHRU_PATH = 'aranetv2_subnet_AT-HT_anno_AF_082919.tsv'
_EDGE_PPI_HITHRU = 'djornl_ppi_hithru'

# Gene to gene literature curated protein-protein interaction
_PPI_LIT_PATH = 'aranetv2_subnet_AT-LC_anno_AF_082919.tsv'
_EDGE_PPI_LIT = 'djornl_ppi_liter'


def load_ppi_lit():
    # Headers and sample row:
    # node1	node2	edge	edge_descrip	layer_descrip
    # AT1G01370	AT1G57820	4.40001558779779	AraNetv2_log-likelihood-score	AraNetv2-LC_lit-curated-ppi
    with open(_PPI_LIT_PATH) as fd:
        headers = True
        gene_verts = []
        edges = []
        for line in fd.readlines():
            if headers:
                headers = False
                continue
            cols = [c.strip() for c in line.split('\t')]
            gene_verts.append({'_key': cols[0]})
            gene_verts.append({'_key': cols[1]})
            edges.append({
                '_from': f'{_GENE_VERT_NAME}/{cols[0]}',
                '_to': f'{_GENE_VERT_NAME}/{cols[1]}',
                'lls': float(cols[2]),
            })
    save_docs(_GENE_VERT_NAME, gene_verts, overwrite=False)
    save_docs(_EDGE_PPI_LIT, edges, overwrite=True)


def load_ppi_hithru():
    # Headers and sample row:
    # node1	node2	edge	edge_descrip	layer_descrip
    # AT1G04100	AT5G43700	5.71517296953967	AraNetv2_log-likelihood-score	AraNetv2-HT_high-throughput-ppi
    with open(_PPI_HITHRU_PATH) as fd:
        headers = True
        gene_verts = []
        edges = []
        for line in fd.readlines():
            if headers:
                headers = False
                continue
            cols = [c.strip() for c in line.split('\t')]
            gene_verts.append({'_key': cols[0]})
            gene_verts.append({'_key': cols[1]})
            edges.append({
                '_from': f'{_GENE_VERT_NAME}/{cols[0]}',
                '_to': f'{_GENE_VERT_NAME}/{cols[1]}',
                'lls': float(cols[2]),
            })
    save_docs(_GENE_VERT_NAME, gene_verts, overwrite=False)
    save_docs(_EDGE_PPI_HITHRU, edges, overwrite=True)


def load_gene_coexpr():
    # Headers and sample row
    # node1	node2	edge	edge_descrip	layer_descrip
    # AT3G04840	AT4G31700	5.70119850042396	AraNetv2_log-likelihood-score	AraNetv2-CX_pairwise-gene-coexpression
    with open(_GENE_COEXPR_PATH) as fd:
        headers = True
        gene_verts = []
        edges = []
        for line in fd.readlines():
            if headers:
                headers = False
                continue
            cols = [c.strip() for c in line.split('\t')]
            gene_verts.append({'_key': cols[0]})
            gene_verts.append({'_key': cols[1]})
            edges.append({
                '_from': f'{_GENE_VERT_NAME}/{cols[0]}',
                '_to': f'{_GENE_VERT_NAME}/{cols[1]}',
                'lls': float(cols[2]),
            })
    save_docs(_GENE_VERT_NAME, gene_verts, overwrite=False)
    save_docs(_EDGE_GENE_COEXPR, edges, overwrite=True)


def load_domain_co_occur():
    # Headers and sample row:
    # node1	node2	edge	edge_descrip	layer_descrip
    # ATMG00900	ATMG00960	4.51442597744908	AraNetv2_log-likelihood-score	AraNetv2-DC_domain-co-occurrence
    with open(_DOMAIN_CO_OCCUR_PATH) as fd:
        headers = True
        gene_verts = []
        edges = []
        for line in fd.readlines():
            if headers:
                headers = False
                continue
            cols = [c.strip() for c in line.split('\t')]
            gene_verts.append({'_key': cols[0]})
            gene_verts.append({'_key': cols[1]})
            edges.append({
                '_from': f'{_GENE_VERT_NAME}/{cols[0]}',
                '_to': f'{_GENE_VERT_NAME}/{cols[1]}',
                'lls': float(cols[2]),
            })
    save_docs(_GENE_VERT_NAME, gene_verts, overwrite=False)
    save_docs(_EDGE_DOMAIN_CO_OCCUR, edges, overwrite=True)


def load_pheno_assns():
    # Headers and sample row:
    # node1	node2	edge	edge_descrip	layer_descrip
    # Na23	AT4G10310	41.300822742442726	AraGWAS-Association_score	AraGWAS-Phenotype_Associations
    with open(_PHENO_ASSN_PATH) as fd:
        pheno_verts = []
        gene_verts = []
        edge_verts = []
        headers = True
        for line in fd.readlines():
            if headers:
                headers = False
                continue
            cols = [c.strip() for c in line.split('\t')]
            edge_doc = {
                '_from': f'{_GENE_VERT_NAME}/{cols[1]}',
                '_to': f'{_PHENO_VERT_NAME}/{cols[0]}',
                'assn_score': float(cols[2])
            }
            edge_verts.append(edge_doc)
            pheno_verts.append({'_key': cols[0]})
            gene_verts.append({'_key': cols[1]})
    save_docs(_EDGE_PHENO_ASSN, edge_verts, overwrite=True)
    save_docs(_PHENO_VERT_NAME, pheno_verts, overwrite=False)
    save_docs(_GENE_VERT_NAME, gene_verts, overwrite=False)


def load_vert_metadata():
    with open(_VERT_PATH) as fd:
        headers = True
        genes = []
        phenos = []
        for row in fd.readlines():
            if headers:
                headers = False
                continue
            cols = [c.strip() for c in row.split(',')]
            go_terms = [c.strip() for c in cols[10].split(',')]
            node_type = cols[1]
            doc = {
                '_key': cols[0],
                'node_type': node_type,
                'transcript': cols[2],
                'gene_symbol': cols[3],
                'gene_full_name': cols[4],
                'gene_model_type': cols[5],
                'tair_computational_desc': cols[6],
                'tair_curator_summary': cols[7],
                'tair_short_desc': cols[8],
                'go_descr': cols[9],
                'go_terms': go_terms,
                'mapman_bin': cols[11],
                'mapman_name': cols[12],
                'mapman_desc': cols[13],
                'pheno_aragwas_id': cols[14],
                'pheno_desc1': cols[15],
                'pheno_desc2': cols[16],
                'pheno_desc3': cols[17],
                'pheno_ref': cols[18],
                'user_notes': cols[19],
            }
            if node_type == 'gene':
                genes.append(doc)
            elif node_type == 'pheno':
                phenos.append(doc)
            else:
                raise RuntimeError(f"invalid node type {node_type}")
    save_docs(_PHENO_VERT_NAME, phenos, overwrite=True)
    save_docs(_GENE_VERT_NAME, genes, overwrite=True)


def main():
    load_vert_metadata()
    load_pheno_assns()
    load_domain_co_occur()
    load_gene_coexpr()
    load_ppi_lit()
    load_ppi_hithru()


def save_docs(coll_name, docs, overwrite=False, on_dupe='update'):
    auth = (os.environ['DB_USER'], os.environ['DB_PASS'])
    resp = requests.post(
        _ADB_URL + f'/_db/{_DB_NAME}/_api/import',
        params={'type': 'documents', 'collection': coll_name,
                'overwrite': ('1' if overwrite else '0'), 'onDuplicate': on_dupe},
        auth=auth,
        data='\n'.join(json.dumps(d) for d in docs)
    )
    if not resp.ok:
        raise RuntimeError(resp.text)
    else:
        print(f"Saved docs to collection {coll_name}!")
        print(resp.text)
        print("=" * 80)


if __name__ == '__main__':
    main()
