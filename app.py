from flask import Flask, render_template, request, redirect, url_for, session,flash
from flask_mail import Mail, Message
from werkzeug.utils import secure_filename
from collections import Counter 
from datetime import datetime


import json
import sqlite3
import os
import uuid
import csv
import numpy as np

from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing import image


from database import (
    init_db, save_to_database, get_all_predictions,
    add_user, validate_user, export_predictions_to_csv,
    delete_all_predictions, delete_user_predictions
)

app = Flask(__name__)
app.secret_key = 'your_secret_key'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
app.config['UPLOAD_FOLDER'] = 'static/uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Flask-Mail configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'your_email@gmail.com'  # Your Gmail address
app.config['MAIL_PASSWORD'] = 'your_app_password' 


mail = Mail(app)
init_db()
    # Use App Password (not your regular password!)



model = load_model('model/plant_disease_model.h5')  # Load your trained model once
class_labels = ['Bacterial Blight', 'Leaf Rust', 'Healthy']  # ✅ Adjust as per your trained labels 
disease_info = {
    'Bacterial Blight': {
        'symptoms': 'Water-soaked spots on leaves',
        'cause': 'Xanthomonas bacteria',
        'remedy': 'Use copper-based fungicides and remove infected leaves'
    },
    'Leaf Rust': {
        'symptoms': 'Reddish-orange pustules on leaf surface',
        'cause': 'Fungal spores spread by wind',
        'remedy': 'Apply fungicide, rotate crops'
    },
    'Healthy': {
        'symptoms': 'No visible symptoms',
        'cause': 'None',
        'remedy': 'No treatment needed'
    }
}





UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

#dashboard
@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect(url_for('login'))

    username = session['username']

    # Connect to database and fetch prediction history for this user
    conn = sqlite3.connect('predictions.db')  # Change to your actual database path
    cursor = conn.cursor()
    cursor.execute("SELECT prediction FROM predictions WHERE username = ?", (username,))
    rows = cursor.fetchall()
    conn.close()

    total_predictions = len(rows)
    prediction_list = [row[0] for row in rows]

    # Find most common disease
    if prediction_list:
        common_disease = Counter(prediction_list).most_common(1)[0][0]
    else:
        common_disease = "N/A"

    return render_template('dashboard.html',
                           total_predictions=total_predictions,
                           common_disease=common_disease)


@app.route('/profile')
def profile():
    return render_template('profile.html')  # make sure profile.html exists



# Add history route here
@app.route('/history')
def history():
    # Check if user is logged in
    if 'username' not in session:
        return redirect(url_for('login'))

    username = session['username']

    # Get filter parameters from request (optional)
    selected_disease = request.args.get('disease', 'All')
    date_from_str = request.args.get('date_from', '')
    date_to_str = request.args.get('date_to', '')
    confidence_str = request.args.get('confidence', '')
    filter_date = request.args.get('date', '')  # Exact match filter

    # Fetch all predictions for the user
    all_predictions = get_all_predictions(username)  # (image_path, disease, confidence, timestamp)

    filtered_predictions = []

    # Convert filter values to appropriate types
    date_from = datetime.strptime(date_from_str, '%Y-%m-%d') if date_from_str else None
    date_to = datetime.strptime(date_to_str, '%Y-%m-%d') if date_to_str else None
    min_confidence = float(confidence_str) if confidence_str else 0.0

    # Filter predictions based on selected filters
    for p in all_predictions:
        image, disease, confidence, pred_date = p

        # Ensure pred_date is a datetime object
        if isinstance(pred_date, str):
            pred_date = datetime.strptime(pred_date, '%Y-%m-%d %H:%M:%S')

       # Apply disease filter
        if selected_disease != "All" and disease != selected_disease:
           continue

       # Get min_confidence from request and safely convert it
        min_confidence_str = request.args.get('confidence')
        try:
           min_confidence = float(min_confidence_str) if min_confidence_str else 0.0
        except ValueError:
           min_confidence = 0.0  # fallback if user types something invalid

       # Apply confidence filter
        if confidence is not None and confidence < min_confidence:
           continue


        # Apply date filters
        if date_from and pred_date < date_from:
            continue
        if date_to and pred_date > date_to:
            continue
        if filter_date and not pred_date.strftime('%Y-%m-%d').startswith(filter_date):
            continue

        # If all filters are passed, add to filtered list
        filtered_predictions.append((image, disease, confidence, pred_date))

    # Get all unique disease types from predictions
    disease_types = sorted(set(p[1] for p in all_predictions))

    # Render history page with filtered predictions
    return render_template("history.html",
                           predictions=filtered_predictions,
                           disease_types=disease_types,
                           selected_disease=selected_disease,
                           date_from=date_from_str,
                           date_to=date_to_str,
                           confidence=confidence_str,
                           filter_date=filter_date)




