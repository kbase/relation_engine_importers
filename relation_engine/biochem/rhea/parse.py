import pandas as pd



CHEBI_ID_FP = "data/rhea/tsv/chebiId_name.tsv"
RHEA_REACTIONS_FP = "data/rhea/tsv/rhea-directions.tsv"


########################################################################################################################
########################################################################################################################
def gen_chebi_terms(fp=CHEBI_ID_FP):
    df = pd.read_csv(fp, sep="\t", header=None)
    df.columns = ["id", "name"]

    for row in df.iterrows():
        _, rowdat = row[0], row[1]

        yield {
            "id": rowdat["id"],
            "name": rowdat["name"],
        }


########################################################################################################################
########################################################################################################################
def gen_rhea_reactions(fp=RHEA_REACTIONS_FP):
    df = pd.read_csv(fp, sep="\t")

    UN, LR, RL, BI = df.columns.tolist()
    directions = ["UN","LR", "RL", "BI"]

    for row in df.iterrows():
        _, rowdat = row[0], row[1]

        for dxn in df.columns.tolist():

            yield {
                "id": str(rowdat[dxn]),
                "is_master": dxn == UN,
                "directions": dict(
                    zip(directions, rowdat.tolist())
                )
            }

