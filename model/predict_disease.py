import numpy as np
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing import image
import os

# Load the model
model_path = os.path.join("model", "plant_disease_model.h5")
model = load_model(model_path)

# Get class labels based on the folder names in train directory
class_labels = sorted(os.listdir(os.path.join("PlantVillage", "train")))

def predict_disease(img_path):
    try:
        img = image.load_img(img_path, target_size=(128, 128))
        img_array = image.img_to_array(img)
        img_array = img_array / 255.0  # Normalize
        img_array = np.expand_dims(img_array, axis=0)

        prediction = model.predict(img_array)
        predicted_class_index = np.argmax(prediction)
        predicted_label = class_labels[predicted_class_index]
        return predicted_label
    except Exception as e:
        return f"Error: {e}"