# delete user's own predictions
@app.route('/delete_my_predictions', methods=['POST'])
def delete_my_predictions():
    if 'username' in session:
        delete_user_predictions(session['username'])
        flash("Your predictions have been deleted.", "info")
    else:
        flash("Please log in to delete your predictions.", "warning")
    return redirect(url_for('history'))

# admin delete all predictions
@app.route('/admin_delete_all_predictions', methods=['POST'])
def admin_delete_all_predictions():
    if 'username' in session and session['username'] == 'admin':  # or use is_admin flag
        delete_all_predictions()
        flash("All predictions have been deleted.", "danger")
    else:
        flash("Access denied.", "danger")
    return redirect(url_for('dashboard'))  # or redirect to admin page





#clear history
@app.route('/clear_history')
def clear_history():
    if 'username' not in session:
        return redirect(url_for('login'))

    username = session['username']
    delete_all_predictions(username)  # This calls a function from database.py
    flash("History cleared.")
    return redirect(url_for('history'))




# Add export CSV route here
@app.route('/export_csv')
def export_csv():
    if 'username' not in session:
        return redirect(url_for('login'))

    username = session['username']
    csv_path = export_predictions_to_csv(username)  # You should have this function in database.py
    return redirect('/' + csv_path)



@app.route('/')
def index():
   return render_template('index.html')




#login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = validate_user(username, password)
        if user:
            session['username'] = username
            return redirect(url_for('dashboard'))  # or wherever you want to redirect after login
        else:
            return render_template('login.html', error="Invalid username or password")
    
    return render_template('login.html')


