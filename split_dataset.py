import os
import shutil
import glob

# Define paths
DATASET_DIR = 'PlantVillage'  # Root folder with 'train' and 'test'
TRAIN_DIR = 'dataset/train'
TEST_DIR = 'dataset/test'

def split_data():
    # Get the list of classes from the train folder
    train_classes = os.listdir(os.path.join(DATASET_DIR, 'train'))

    for cls in train_classes:
        train_class_path = os.path.join(DATASET_DIR, 'train', cls)
        test_class_path = os.path.join(DATASET_DIR, 'test', cls)

        # Create corresponding directories in output folders
        os.makedirs(os.path.join(TRAIN_DIR, cls), exist_ok=True)
        os.makedirs(os.path.join(TEST_DIR, cls), exist_ok=True)

        # Copy training images (skip if not a file)
        for img in os.listdir(train_class_path):
            src = os.path.join(train_class_path, img)
            dst = os.path.join(TRAIN_DIR, cls, img)
            if os.path.isfile(src):
                shutil.copy(src, dst)
                print(f"Copied to train: {dst}")

        # Copy testing images (skip if not a file)
        for img in os.listdir(test_class_path):
            src = os.path.join(test_class_path, img)
            dst = os.path.join(TEST_DIR, cls, img)
            if os.path.isfile(src):
                shutil.copy(src, dst)
                print(f"Copied to test: {dst}")


     # Optional: Clean up any empty folders
    for folder in glob.glob(os.path.join(DATASET_DIR, "*", "*/")):
        if not os.listdir(folder):
            os.rmdir(folder)
            print(f"Removed empty folder: {folder}")

if __name__ == "__main__":
    split_data()
