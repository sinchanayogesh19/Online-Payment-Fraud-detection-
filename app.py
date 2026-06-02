from flask import Flask, render_template, request, redirect, session, url_for
from werkzeug.security import generate_password_hash, check_password_hash
import numpy as np
import pandas as pd
import joblib
import json
import os
from functools import wraps

app = Flask(__name__)
app.secret_key = 'your_secret_key_change_this'

# Load model & encoder
model = joblib.load("model.pkl")
le = joblib.load("encoder.pkl")

# Load dataset for dashboard
data = pd.read_csv("new_file.csv")

# User database file
USERS_DB = 'users.json'

# Initialize users database if it doesn't exist
if not os.path.exists(USERS_DB):
    with open(USERS_DB, 'w') as f:
        json.dump({}, f)

def load_users():
    """Load users from JSON file"""
    with open(USERS_DB, 'r') as f:
        return json.load(f)

def save_users(users):
    """Save users to JSON file"""
    with open(USERS_DB, 'w') as f:
        json.dump(users, f, indent=4)

def login_required(f):
    """Decorator to require login"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# ===========================
# AUTHENTICATION ROUTES
# ===========================

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login"""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        if not username or not password:
            return render_template('login.html', error='All fields are required')
        
        users = load_users()
        
        if username in users and check_password_hash(users[username]['password'], password):
            session['username'] = username
            return redirect(url_for('home'))
        else:
            return render_template('login.html', error='Invalid username or password')
    
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    """Handle user signup"""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        email = request.form.get('email', '').strip()
        
        # Validation
        if not username or not password or not email:
            return render_template('signup.html', error='All fields are required')
        
        if len(password) < 6:
            return render_template('signup.html', error='Password must be at least 6 characters')
        
        if password != confirm_password:
            return render_template('signup.html', error='Passwords do not match')
        
        users = load_users()
        
        if username in users:
            return render_template('signup.html', error='Username already exists')
        
        # Create new user
        users[username] = {
            'password': generate_password_hash(password),
            'email': email
        }
        save_users(users)
        
        return redirect(url_for('login'))
    
    return render_template('signup.html')

@app.route('/forgot-password')
def forgot_password():
    """Forgot password placeholder"""
    return render_template('forgot_password.html')

@app.route('/logout')
def logout():
    """Handle user logout"""
    session.clear()
    return redirect(url_for('login'))

# ===========================
# MAIN APP ROUTES
# ===========================

@app.route('/')
@login_required
def home():
    types = list(le.classes_)
    username = session.get('username')
    return render_template('index.html', types=types, username=username)

@app.route('/predict', methods=['POST'])
@login_required
def predict():
    try:
        t = le.transform([request.form['type']])[0]
        step = float(request.form['step'])
        amount = float(request.form['amount'])
        old_org = float(request.form['oldbalanceOrg'])
        new_org = float(request.form['newbalanceOrig'])
        old_dest = float(request.form['oldbalanceDest'])
        new_dest = float(request.form['newbalanceDest'])

        input_data = np.array([[t, step, amount, old_org,
                                new_org, old_dest, new_dest]])

        result = model.predict(input_data)[0]
        prob = model.predict_proba(input_data)[0][1]

        if result == 1:
            prediction = f"⚠️ Fraud Detected (Probability: {prob:.2f})"
            risk_level = "HIGH"
        else:
            prediction = f"✅ Safe Transaction (Probability: {prob:.2f})"
            risk_level = "LOW"

        return render_template('index.html',
                               prediction=prediction,
                               risk_level=risk_level,
                               types=list(le.classes_),
                               username=session.get('username'))

    except Exception as e:
        return render_template('index.html',
                               prediction="❌ Invalid Input",
                               types=list(le.classes_),
                               username=session.get('username'))


# -------------------------------
# DASHBOARD ROUTE
# -------------------------------
@app.route('/dashboard')
@login_required
def dashboard():

    total = len(data)
    fraud = data['isFraud'].sum()
    safe = total - fraud
    fraud_percent = (fraud / total) * 100

    # Transaction type distribution
    type_counts = data['type'].value_counts().to_dict()
    username = session.get('username')

    return render_template(
        'dashboard.html',
        total=total,
        fraud=fraud,
        safe=safe,
        fraud_percent=round(fraud_percent, 2),
        type_labels=list(type_counts.keys()),
        type_values=list(type_counts.values()),
        username=username
    )

if __name__ == "__main__":
    app.run(debug=True)