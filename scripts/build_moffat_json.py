"""
Transform Candidate_Sites_Final (exported to WGS84 GeoJSON via ogr2ogr) into
findings-template's data contract: data/moffat-siting.json.

Source GeoJSON is produced from the live gdb, e.g.:
  ogr2ogr -f GeoJSON -t_srs EPSG:4326 candidate_sites_final_wgs84.geojson \
    "Siting Tool.gdb" "Candidate_Sites_Final"
"""
import json
import sys

SRC = sys.argv[1] if len(sys.argv) > 1 else (
    r"C:\Users\mlevij\AppData\Local\Temp\claude\C--Program-Files-Git"
    r"\7d311543-8142-446b-9513-d9db25fe7dd6\scratchpad"
    r"\candidate_sites_final_wgs84.geojson"
)
OUT = r"C:\Users\mlevij\repos\findings-template\data\moffat-siting.json"

# Standard NLCD 2019 / USDA CDL legend codes present in this dataset.
NLCD_LABELS = {
    41: "Deciduous Forest",
    42: "Evergreen Forest",
    43: "Mixed Forest",
    52: "Shrub/Scrub",
    71: "Grassland/Herbaceous",
}
CDL_LABELS = {
    36: "Alfalfa",
    141: "Deciduous Forest",
    142: "Evergreen Forest",
    152: "Shrubland",
    176: "Grassland/Pasture",
}


def method_label(method_key, n):
    return f"{'K-Means' if method_key == 'kmeans' else 'cLHS'} site {n}"


