import os
import csv
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, send_from_directory
from werkzeug.utils import secure_filename
from model import predict_leaf_disease  # you will create this file with a prediction function

# Flask app config
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['ALLOWED_EXTENSIONS'] = {'jpg', 'jpeg', 'png', 'gif'}

# Make sure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Allow only certain image types
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

# Home redirect to /predict
@app.route('/')
def home():
    return redirect(url_for('predict'))

# Predict Route
@app.route('/predict', methods=['GET', 'POST'])
def predict():
    if request.method == 'POST':
        file = request.files.get('file')
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)

            # Call your model prediction function
            result = predict_leaf_disease(filepath)

            # Save to history CSV
            with open('prediction_history.csv', 'a', newline='') as file_history:
                writer = csv.writer(file_history)
                writer.writerow([filename, result['plant_type'], result['diseases'][0]['name'], result['diseases'][0]['confidence'], datetime.now()])

            # Render predict.html with results
            return render_template(
                'predict.html',
                filename=filename,
                plant_type=result['plant_type'],
                plant_category=result['plant_category'],
                diseases=result['diseases']
            )

    # On GET request, just show the form
    return render_template('predict.html')

# File downloader (used for report/PDF)
@app.route('/download_report', methods=['POST'])
def download_report():
    filename = request.form.get('filename')
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)

# Serve uploaded images
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    app.run(debug=True)