#predict
# app.py or routes.py
@app.route('/predict', methods=['GET', 'POST'])
def predict():
    if 'username' not in session:
        return redirect(url_for('login'))

    if request.method == 'GET':
        return render_template('predict.html', hide_register_button=True)

    if 'file' not in request.files:
        return "No file part", 400

    file = request.files['file']
    if file.filename == '':
        return "No selected file", 400  

    if file:
        filename = secure_filename(file.filename)
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(image_path)

        result = predict_disease(image_path)
        print("MODEL RESULT:", result)

        if isinstance(result, dict):
            diseases = result.get('diseases', [])
            plant_type = result.get('plant_type', 'Unknown Plant')
            plant_category = result.get('plant_category', 'Unknown Category')
        elif isinstance(result, str):
            diseases = [{'name': result, 'confidence': 0.0}]
            plant_type = 'Unknown Plant'
            plant_category = 'Unknown Category'
        else:
            diseases = []
            plant_type = 'Unknown Plant'
            plant_category = 'Unknown Category'

        if diseases:
            prediction_result = diseases[0].get('name', 'Unknown Disease')
            confidence = diseases[0].get('confidence', 0.0)
        else:
            prediction_result = 'No Disease Detected'
            confidence = 0.0

        save_to_database(session['username'], image_path, prediction_result)

        with open('prediction_history.csv', 'a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([filename, prediction_result, confidence, datetime.now()])

        for disease in diseases:
            info = disease_info.get(disease['name'], {})
            disease['symptoms'] = info.get('symptoms', 'Not available')
            disease['cause'] = info.get('cause', 'Not available')
            disease['remedy'] = info.get('remedy', 'Not available')    

        return render_template(
            'predict.html',
            prediction_result=prediction_result,
            confidence=confidence,
            plant_type=plant_type,
            plant_category=plant_category,
            filename=filename,
            diseases=diseases,
            hide_register_button=True  # Add this here too!
        )






# Show treatment details for a specific disease
@app.route('/treatment/<disease_name>')
def treatment(disease_name):
    suggestions = {
        "Leaf Rust": {
            "medicine": "Use Mancozeb-based fungicide weekly.",
            "supplements": "Apply potassium-rich fertilizer.",
            "pesticides": "Neem oil or sulfur-based sprays.",
            "tips": "Avoid overhead watering and rotate crops."
        },
        "Bacterial Blight": {
            "medicine": "Copper-based bactericide like Kocide 3000.",
            "supplements": "Zinc and magnesium foliar spray.",
            "pesticides": "Bordeaux mixture can be applied.",
            "tips": "Remove infected leaves and sanitize tools."
        },
        "Powdery Mildew": {
            "medicine": "Sulfur or potassium bicarbonate sprays.",
            "supplements": "Use seaweed extract for better resistance.",
            "pesticides": "Spray horticultural oils weekly.",
            "tips": "Improve air circulation and reduce humidity."
        },
        "Root Rot": {
            "medicine": "Fungicide with mefenoxam or fosetyl-Al.",
            "supplements": "Use bio-fungicides with Trichoderma.",
            "pesticides": "Avoid overuse—focus on drainage.",
            "tips": "Use well-draining soil and avoid overwatering."
        },
        "Early Blight": {
            "medicine": "Chlorothalonil or copper fungicides.",
            "supplements": "Nitrogen-balanced fertilizer.",
            "pesticides": "Spray every 7–10 days as preventive.",
            "tips": "Destroy infected debris and mulch around plants."
        },
        "Late Blight": {
           "medicine": "Use fungicides like Metalaxyl or Mancozeb.",
           "supplements": "Add phosphorus-rich fertilizers to strengthen roots.",
           "pesticides": "Use preventive sprays weekly during wet weather.",
           "tips": "Remove infected plants. Ensure good drainage and reduce humidity."
        }
    }

    suggestion = suggestions.get(disease_name, {
        "medicine": "Information not available.",
        "supplements": "Information not available.",
        "pesticides": "Information not available.",
        "tips": "Please consult an expert for specific treatment."
    })

    return render_template('treatment.html', disease_name=disease_name, suggestion=suggestion)





           






# download_report route (Add here)
@app.route('/download-report', methods=['GET', 'POST'])
def handle_download_report():
    if request.method == 'POST':
        # Handle report generation via POST (e.g., form submission)
        image = request.form.get('image')
        prediction = request.form.get('prediction')
    else:
        # Handle GET method (e.g., via query params)
        image = request.args.get('image')
        prediction = request.args.get('prediction')

    report_text = f"Prediction Report\n\nImage: {image}\nPrediction: {prediction}"
    
    return Response(
        report_text,
        mimetype="text/plain",
        headers={"Content-disposition": "attachment; filename=prediction_report.txt"}
    )






#register
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        data = request.form

        # Check if passwords match
        if data['password'] != data['confirm_password']:
            flash("Passwords do not match!")
            return redirect(url_for('register'))

        # Call the add_user() function from database.py
        success = add_user(
            data['first_name'], data['last_name'], data['username'], data['dob'],
            data['gender'], data['email'], data['phone'], data['alt_phone'],
            data['password'], data['house'], data['street'], data['landmark'],
            data['city'], data['state'], data['pin'], data['country'], data['language']
        )

        if not success:
            flash("Username already exists. Please choose another.")
            return redirect(url_for('register'))

        flash("Registration successful!")
        return redirect(url_for('login'))

    return render_template('register.html')







#logout
@app.route('/logout')
def logout():
    session.pop('username', None)
    flash("You have been logged out.")
    return redirect(url_for('login'))


#forgot_ password
@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email']

        # Check if email exists in the users table
        conn = sqlite3.connect('predictions.db')
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
        user = cursor.fetchone()
        conn.close()

        if user:
            token = str(uuid.uuid4())

            # Save token in reset_tokens table
            conn = sqlite3.connect('predictions.db')
            cursor = conn.cursor()
            cursor.execute("INSERT INTO reset_tokens (email, token) VALUES (?, ?)", (email, token))
            conn.commit()
            conn.close()

            # Generate reset link
            reset_link = url_for('reset_password', token=token, _external=True)

            # Send email
            msg = Message('Password Reset Request',
                          sender='your_email@gmail.com',
                          recipients=[email])
            msg.body = f'''Hi,

Click the link below to reset your password:

{reset_link}

If you didn't request this, please ignore this email.

Thanks!'''
            mail.send(msg)

            flash('Password reset link has been sent to your email.')
        else:
            flash('Email not found.')

        return redirect(url_for('forgot_password'))

    return render_template('forgot_password.html')





#reset password
@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    conn = sqlite3.connect('your_database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT email FROM reset_tokens WHERE token = ?", (token,))
    row = cursor.fetchone()
    conn.close()

    email = row[0] if row else None

    if not email:
        flash('Invalid or expired token.')
        return redirect(url_for('login'))

    if request.method == 'POST':
        new_password = request.form['password']
        confirm_password = request.form['confirm_password']

        if new_password != confirm_password:
            flash('Passwords do not match.')
            return redirect(url_for('reset_password', token=token))

        # Update password
        conn = sqlite3.connect('predictions.db')
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET password = ? WHERE email = ?", (new_password, email))
        conn.commit()

        # Delete used token
        cursor.execute("DELETE FROM reset_tokens WHERE token = ?", (token,))
        conn.commit()
        conn.close()

        flash('Password reset successful. You can now log in.')
        return redirect(url_for('login'))

    return render_template('reset_password.html')






#home route
@app.route('/')
def home():
    if 'username' in session:
        return redirect(url_for('dashboard'))
    else:
        return render_template('index.html')




#download_report
@app.route('/download-report')
def download_report():
    # Sample prediction data (replace with actual DB query)
    predictions = [
        {'date': '2025-04-01', 'plant': 'Tomato', 'disease': 'Leaf Curl'},
        {'date': '2025-04-02', 'plant': 'Potato', 'disease': 'Early Blight'},
    ]

    # Create a CSV in memory
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=['date', 'plant', 'disease'])
    writer.writeheader()
    writer.writerows(predictions)

    # Create response with CSV data
    response = Response(output.getvalue(), mimetype='text/csv')
    response.headers['Content-Disposition'] = 'attachment; filename=prediction_report.csv'
    return response



#date time
from datetime import datetime

@app.template_filter('datetimeformat')
def datetimeformat(value, format='%B %d, %Y, %I:%M %p'):
    """Format datetime string to readable format."""
    try:
        dt = datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
        return dt.strftime(format)
    except Exception:
        return value  # If format fails, return original




# Upload route for capturing/uploading leaf image
@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        # Handling file upload
        if 'image' in request.files:
            image = request.files['image']
            if image.filename == '':
                return "No selected image"
            if image:
                filename = secure_filename(image.filename)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                image.save(filepath)
                
                # Call your ML model prediction here
                prediction, symptoms, solution = predict_disease(filepath)
                
                return render_template('result.html', prediction=prediction, symptoms=symptoms, solution=solution)
        
        # Handling webcam image capture
        elif 'webcam_image' in request.form:
            webcam_image_data = request.form['webcam_image']
            image_data = webcam_image_data.split(',')[1]  # Remove the 'data:image/jpeg;base64,' part
            image_data = base64.b64decode(image_data)  # Decode the base64 string

            # Save the webcam image to the static folder
            filename = 'webcam_capture.jpg'
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            with open(filepath, 'wb') as f:
                f.write(image_data)
                
            # Call your ML model prediction here
            prediction, symptoms, solution = predict_disease(filepath)
            
            return render_template('result.html', prediction=prediction, symptoms=symptoms, solution=solution)

    return render_template('upload.html')

# Prediction logic placeholder
def predict_disease(image_path):
    return {
        'plant_type': "Tomato",
        'plant_category': "Vegetable",
        'diseases': [
            {"name": "Late Blight", "confidence": 92},
            {"name": "Early Blight", "confidence": 85}
        ]
    }




#predict leaf
def predict_leaf(img_path):
    img = image.load_img(img_path, target_size=(224, 224))
    img_array = image.img_to_array(img)
    img_array = np.expand_dims(img_array, axis=0)
    img_array = img_array / 255.0

    prediction = model.predict(img_array)[0]
    predicted_index = np.argmax(prediction)
    prediction_result = class_labels[predicted_index]
    confidence = round(prediction[predicted_index] * 100, 2)

    # Add static knowledge for demo purposes
    disease_info = {
        "Leaf Blight": {
            "prevention": "Ensure good air circulation, avoid overhead watering, use disease-free seeds.",
            "supplements": "Apply copper-based fungicides, balanced NPK fertilizer.",
            "duration": "10-15 days with proper treatment."
        },
        "Leaf Rust": {
            "prevention": "Avoid overhead watering and maintain air circulation.",
            "supplements": "Use potassium-rich fertilizer.",
            "duration": "1–2 weeks after treatment with fungicide."
        },
        "Healthy": {
            "prevention": "Maintain proper watering and sunlight. Regular monitoring.",
            "supplements": "None needed.",
            "duration": "No treatment required."
        }
    }

    info = disease_info.get(prediction_result, {
        "prevention": "Not Available",
        "supplements": "Not Available",
        "duration": "Not Available"
    })

    return {
        'name': 'Wheat Leaf',  # You can make this dynamic later
        'disease': prediction_result,
        'prevention': info['prevention'],
        'supplements': info['supplements'],
        'duration': info['duration']
    }





#scan_leaf
@app.route('/scan-leaf', methods=['GET', 'POST'])
def scan_leaf():
    if request.method == 'POST':
        if 'leaf_image' not in request.files:
            flash('No file part')
            return redirect(request.url)

        file = request.files['leaf_image']
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)

        if file:
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)

            prediction_data = predict_leaf(filepath)

            return render_template(
                'scan_result.html',
                prediction=prediction_data['disease'],
                symptoms=prediction_data['prevention'],
                solution=prediction_data['supplements']
            )

    return render_template('scan_leaf.html')







@app.route('/disease-report')
def disease_report():
    # Demo data
    predictions = [
        {
            'name': 'Wheat Leaf',
            'disease': 'Leaf Blight',
            'prevention': 'Ensure good air circulation, avoid overhead watering, use disease-free seeds.',
            'supplements': 'Apply copper-based fungicides, balanced NPK fertilizer.',
            'duration': '10-15 days with proper treatment.'
        },
        {
            'name': 'Tomato Leaf',
            'disease': 'Early Blight',
            'prevention': 'Rotate crops annually, remove infected leaves, use resistant varieties.',
            'supplements': 'Neem oil spray, phosphorus-rich fertilizer.',
            'duration': '7-10 days depending on severity.'
        }
        # Add more plant reports if needed
    ]
    return render_template('disease_report.html', predictions=predictions)

















if __name__ == '__main__':
    app.run(debug=True)


 #   import webbrowser
# webbrowser.open('http://127.0.0.1:5000')

