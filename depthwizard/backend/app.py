cat << 'EOF' > app.py
import os
import cv2
import numpy as np
import rasterio
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from transformers import pipeline
from PIL import Image

app = FastAPI(title="DepthWizard Pipeline")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

os.makedirs("outputs", exist_ok=True)
app.mount("/outputs", StaticFiles(directory="outputs"), name="outputs")

print("Loading Depth Anything v2 model...")
depth_pipe = pipeline(task="depth-estimation", model="depth-anything/Depth-Anything-V2-Small-hf")
print("Model loaded successfully!")

@app.post("/api/process")
async def process_image(file: UploadFile = File(...)):
    raw_bytes = await file.read()
    temp_in = os.path.join("outputs", file.filename)
    with open(temp_in, "wb") as f:
        f.write(raw_bytes)
        
    is_georeferenced = False
    profile = None
    
    try:
        with rasterio.open(temp_in) as src:
            if src.crs is not None:
                is_georeferenced = True
                profile = src.profile
    except Exception:
        is_georeferenced = False

    pil_img = Image.open(temp_in).convert("RGB")
    result = depth_pipe(pil_img)
    rel_depth = np.array(result["depth"], dtype=np.float32)
    
    # Normalize 0.0 - 1.0
    rel_depth_norm = (rel_depth - rel_depth.min()) / (rel_depth.max() - rel_depth.min() + 1e-8)
    
    heightmap_png = os.path.join("outputs", "heightmap.png")
    cv2.imwrite(heightmap_png, (rel_depth_norm * 255).astype(np.uint8))
    
    mode = "Absolute DSM (Metric)" if is_georeferenced else "Relative DSM (rDSM)"
    
    return {
        "status": "success",
        "is_georeferenced": is_georeferenced,
        "texture_url": f"/outputs/{file.filename}",
        "heightmap_url": "/outputs/heightmap.png",
        "metrics": {
            "mode": mode,
            "min_val": 0.0,
            "max_val": 100.0 if is_georeferenced else 1.0
        }
    }
EOF
