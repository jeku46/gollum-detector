"""
Script to train YOLOv8/YOLOv11 model locally using Roboflow dataset

Prerequisites:
    pip install ultralytics roboflow

Usage:
    python train_yolo.py

To find your project details:
    1. Visit https://app.roboflow.com/die-counter
    2. Click on your Gollum detection project
    3. Note the project URL - it will be like: /die-counter/YOUR_PROJECT_NAME
    4. Click on the version you want to use - it will show "Version X"
"""

from roboflow import Roboflow
from ultralytics import YOLO
import os

print("=" * 60)
print("YOLO Training Script for Gollum Detection")
print("=" * 60)

# Configuration - UPDATE THESE VALUES
API_KEY = "g3kyzU8K82YQwalVS2Ks"
WORKSPACE = "die-counter"

# Get project details from user
print("\nTo find your project name and version:")
print("1. Visit https://app.roboflow.com/die-counter")
print("2. Your project URL will show the project name")
print("3. Select the version you want to train with\n")

PROJECT_NAME = input("Enter your project name (or press Enter to use 'gollum-detection-pwu2j'): ").strip() or "gollum-detection-pwu2j"
VERSION = input("Enter your dataset version number (e.g., 1, 2, 3): ").strip()

if not VERSION:
    print("Error: Version number is required")
    exit(1)

VERSION = int(VERSION)

# Ask for model choice
print("\n" + "=" * 60)
print("Choose YOLO Model:")
print("=" * 60)
print("YOLOv8 options:")
print("  1. yolov8n.pt (nano - fastest, least accurate)")
print("  2. yolov8s.pt (small)")
print("  3. yolov8m.pt (medium)")
print("  4. yolov8l.pt (large)")
print("  5. yolov8x.pt (xlarge - slowest, most accurate)")
print("\nYOLOv11 options (newer, often better):")
print("  6. yolo11n.pt (nano - fastest, least accurate)")
print("  7. yolo11s.pt (small)")
print("  8. yolo11m.pt (medium)")
print("  9. yolo11l.pt (large)")
print("  10. yolo11x.pt (xlarge - slowest, most accurate)")

model_choice = input("\nEnter choice (1-10, or press Enter for yolo11n): ").strip() or "6"
model_map = {
    "1": "yolov8n.pt", "2": "yolov8s.pt", "3": "yolov8m.pt", "4": "yolov8l.pt", "5": "yolov8x.pt",
    "6": "yolo11n.pt", "7": "yolo11s.pt", "8": "yolo11m.pt", "9": "yolo11l.pt", "10": "yolo11x.pt",
}
model_name = model_map.get(model_choice, "yolo11n.pt")

print(f"\n{'=' * 60}")
print(f"Configuration:")
print(f"{'=' * 60}")
print(f"Workspace: {WORKSPACE}")
print(f"Project: {PROJECT_NAME}")
print(f"Version: {VERSION}")
print(f"Model: {model_name}")
print(f"{'=' * 60}\n")

# Initialize Roboflow
print("Connecting to Roboflow...")
rf = Roboflow(api_key=API_KEY)
project = rf.workspace(WORKSPACE).project(PROJECT_NAME)

# Download dataset in YOLOv8 format
print(f"Downloading dataset version {VERSION}...")
dataset = project.version(VERSION).download("yolov8")
print(f"Dataset downloaded to: {dataset.location}")

# Initialize model
print(f"\nLoading {model_name}...")
model = YOLO(model_name)

# Train the model
print("\nStarting training...")
print("This may take a while depending on your hardware and dataset size.\n")

results = model.train(
    data=f"{dataset.location}/data.yaml",  # Path to dataset YAML
    epochs=100,                              # Number of training epochs
    imgsz=640,                              # Image size
    batch=16,                               # Batch size (adjust based on GPU/CPU memory)
    name='gollum-detector',                 # Experiment name
    patience=20,                            # Early stopping patience
    device='mps',                           # Use Apple Silicon GPU (change to 0 for NVIDIA GPU or 'cpu' for CPU)
    # Additional parameters you can adjust:
    # lr0=0.01,                             # Initial learning rate
    # augment=True,                         # Apply data augmentation
)

print("\n" + "=" * 60)
print("Training Complete!")
print("=" * 60)

# Validate the model
print("\nValidating model...")
metrics = model.val()

print(f"\nResults:")
print(f"  Best model: runs/detect/gollum-detector/weights/best.pt")
print(f"  Last model: runs/detect/gollum-detector/weights/last.pt")
print(f"  Metrics: {metrics}")

# Ask if user wants to export
export_choice = input("\nDo you want to export the model? (y/n): ").strip().lower()
if export_choice == 'y':
    print("Exporting model to ONNX format...")
    model.export(format='onnx')
    print("Export complete!")

print("\n" + "=" * 60)
print("Next Steps:")
print("=" * 60)
print("1. Check the training results in: runs/detect/gollum-detector/")
print("2. Your best model is at: runs/detect/gollum-detector/weights/best.pt")
print("3. You can upload this model to Roboflow or use it locally")
print("=" * 60)
