# 🌿 Crop Disease Detector

A deep learning-based web application that detects crop diseases from plant leaf images using a trained Convolutional Neural Network (CNN) model.

---

## 🚀 Features

- Upload plant leaf images to detect diseases
- Accurate CNN-based predictions
- Clean web interface using Flask
- Saves prediction history in a database

---

## 🧠 Algorithm Used

This project uses a **Convolutional Neural Network (CNN)** to classify plant diseases. CNNs are ideal for image classification tasks because they can automatically learn and extract spatial features from images.

---

## 📁 Project Structure
├── app.py # Flask web application
├── model.py # CNN model definition
├── plant_disease_model.h5 # Trained model file
├── templates/ # HTML templates
├── static/ # CSS and assets
├── dataset/ # Image dataset
├── prediction_history.csv # Stores prediction logs
├── database.py # SQLite database setup
├── .gitignore # Ignore unnecessary files
└── README.md # Project overview

#  How to Run the Project
```bash
git clone https://github.com/samiksha1218/Crop-disease-detector.git
cd Crop-disease-detector
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python app.py

Then open your browser and go to: http://localhost:5000

