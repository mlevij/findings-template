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
        # Rendered as separate <p> elements by the page, not one flat block of text --
        # keep each list entry to one self-contained paragraph.
        "summary": [
            "These 60 candidate sites (5 per watershed, per method) come from two "
            "different, competing computer-driven selection methods shown together on "
            "one map \u2014 not a single ranked list, and not a human picking favorites. "
            "Both methods only ever consider spots within a half-mile of a real road or "
            "off-road track, so nothing shown here requires a serious backcountry trek "
            "to reach. From there, the two methods disagree on purpose:",

            "K-means groups every possible spot into clusters of similar terrain, "
            "soil, and vegetation, then picks the single most \u2018typical\u2019 example from "
            "each cluster \u2014 its 5 picks per watershed represent the common, everyday "
            "conditions you'd actually encounter out there.",

            "cLHS (conditioned Latin Hypercube Sampling) does the opposite on "
            "purpose: it deliberately spreads its 5 picks across the full range of "
            "conditions present, including rare or unusual combinations a \u2018typical\u2019 "
            "pick would skip right past \u2014 a specific soil pocket, an odd elevation "
            "band, etc.",

            "Where the two methods happen to agree on a similar spot is a stronger "
            "signal that location is a solid choice; where they diverge just gives the "
            "team more options to weigh. See Methodology below for the technical "
            "detail \u2014 formulas, data sources, and exactly how each method works under "
            "the hood.",
        ],
        # Same rendering convention as summary above -- one paragraph per entry.
        "methodology": [
            "STEP 1 \u2014 BUILDING THE CANDIDATE POOL. A candidate \u2018site\u2019 was generated "
            "at every cell of a ~30m-resolution digital elevation model (DEM, a grid of "
            "ground-elevation values) across BLM-managed land within the 6 target HUC10 "
            "watersheds \u2014 roughly 1.25 million points. Each point was then checked "
            "against an accessibility corridor: a half-mile buffer around every road or "
            "off-road track in the county, built from a statewide CDOT (Colorado "
            "Department of Transportation) road inventory plus OpenStreetMap's "
            "crowd-sourced track data (added because the official CDOT roads alone "
            "turned out to miss the majority of informal BLM routes actually usable by "
            "a capable 4x4). Any point outside that half-mile corridor was dropped "
            "before either selection method ever saw it \u2014 accessibility is a hard "
            "requirement to even be considered, not a factor either method weighs "
            "against the others. Points missing data for any covariate below (common "
            "near the edges of the covered area) were also dropped. Roughly 846,000 "
            "candidate points survived both filters.",

            "STEP 2 \u2014 PREPARING THE COMPARISON. Each surviving point carries a mix of "
            "measurements on very different scales \u2014 elevation in meters, slope in "
            "degrees, distance in meters \u2014 which would make comparisons unfair if used "
            "as-is (a 1000m difference in elevation would swamp a 30-degree difference "
            "in slope in any distance calculation). To fix this, the continuous "
            "measurements (elevation, slope, aspect, and distance to the nearest CBRFC "
            "stream-gage/forecast point, a proxy for real-time streamflow data) were "
            "each converted to a z-score \u2014 how many standard deviations above or below "
            "the average that value is \u2014 putting everything on one common, comparable "
            "scale. Distance-to-gage was then deliberately down-weighted to half "
            "strength relative to the others, since the project team asked for it to "
            "matter less than terrain/soil/vegetation similarity. The category-type "
            "measurements (NLCD land cover class, CDL crop class, MLRA ecoregion, and "
            "NRCS Ecological Site \u2014 a rangeland classification based on soil, climate, "
            "and vegetation potential) can't be z-scored the same way, since they're "
            "labels, not numbers. Instead they were one-hot encoded \u2014 turned into a set "
            "of yes/no columns, one per possible category, each marked 1 if a point has "
            "that category and 0 otherwise, which is the standard way to feed "
            "non-numeric categories into a distance-based algorithm like either method "
            "below.",

            "STEP 3 \u2014 K-MEANS (favors typical/representative sites). K-means is a "
            "widely used clustering algorithm: give it a set of points and a target "
            "number of groups k, and it splits the points into k clusters such that "
            "each point is closer to its own cluster's center than to any other "
            "cluster's center \u2014 formally, it minimizes the total squared distance from "
            "every point to its assigned cluster center. Run here via SciPy (a widely "
            "used, well-tested Python library for scientific/numerical computing) with "
            "k=5 per watershed. A cluster's mathematical center is rarely a real, "
            "visitable location, so for each of the 5 clusters the actual real "
            "candidate point closest to that center was selected as the site \u2014 never a "
            "synthetic average location.",

            "STEP 4 \u2014 cLHS (favors spanning the full range of conditions). Conditioned "
            "Latin Hypercube Sampling (Minasny & McBratney, 2006) starts from a "
            "different goal: instead of finding typical examples, ensure the sample "
            "spans the entire range of each covariate roughly evenly. Each covariate's "
            "values are first split into 5 equal-sized bins (a Latin Hypercube \u2014 the "
            "same idea as making sure a sample includes some low, medium, and high "
            "values of every measurement, not just the middle of the pack). The "
            "algorithm then searches for the 5-point sample that comes closest to "
            "landing exactly one point in every bin of every covariate at once, using "
            "simulated annealing \u2014 an optimization technique (named for how molten "
            "metal is cooled slowly to reach a stable structure) that starts by freely "
            "swapping points in and out even when a swap looks worse in the short term, "
            "then gradually gets stricter about only accepting improvements as it runs, "
            "so it doesn't get stuck on the first mediocre answer it finds. This is a "
            "simplified, hand-written implementation (no ready-made tool for this "
            "exists) that intentionally omits the original published method's "
            "correlation-preservation term, a refinement that keeps naturally-related "
            "covariates (like elevation and temperature) from being sampled as if they "
            "were independent \u2014 worth a sanity check against the full candidate "
            "population's distributions before treating these picks as final.",

            "WHAT WASN'T USED TO PICK SITES. Elevation, slope, aspect, land cover, MLRA, "
            "Ecological Site, and distance-to-gage were the only inputs either method "
            "used to choose sites. Everything else shown per site \u2014 distance to town/"
            "road/recreation-area/forest-boundary, and the full SSURGO soil chemistry "
            "panel (pH, organic matter, texture, CEC, etc.) \u2014 was attached afterward, "
            "purely for the team's reference, and had zero influence on which sites "
            "were chosen. The soil chemistry values in particular are SSURGO map-unit "
            "estimates, not lab measurements \u2014 the project plans to re-measure these "
            "properties directly at each installed site, so treat these as a preview, "
            "not a substitute.",
        ],
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
