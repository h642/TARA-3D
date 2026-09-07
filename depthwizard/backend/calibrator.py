import numpy as np
import rasterio
from rasterio.enums import Resampling
from sklearn.linear_model import RANSACRegressor

def calibrate_relative_to_metric(rel_depth: np.ndarray, srtm_dem: np.ndarray):
    """
    Fits scale (s) and shift (t) such that: metric_dsm = s * rel_depth + t
    RANSAC filters out micro-structures (buildings/trees) as outliers, 
    fitting the macro ground elevation.
    """
    # Flatten arrays
    x = rel_depth.reshape(-1, 1)
    y = srtm_dem.reshape(-1, 1)
    
    # Filter out nodata values from coarse DEM
    valid_mask = ~np.isnan(y) & ~np.isinf(y) & (y > -500)
    x_clean = x[valid_mask].reshape(-1, 1)
    y_clean = y[valid_mask].reshape(-1, 1)
    
    # Fit robust linear model
    ransac = RANSACRegressor(random_state=42, residual_threshold=5.0)
    ransac.fit(x_clean, y_clean)
    
    s = float(ransac.estimator_.coef_[0][0])
    t = float(ransac.estimator_.intercept_[0])
    
    metric_dsm = (s * rel_depth + t).astype(np.float32)
    return metric_dsm, s, t

def export_geotiff(output_path: str, data: np.ndarray, profile: dict):
    """Saves single-band float32 GeoTIFF preserving CRS and Affine Transform."""
    profile.update({
        'dtype': 'float32',
        'count': 1,
        'compress': 'lzw'
    })
    with rasterio.open(output_path, 'w', **profile) as dst:
        dst.write(data, 1)
