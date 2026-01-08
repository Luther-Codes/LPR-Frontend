from pathlib import Path
import time
import streamlit as st
from PIL import Image
import cv2
import numpy as np
from ultralytics import YOLO

# ----------------------------
# Config Paths
# ----------------------------
BASE_DIR = Path(__file__).resolve().parent
MODEL_DIR = BASE_DIR / "models"

# ---------------------------
# Page Config
# ---------------------------
st.set_page_config(
    page_title="License Plate Recognition",
    layout="centered"
)

st.title("License Plate Recognition (YOLOv8)")
st.caption("Plate detection + character recognition")

# ---------------------------
# Load Models (cached)
# ---------------------------
@st.cache_resource
def load_models():
    plate_detector = YOLO(str(MODEL_DIR / "LPR_MODEL.pt"))
    char_detector = YOLO(str(MODEL_DIR / "OCR_MODEL.pt"))
    return plate_detector, char_detector


plate_detector, char_detector = load_models()

# ---------------------------
# Utilities
# ---------------------------
CHAR_MAP = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"

def sort_characters(char_boxes):
    return sorted(char_boxes, key=lambda b: b["x_min"])

# ---------------------------
# File Upload
# ---------------------------
uploaded_file = st.file_uploader(
    "Upload an image",
    type=["jpg", "jpeg", "png"]
)

if uploaded_file:
    start_time = time.time()

    # Load image
    pil_img = Image.open(uploaded_file).convert("RGB")
    img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)

    st.image(pil_img, caption="Uploaded Image", use_container_width=True)

    # ---------------------------
    # Plate Detection
    # ---------------------------
    plate_results = plate_detector(img, conf=0.4, verbose=False)
    boxes = plate_results[0].boxes

    if len(boxes) == 0:
        st.error("No license plate detected")
        st.stop()

    st.subheader("Detected Plates")

    for idx, box in enumerate(boxes):
        x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
        cropped_plate = img[y1:y2, x1:x2]

        st.image(
            cv2.cvtColor(cropped_plate, cv2.COLOR_BGR2RGB),
            caption=f"Plate {idx + 1}"
        )

        # ---------------------------
        # Character Detection
        # ---------------------------
        char_results = char_detector(cropped_plate, conf=0.3, verbose=False)

        char_items = []
        for cbox in char_results[0].boxes:
            cx1 = int(cbox.xyxy[0][0])
            cls = int(cbox.cls[0])
            char = CHAR_MAP[cls] if cls < len(CHAR_MAP) else "?"
            char_items.append((cx1, char))

        char_items.sort(key=lambda x: x[0])
        plate_number = "".join(c for _, c in char_items)

        st.success(f"Plate Number: **{plate_number}**")

    elapsed = (time.time() - start_time) * 1000
    st.caption(f"Time taken: {elapsed:.2f} ms")
