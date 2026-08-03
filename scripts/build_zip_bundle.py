"""
Bundle every file currently in data/ into data/moffat-siting-all.zip -- run this
as the LAST step whenever any of the individual data files (JSON, CSV, KMZ,
boundary/roads GeoJSON) get regenerated, so the bundle stays in sync with them.
"""
import os
import zipfile

DATA_DIR = r"C:\Users\mlevij\repos\findings-template\data"
OUT_ZIP = os.path.join(DATA_DIR, "moffat-siting-all.zip")
EXCLUDE = {"moffat-siting-all.zip"}


def build():
    files = [f for f in os.listdir(DATA_DIR) if f not in EXCLUDE and os.path.isfile(os.path.join(DATA_DIR, f))]
    with zipfile.ZipFile(OUT_ZIP, "w", zipfile.ZIP_DEFLATED) as z:
        for f in files:
            z.write(os.path.join(DATA_DIR, f), arcname=f)
    print(f"Bundled {len(files)} files into {OUT_ZIP}:")
    for f in sorted(files):
        print(f"  {f}")


if __name__ == "__main__":
    build()
