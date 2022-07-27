"""
Called from download_kegg.sh
download_kegg.sh will download the names of the desired databases
But you can only GET the records for the names 10 at a time without a subscription
Here download the records 10 at a time
"""
import os
import pandas as pd
import requests
import sys
import time

MAX_GET = 10
UPDATE_INTERVAL = 200
GET_URL = "http://rest.kegg.jp/get/"


def download_kegg(fp, out_dir):
    """
    Given a TSV file path with the first column being a list of KEGG names, e.g.
        cpd:C00001
        cpd:C00002
        cpd:C00003
        ...
        cpd:C22503
    Download the full records 10 at a time (all that is allowed without paid subscription)
    """
    fn = os.path.basename(fp)
    fn_extless = os.path.splitext(fn)[0]
    fp_out = os.path.join(out_dir, fn_extless + "_full" + ".txt")

    print("\n\nDownloading records from %s names, %d at a time ...\n" % (fp, MAX_GET))

    df = pd.read_csv(fp, sep="\t", header=None)
    names = df[0].tolist()  # first column is names

    t0 = time.time()

    with open(fp_out, "w") as fh_out:
        for i in range(0, len(names), MAX_GET):  # can only GET 10 at a time

            # print some update info
            if i % (UPDATE_INTERVAL * MAX_GET):  # every N GETS
                if i:
                    print("%ds/record ... " % int((t0 - time.time()) / i), end="")
                print("%d/%d, " % (i, len(names)), end="")

            get_names = "+".join(names[i : i + MAX_GET])  # concat <=10 names
            url = os.path.join(GET_URL, get_names)
            txt = requests.get(url).text
            fh_out.write(txt)

    print("\n\nFinished %s" % fp)
    print("Wrote to %s" % fp_out)


if __name__ == "__main__":
    """
    Arg1: Output dir
    Arg2+: KEGG name file paths
    """
    out_dir = sys.argv[1]
    for fp in sys.argv[2:]:
        download_kegg(fp, out_dir)
