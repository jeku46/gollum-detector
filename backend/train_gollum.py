"""
Train YOLOv11 model for Gollum detection
"""
from roboflow import Roboflow
from ultralytics import YOLO
import os

print("=" * 60)
print("Training YOLOv11 Gollum Detection Model")
print("=" * 60)

# Configuration
API_KEY = "g3kyzU8K82YQwalVS2Ks"
WORKSPACE = "die-counter"
PROJECT_NAME = "gollum-finder-b7c9n"
VERSION = 1  # gollum-finder-1
MODEL = "yolo11n.pt"  # YOLOv11 nano - fast training, good for testing

print(f"\nConfiguration:")
print(f"  Project: {PROJECT_NAME}")
print(f"  Version: {VERSION}")
print(f"  Model: {MODEL}")
print("=" * 60)

# Dataset path (already downloaded)
DATASET_PATH = "/Users/jenniferkuchta/Projects/GollumApp/backend/Gollum-Finder-1"
print(f"\n1. Using dataset at: {DATASET_PATH}")

# Load base model
print(f"\n2. Loading {MODEL}...")
model = YOLO(MODEL)

# Train the model
print("\n3. Starting training...")
print("   This may take 10-30 minutes depending on your hardware.\n")

results = model.train(
    data=f"{DATASET_PATH}/data.yaml",
    epochs=50,          # Reduced epochs for faster training
    imgsz=640,
    batch=8,            # Smaller batch for Mac memory
    name='gollum-yolo11',
    patience=10,        # Early stopping
    device='mps',       # Apple Silicon GPU
    verbose=True,
)

print("\n" + "=" * 60)
print("Training Complete!")
print("=" * 60)

# Get the best model path
best_model_path = "runs/detect/gollum-yolo11/weights/best.pt"
print(f"\nBest model saved at: {best_model_path}")

# Copy best model to a convenient location
import shutil
final_model_path = os.path.join(os.path.dirname(__file__), "gollum_model.pt")
if os.path.exists(best_model_path):
    shutil.copy(best_model_path, final_model_path)
    print(f"Model copied to: {final_model_path}")

print("\nNext: Update server.py to use this model for live detection!")
print("=" * 60)
