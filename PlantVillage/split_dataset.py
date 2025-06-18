import os
import shutil
import random

# Define your main dataset folder
base_dir = "PlantVillage"
train_dir = os.path.join(base_dir, "train")
test_dir = os.path.join(base_dir, "test")

# Create train and test folders
os.makedirs(train_dir, exist_ok=True)
os.makedirs(test_dir, exist_ok=True)

# Set split ratio
split_ratio = 0.8

# List all disease class folders
class_folders = [f for f in os.listdir(base_dir)
                 if os.path.isdir(os.path.join(base_dir, f)) and f not in ['train', 'test']]

for class_name in class_folders:
    print(f"Processing class: {class_name}")
    class_path = os.path.join(base_dir, class_name)
    images = os.listdir(class_path)
    random.shuffle(images)

    # Split data
    split_point = int(len(images) * split_ratio)
    train_images = images[:split_point]
    test_images = images[split_point:]

    # Make class folders in train/test
    os.makedirs(os.path.join(train_dir, class_name), exist_ok=True)
    os.makedirs(os.path.join(test_dir, class_name), exist_ok=True)

    # Move images
    for img in train_images:
        src = os.path.join(class_path, img)
        dst = os.path.join(train_dir, class_name, img)
        shutil.move(src, dst)

    for img in test_images:
        src = os.path.join(class_path, img)
        dst = os.path.join(test_dir, class_name, img)
        shutil.move(src, dst)

    # Optionally remove the now-empty original class folder
    os.rmdir(class_path)

print("✅ Dataset split into train and test folders successfully.")
