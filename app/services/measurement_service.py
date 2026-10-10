import geopandas as gpd
from shapely.geometry.base import BaseGeometry
import logging

logger = logging.getLogger(__name__)

def calculate_measurements(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """
    Takes a GeoDataFrame, decides on a suitable CRS for measurement if geographic,
    reprojects it, and calculates area and length based on geometry type.
    """
    if gdf.empty:
        gdf["measurement_value"] = None
        gdf["measurement_unit"] = None
        gdf["measurement_crs"] = None
        return gdf
        
    measurement_crs = gdf.crs

    if gdf.crs and gdf.crs.is_geographic:
        # Check extent to ensure UTM is appropriate (UTM zones are 6 degrees wide)
        bounds = gdf.total_bounds
        lon_width = abs(bounds[2] - bounds[0])
        
        try:
            if lon_width > 12: # Spans more than 2 UTM zones (rough safety check)
                logger.warning(f"Dataset spans {lon_width} degrees. UTM might be inaccurate. Falling back to an Equal Area projection for measurements.")
                # We can use Pseudo-Mercator (3857) or World Cylindrical Equal Area (6933)
                measurement_crs = "EPSG:6933" # Equal-Area Cylindrical (good for Area over large spans)
            else:
                measurement_crs = gdf.estimate_utm_crs()
                logger.info(f"Geographic CRS. Estimated UTM CRS: {measurement_crs}")
                
            projected_gdf = gdf.to_crs(measurement_crs)
        except Exception as e:
            logger.error(f"Failed to project geographic coordinates: {e}")
            # Fallback to World Cylindrical Equal Area just in case
            try:
                measurement_crs = "EPSG:6933"
                projected_gdf = gdf.to_crs(measurement_crs)
            except Exception as inner_e:
                logger.warning("Could not project geometry safely. Measurements might not be possible.")
                projected_gdf = gdf
    else:
        # Already projected or no CRS. Assume local units (usually meters).
        projected_gdf = gdf
        
    measurement_values = []
    measurement_units = []
    
    for idx, row in projected_gdf.iterrows():
        geom: BaseGeometry = row.geometry
        if geom is None or geom.is_empty:
            measurement_values.append(None)
            measurement_units.append(None)
            continue
            
        geom_type = geom.geom_type
        
        if geom_type in ['Polygon', 'MultiPolygon']:
            # Area in square units (usually sq meters if projected correctly)
            val = geom.area
            unit = "sq. meters"
        elif geom_type in ['LineString', 'MultiLineString']:
            # Length in linear units (usually meters)
            val = geom.length
            unit = "meters"
        elif geom_type in ['Point', 'MultiPoint']:
            val = None
            unit = None
        else:
            logger.warning(f"Unsupported geometry type for measurement: {geom_type}")
            val = None
            unit = None
            
        measurement_values.append(val)
        measurement_units.append(unit)
        
    # Assign back to original GDF
    # We maintain the original geometries in the return DF, but attach the measurement metadata
    gdf["measurement_value"] = measurement_values
    gdf["measurement_unit"] = measurement_units
    gdf["measurement_crs"] = str(measurement_crs) if measurement_crs else None
    
    return gdf
