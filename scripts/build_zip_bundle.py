"""
Bundle the user-facing export files in data/ into data/moffat-siting-all.zip --
run this as the LAST step whenever any of the individual export files change,
so the bundle stays in sync with them.

Only includes files meant for people to download and use elsewhere (CSV +
KMZ). Explicitly excludes moffat-siting.json (the page's own internal data
contract -- methodology text, UI config -- not a portable layer) and the raw
.geojson files (only the page's own Leaflet map needs those; the matching
.kmz versions are the user-friendly export of the same layers).
"""
import os
import zipfile

DATA_DIR = r"C:\Users\mlevij\repos\findings-template\data"
OUT_ZIP = os.path.join(DATA_DIR, "moffat-siting-all.zip")
INCLUDE = {
    "moffat-siting.csv",
    "moffat-siting.kmz",
    "moffat-huc10.kmz",
    "moffat-roads.kmz",
    "moffat-county.kmz",
}


def build():
    files = [f for f in INCLUDE if os.path.isfile(os.path.join(DATA_DIR, f))]
    missing = INCLUDE - set(files)
    if missing:
        print(f"WARNING: expected but not found, skipping: {sorted(missing)}")
    with zipfile.ZipFile(OUT_ZIP, "w", zipfile.ZIP_DEFLATED) as z:
        for f in files:
            z.write(os.path.join(DATA_DIR, f), arcname=f)
    print(f"Bundled {len(files)} files into {OUT_ZIP}:")
    for f in sorted(files):
        print(f"  {f}")


if __name__ == "__main__":
    build()
