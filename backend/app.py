import time
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from PIL import Image
import io
import cv2
import numpy as np
import torch
from ultralytics import YOLO


# ---------------------------
# Load Models
# ---------------------------
plate_detector = YOLO("models/LPR_MODEL.pt")     # YOLO model for plate detection
char_detector = YOLO("models/OCR_MODEL.pt")       # YOLO model for character detection

# ---------------------------
# Render Setup
# ---------------------------
plate_detector.to("cpu")
char_detector.to("cpu")

# ---------------------------
# FastAPI
# ---------------------------
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------
# Pydantic Schemas
# ---------------------------
class BoundingBox(BaseModel):
    x_min: int
    y_min: int
    x_max: int
    y_max: int
    confidence: float | None = None
    cls: int | None = None


class PlateOutput(BaseModel):
    plate_number: str
    plate_box: BoundingBox
    plate_confidence: float | None = None
    char_boxes: list[BoundingBox]


class MultiPlateResponse(BaseModel):
    status: str
    total_plates: int
    plates: list[PlateOutput]
    time_taken_ms: float


# ---------------------------
# Utility: Sort character boxes by X
# ---------------------------
def sort_characters(char_boxes):
    return sorted(char_boxes, key=lambda b: b["x_min"])


# ---------------------------
# MAIN ENDPOINT
# ---------------------------
@app.get("/")
def health():
    return {
        "status": "ok",
        "service": "LPR Backend",
        "model_loaded": True
    }

@app.post("/recognize", response_model=MultiPlateResponse)
async def recognize(file: UploadFile = File(...)):
    start_time = time.time()

    # 1. Validate image type
    if not file.filename.lower().endswith((".jpg", ".jpeg", ".png")):
        raise HTTPException(status_code=400, detail="Invalid image format")

    # 2. Read → PIL → CV2
    img_bytes = await file.read()
    pil_img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
    img_cv2 = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)

    # 3. Detect plates
    plate_results = plate_detector(img_cv2, conf=0.4, verbose=False)
    boxes = plate_results[0].boxes

    if len(boxes) == 0:
        raise HTTPException(status_code=404, detail="No license plates detected")

    plates_output = []

    # ---------------------------
    # Process each detected plate
    # ---------------------------
    for idx, box in enumerate(boxes):
        x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())

        # Keep coords within image
        x1 = max(0, x1); y1 = max(0, y1)
        x2 = min(img_cv2.shape[1], x2); y2 = min(img_cv2.shape[0], y2)

        # Crop plate region
        cropped_plate = img_cv2[y1:y2, x1:x2]

        # Optional Debug Save
        # cv2.imwrite(f"debug_plate_{idx+1}.jpg", cropped_plate)

        # ---------------------------
        # Detect characters on plate
        # ---------------------------
        char_results = char_detector(cropped_plate, conf=0.30, verbose=False)

        char_boxes_raw = []
        char_items = []   # (x_min, char)

        char_map = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"

        for cbox in char_results[0].boxes:
            cx1, cy1, cx2, cy2 = map(int, cbox.xyxy[0].tolist())
            conf = float(cbox.conf[0])
            cls = int(cbox.cls[0])

            # Map class index to the actual character
            detected_char = char_map[cls] if cls < len(char_map) else "?"

            # Collect char based on X-position
            char_items.append((cx1, detected_char))

            # Box for response
            char_boxes_raw.append({
                "x_min": cx1, "y_min": cy1,
                "x_max": cx2, "y_max": cy2,
                "confidence": conf,
                "cls": cls
            })

        # Sort chars left → right
        char_items.sort(key=lambda x: x[0])
        plate_number = "".join([c for (_, c) in char_items])

        # Sort boxes too
        char_boxes_sorted = sort_characters(char_boxes_raw)

        # Convert dicts → Pydantic
        char_boxes = [BoundingBox(**b) for b in char_boxes_sorted]

        # Add plate result
        plates_output.append(
            PlateOutput(
                plate_number=plate_number,
                plate_confidence=float(box.conf[0]),   # <-- NEW
                plate_box=BoundingBox(
                    x_min=x1, y_min=y1,
                    x_max=x2, y_max=y2,
                    confidence=float(box.conf[0]),
                    cls=int(box.cls[0]),
                ),
                char_boxes=char_boxes,
            )
        )

    end_time = time.time()

    return MultiPlateResponse(
        status="success",
        total_plates=len(plates_output),
        plates=plates_output,
        time_taken_ms=(end_time - start_time) * 1000,
    )
