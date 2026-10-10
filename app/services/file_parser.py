import os
import zipfile
import geopandas as gpd
import fiona
import json
import logging
from pathlib import Path

# Enable KML driver support in Fiona
fiona.drvsupport.supported_drivers['KML'] = 'rw'
fiona.drvsupport.supported_drivers['LIBKML'] = 'rw'

logger = logging.getLogger(__name__)

class FileParserError(Exception):
    pass

def validate_and_find_shapefile_in_zip(zip_path: str) -> str:
    """
    Validates safely that the ZIP contains .shp, .shx, and .dbf.
    Returns the internal path to the primary .shp file.
    """
    try:
        with zipfile.ZipFile(zip_path, 'r') as zf:
            namelist = zf.namelist()
            
            # Check for path traversal inside the zip
            for name in namelist:
                if '..' in name or name.startswith('/'):
                    raise FileParserError("Unsafe file paths detected in ZIP archive.")
                    
            shp_files = [f for f in namelist if f.lower().endswith('.shp')]
            if not shp_files:
                raise FileParserError("No .shp file found in the ZIP archive.")
                
            main_shp = shp_files[0] # Pick the first one
            base_name = os.path.splitext(main_shp)[0]
            
            # Ensure companion files exist
            shx_exists = any(f.lower() == f"{base_name.lower()}.shx" for f in namelist)
            dbf_exists = any(f.lower() == f"{base_name.lower()}.dbf" for f in namelist)
            
            if not shx_exists or not dbf_exists:
                raise FileParserError("Missing required Shapefile companions (.shx, .dbf) in ZIP.")
            
            # Note: We safely ignore missing .prj (Coordinate Reference System), it will just result in None CRS
            return main_shp
            
    except zipfile.BadZipFile:
        raise FileParserError("Uploaded file is not a valid ZIP archive.")

def parse_geospatial_file(file_path: str, filename: str) -> gpd.GeoDataFrame:
    """
    Takes a path to a downloaded temporal file, decides on the driver,
    and returns a parsed GeoDataFrame.
    """
    lower_filename = filename.lower()
    
    try:
        if lower_filename.endswith('.zip'):
            shp_internal_path = validate_and_find_shapefile_in_zip(file_path)
            # GeoPandas can read directly from a ZIP using VFS
            vfs_path = f"zip://{file_path}!/{shp_internal_path}"
            gdf = gpd.read_file(vfs_path)
            return gdf
            
        elif lower_filename.endswith('.kml'):
            # Directly read KML
            gdf = gpd.read_file(file_path, driver='KML')
            return gdf
            
        else:
            raise FileParserError("Unsupported file extension. Please upload a .zip (Shapefile) or .kml file.")
            
    except FileParserError:
        raise
    except Exception as e:
        logger.error(f"Error parsing file {filename}: {str(e)}")
        raise FileParserError(f"Failed to parse geospatial data: {str(e)}")
