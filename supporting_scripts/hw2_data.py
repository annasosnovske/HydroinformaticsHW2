import datetime
import os

import geopandas as gpd
import numpy as np

from supporting_scripts import dataprocessing
from supporting_scripts import getData
from pynhd import NLDI


def fetch_streamflow(usgs_gage_id):
    """Fetch raw NWIS streamflow for a USGS gage id."""
    return getData.get_usgs_streamflow(usgs_gage_id)


def load_basin_and_network(usgs_gage_id, basinname, output_dir="files"):
    """Load basin, gage feature, and upstream flowline network for a USGS site."""
    nldi = NLDI()

    print("Collecting basins...", end="")
    basin = nldi.get_basins(usgs_gage_id)

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    basin.to_file(f"{output_dir}/{basinname}.shp")
    print("done")

    site_feature = nldi.getfeature_byid("nwissite", f"USGS-{usgs_gage_id}")
    upstream_network = nldi.navigate_byid(
        "nwissite", f"USGS-{usgs_gage_id}", "upstreamMain", "flowlines", distance=9999
    )

    return basin, site_feature, upstream_network


def prepare_streamflow_dataframe(streamflow):
    """Clean NWIS streamflow and convert cfs to cms."""
    cleaned = dataprocessing.clean_nwis_dataframe(streamflow)
    cleaned.index.name = "Date"
    cleaned["flow_cfs"] = cleaned["flow_cfs"] * 0.0283168
    cleaned.rename(columns={"flow_cfs": "flow_cms"}, inplace=True)
    return cleaned


def load_requested_snotel_data(requested_sites):
    """Load SNOTEL/SWE data for requested site codes."""
    return getData.load_snotel_data(requested_sites)


def load_station_metadata(target_codes):
    """Load station metadata GeoDataFrames for target SNOTEL codes."""
    all_stations_gdf = gpd.read_file(
        "https://raw.githubusercontent.com/egagli/snotel_ccss_stations/main/all_stations.geojson"
    ).set_index("code")
    all_stations_gdf = all_stations_gdf[all_stations_gdf["csvData"] == True]

    gdf_in_bbox = all_stations_gdf[
        all_stations_gdf.index.astype(str).isin(target_codes)
    ].copy()

    gdf_in_bbox.reset_index(drop=False, inplace=True)

    gdf_in_bbox["beginDate"] = [
        datetime.datetime.strftime(gdf_in_bbox["beginDate"][i], "%Y-%m-%d")
        for i in np.arange(0, len(gdf_in_bbox), 1)
    ]
    gdf_in_bbox["endDate"] = [
        datetime.datetime.strftime(gdf_in_bbox["endDate"][i], "%Y-%m-%d")
        for i in np.arange(0, len(gdf_in_bbox), 1)
    ]

    return all_stations_gdf, gdf_in_bbox