def build():
    with open(SRC, encoding="utf-8") as f:
        src = json.load(f)

    project = {
        "title": "Moffat County Weather / Soil Moisture Station Siting",
        "subtitle": "Candidate installation sites on BLM land across 6 Yampa-basin HUC10 watersheds",
        "summary": (
            "These 60 sites come from two independent, competing selection methods shown "
            "together \u2014 k-means and cLHS \u2014 not a single ranked list. Where the two "
            "agree is a stronger signal; where they diverge gives fallback options. See "
            "Methodology below for the full covariate stack and how each method works."
        ),
        "methodology": (
            "Candidate points were generated at every DEM cell (~30m) across BLM land "
            "within the 6 target HUC10 watersheds, then reduced to those with complete "
            "covariate data. Continuous covariates (elevation, slope, aspect, distance to "
            "nearest CBRFC gage/forecast point) were z-scored; categorical covariates (NLCD "
            "land cover class, CDL crop class, MLRA region, NRCS Ecological Site) were "
            "one-hot encoded. Distance-to-gage was weighted at half strength relative to the "
            "other covariates. Two independent site-selection methods were then run per "
            "watershed, 5 sites each: k-means clustering (scipy), which favors sites "
            "representing common/typical conditions, and a simplified conditioned Latin "
            "Hypercube Sample, which favors sites spanning the full range of conditions "
            "including rarer ones. Elevation, slope, aspect, land cover, and MLRA were "
            "direct clustering inputs. Distance to town/road/recreation-area/forest-boundary "
            "and full SSURGO soil chemistry were attached to the final sites afterward for "
            "documentation only \u2014 they did not influence which sites were selected. "
            "Distance-to-road uses a statewide CDOT road inventory (with real functional/"
            "admin classification), not a Forest Service travel-management layer that has "
            "no coverage on BLM land \u2014 accessibility context here is not yet weighted by "
            "road class, that's a planned refinement."
        ),
    }

    categories = [
        {"key": "kmeans", "label": "K-Means", "colorSlot": 1},
        {"key": "clhs", "label": "cLHS", "colorSlot": 2},
    ]

    attribute_groups = [
        {
            "label": "Location",
            "fields": [
                {"key": "watershed", "label": "HUC10 Watershed"},
                {"key": "mlra_name", "label": "MLRA / Ecoregion"},
            ],
        },
        {
            "label": "Terrain",
            "fields": [
                {"key": "elevation_m", "label": "Elevation", "unit": "m"},
                {"key": "slope_deg", "label": "Slope", "unit": "\u00b0"},
                {"key": "aspect_deg", "label": "Aspect", "unit": "\u00b0"},
            ],
        },
        {
            "label": "Land Cover",
            "fields": [
                {"key": "nlcd_class", "label": "NLCD Land Cover"},
                {"key": "cdl_class", "label": "CDL Crop/Cover Class"},
            ],
        },
        {
            "label": "Soil",
            "fields": [
                {"key": "soil_map_unit", "label": "Soil Map Unit"},
                {"key": "ecological_site", "label": "Ecological Site"},
                {"key": "soil_taxonomy", "label": "Taxonomic Class"},
                {"key": "parent_material", "label": "Parent Material"},
                {"key": "temp_regime", "label": "Soil Temp. Regime"},
                {"key": "moisture_regime", "label": "Soil Moisture Regime"},
            ],
        },
        {
            "label": "Soil Chemistry (0-6 in, SSURGO estimate)",
            "fields": [
                {"key": "ph", "label": "pH"},
                {"key": "organic_matter_pct", "label": "Organic Matter", "unit": "%"},
                {"key": "cec", "label": "CEC", "unit": "meq/100g"},
                {"key": "sand_pct", "label": "Sand", "unit": "%"},
                {"key": "silt_pct", "label": "Silt", "unit": "%"},
                {"key": "clay_pct", "label": "Clay", "unit": "%"},
            ],
        },
        {
            "label": "Context (documentation only \u2014 not a clustering input)",
            "fields": [
                {"key": "dist_to_town_km", "label": "Distance to Town", "unit": "km"},
                {"key": "dist_to_road_km", "label": "Distance to Road", "unit": "km"},
                {
                    "key": "dist_to_forest_boundary_km",
                    "label": "Distance to Forest Boundary",
                    "unit": "km",
                },
            ],
        },
    ]

    per_watershed_counter = {}
    points = []
    for feat in src["features"]:
        p = feat["properties"]
        lon, lat = feat["geometry"]["coordinates"]
        method = p["method"]
        watershed = p["huc10_name"]
        key = (method, watershed)
        per_watershed_counter[key] = per_watershed_counter.get(key, 0) + 1
        n = per_watershed_counter[key]

        nlcd = p.get("nlcd_class")
        cdl = p.get("cdl_class")

        attrs = {
            "watershed": watershed,
            "mlra_name": p.get("mlra_name"),
            "elevation_m": round(p["elevation_m"], 1) if p.get("elevation_m") is not None else None,
            "slope_deg": round(p["slope_deg"], 1) if p.get("slope_deg") is not None else None,
            "aspect_deg": round(p["aspect_deg"], 1) if p.get("aspect_deg") is not None else None,
            "nlcd_class": NLCD_LABELS.get(int(nlcd)) if nlcd is not None else None,
            "cdl_class": CDL_LABELS.get(int(cdl)) if cdl is not None else None,
            "soil_map_unit": p.get("muname"),
            "ecological_site": p.get("EcoSiteNm_DCP"),
            "ecosite_id": p.get("EcoSiteID_DCP"),
            "soil_taxonomy": p.get("TaxClName_DCP"),
            "parent_material": p.get("ParMatNm_DCP"),
            "ph": p.get("pHwater_DCP_0_6_in"),
            "organic_matter_pct": p.get("OrgMatter_DCP_0_6_in"),
            "sand_pct": p.get("Sand_DCP_0_6_in"),
            "silt_pct": p.get("Silt_DCP_0_6_in"),
            "clay_pct": p.get("Clay_DCP_0_6_in"),
            "cec": p.get("CEC7_DCP_0_6_in"),
            "temp_regime": p.get("TempRegime_DCP"),
            "moisture_regime": p.get("MoistRegim_DCP"),
            "dist_to_town_km": round(p["dist_town"] / 1000, 1) if p.get("dist_town") is not None else None,
            "dist_to_road_km": round(p["dist_road"] / 1000, 1) if p.get("dist_road") is not None else None,
            "dist_to_forest_boundary_km": round(p["dist_forestbound"] / 1000, 1)
            if p.get("dist_forestbound") is not None
            else None,
        }

        watershed_id = watershed.replace(" ", "_").replace(",", "")
        points.append(
            {
                "id": f"{method}-{watershed_id}-{n}",
                "lat": lat,
                "lon": lon,
                "category": method,
                "group": watershed,
                "name": f"{method_label(method, n)} \u2014 {watershed}",
                "attributes": attrs,
            }
        )

    out = {
        "project": project,
        "categoryField": "method",
        "categories": categories,
        "groupField": "watershed",
        "attributeGroups": attribute_groups,
        "points": points,
    }

    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=1, ensure_ascii=False)

    print(f"Wrote {len(points)} points to {OUT}")


if __name__ == "__main__":
    build()
