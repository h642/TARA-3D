import numpy as np
import rasterio

def evaluate_accuracy(pred_tif_path: str, ref_tif_path: str):
    """Computes RMSE, MAE, and Pearson Correlation against ground truth."""
    with rasterio.open(pred_tif_path) as p_src, rasterio.open(ref_tif_path) as r_src:
        pred = p_src.read(1)
        ref = r_src.read(1)
        
    mask = ~np.isnan(pred) & ~np.isnan(ref) & (ref > -500)
    p_valid = pred[mask]
    r_valid = ref[mask]
    
    # 1. Root Mean Square Error
    rmse = np.sqrt(np.mean((p_valid - r_valid) ** 2))
    # 2. Mean Absolute Error
    mae = np.mean(np.abs(p_valid - r_valid))
    # 3. Pearson Correlation (r)
    r_corr = np.corrcoef(p_valid, r_valid)[0, 1]
    
    return {
        "RMSE_meters": float(rmse),
        "MAE_meters": float(mae),
        "Pearson_r": float(r_corr),
        "Evaluated_Pixels": int(np.sum(mask))
    }
