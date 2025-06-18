import numpy as np
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing import image
from model import predict_leaf_disease



# Class names must match model output
CLASS_NAMES = ["Healthy", "Powdery Mildew", "Leaf Spot", "Rust"]

# Load trained model
model = load_model("plant_disease_model.h5")

# Define disease details (add more if needed)
DISEASE_INFO = {
    "Healthy": {
        "symptoms": "No visible symptoms. Leaf is healthy.",
        "cause": "None",
        "remedy": "No treatment needed."
    },
    "Powdery Mildew": {
        "symptoms": "White powdery spots on leaves.",
        "cause": "Fungal infection (Erysiphales).",
        "remedy": "Apply sulfur-based fungicides and improve air circulation."
    },
    "Leaf Spot": {
        "symptoms": "Dark or light brown spots on leaves.",
        "cause": "Bacterial or fungal infection.",
        "remedy": "Remove affected leaves and apply appropriate fungicide."
    },
    "Rust": {
        "symptoms": "Orange or yellow spots on the underside of leaves.",
        "cause": "Rust fungus (Pucciniales).",
        "remedy": "Use rust-specific fungicides and remove infected leaves."
    },
    "Downy Mildew": {
    "symptoms": "Yellowish patches on upper leaf surfaces, grey mold on undersides.",
    "cause": "Fungal pathogen (Peronospora spp.)",
    "remedy": "Apply metalaxyl-based fungicides, improve airflow."
},

}

# Use this function in routes.py
def predict_leaf_disease(img_path):
    img = image.load_img(img_path, target_size=(64, 64))
    img_array = image.img_to_array(img)
    img_array = np.expand_dims(img_array, axis=0)
    img_array = img_array / 255.0

    prediction = model.predict(img_array)[0]
    predicted_index = np.argmax(prediction)
    predicted_class = CLASS_NAMES[predicted_index]
    confidence = float(np.max(prediction)) * 100

    disease_info = DISEASE_INFO.get(predicted_class, {
        "symptoms": "N/A",
        "cause": "N/A",
        "remedy": "N/A"
    })

    return {
        "plant_type": "Unknown Plant",  # Optional: use image metadata or user input
        "plant_category": "Unknown Category",  # Optional
        "diseases": [
            {
                "name": predicted_class,
                "confidence": round(confidence, 2),
                "symptoms": disease_info["symptoms"],
                "cause": disease_info["cause"],
                "remedy": disease_info["remedy"]
            }
        ]
    }
