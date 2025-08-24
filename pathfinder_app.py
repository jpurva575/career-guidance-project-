from flask import Flask, render_template, request, redirect, url_for, flash, session
import pandas as pd
import numpy as np
import os
from datetime import datetime
import joblib
import hashlib
import sqlite3
from functools import wraps

app = Flask(__name__)
app.secret_key = 'pathfinder_secret_key_2024'

# Load datasets
def load_datasets():
    careers_df = pd.read_csv('datasets/careers_dataset.csv')
    skills_df = pd.read_csv('datasets/skills_dataset.csv')
    courses_df = pd.read_csv('datasets/courses_dataset.csv')
    return careers_df, skills_df, courses_df

# Initialize datasets
try:
    careers_df, skills_df, courses_df = load_datasets()
except:
    careers_df = pd.DataFrame()
    skills_df = pd.DataFrame()
    courses_df = pd.DataFrame()

# Load ML model and encoders
MODEL_PATH = 'ml_model/career_predictor.pkl'
clf = None
mlb_interests = mlb_skills = mlb_hobbies = le_personality = le_work_style = le_career = None

def load_ml_model():
    global clf, mlb_interests, mlb_skills, mlb_hobbies, le_personality, le_work_style, le_career
    try:
        ml_bundle = joblib.load(MODEL_PATH)
        clf = ml_bundle['model']
        mlb_interests = ml_bundle['mlb_interests']
        mlb_skills = ml_bundle['mlb_skills']
        mlb_hobbies = ml_bundle['mlb_hobbies']
        le_personality = ml_bundle['le_personality']
        le_work_style = ml_bundle['le_work_style']
        le_career = ml_bundle['le_career']
        print('ML model loaded successfully!')
        return True
    except Exception as e:
        print('ML model not loaded:', e)
        return False

# Load the model
load_ml_model()

# Database initialization
def init_db():
    conn = sqlite3.connect('pathfinder.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            age INTEGER,
            education_level TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            predicted_career TEXT,
            profile_data TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    conn.commit()
    conn.close()

# Initialize database
init_db()

# Authentication decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Password hashing
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# User authentication functions
def get_user_by_email(email):
    conn = sqlite3.connect('pathfinder.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
    user = cursor.fetchone()
    conn.close()
    return user

def create_user(first_name, last_name, email, password, age, education_level):
    conn = sqlite3.connect('pathfinder.db')
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO users (first_name, last_name, email, password, age, education_level)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (first_name, last_name, email, hash_password(password), age, education_level))
        conn.commit()
        user_id = cursor.lastrowid
        conn.close()
        return user_id
    except sqlite3.IntegrityError:
        conn.close()
        return None

def save_user_result(user_id, predicted_career, profile_data):
    conn = sqlite3.connect('pathfinder.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO user_results (user_id, predicted_career, profile_data)
        VALUES (?, ?, ?)
    ''', (user_id, predicted_career, str(profile_data)))
    conn.commit()
    conn.close()

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = get_user_by_email(email)
        
        if user and user[4] == hash_password(password):  # user[4] is the password field
            session['user_id'] = user[0]
            session['user_name'] = f"{user[1]} {user[2]}"
            session['user_email'] = user[3]
            flash('Welcome back! You have successfully logged in.', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password. Please try again.', 'error')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        email = request.form.get('email')
        age = request.form.get('age')
        education_level = request.form.get('education_level')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        # Validation
        if not all([first_name, last_name, email, age, education_level, password, confirm_password]):
            flash('All fields are required.', 'error')
            return render_template('register.html')
        
        if password != confirm_password:
            flash('Passwords do not match.', 'error')
            return render_template('register.html')
        
        if len(password) < 8:
            flash('Password must be at least 8 characters long.', 'error')
            return render_template('register.html')
        
        # Check if user already exists
        existing_user = get_user_by_email(email)
        if existing_user:
            flash('Email already registered. Please use a different email or login.', 'error')
            return render_template('register.html')
        
        # Create user
        user_id = create_user(first_name, last_name, email, password, age, education_level)
        
        if user_id:
            session['user_id'] = user_id
            session['user_name'] = f"{first_name} {last_name}"
            session['user_email'] = email
            flash('Account created successfully! Welcome to Pathfinder.', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Registration failed. Please try again.', 'error')
    
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out successfully.', 'success')
    return redirect(url_for('home'))

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

@app.route('/my-results')
@login_required
def my_results():
    # Get user's previous results from database
    conn = sqlite3.connect('pathfinder.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT predicted_career, profile_data, created_at 
        FROM user_results 
        WHERE user_id = ? 
        ORDER BY created_at DESC
    ''', (session['user_id'],))
    results = cursor.fetchall()
    conn.close()
    
    return render_template('my_results.html', results=results)

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/assessment')
@login_required
def assessment():
    return render_template('assessment.html')

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        session['user_profile'] = {
            'name': request.form.get('name'),
            'age': request.form.get('age'),
            'education_level': request.form.get('education_level'),
            'percentage': float(request.form.get('percentage', 0)),
            'interests': request.form.getlist('interests'),
            'skills': request.form.getlist('skills'),
            'hobbies': request.form.getlist('hobbies'),
            'personality': request.form.get('personality'),
            'work_style': request.form.get('work_style')
        }
        return redirect(url_for('results'))
    return render_template('profile.html')

@app.route('/submit_profile', methods=['POST'])
@login_required
def submit_profile():
    profile = {
        'name': request.form.get('name'),
        'age': int(request.form.get('age', 16)),
        'education_level': request.form.get('education_level'),
        'percentage': float(request.form.get('percentage', 0)),
        'interests': request.form.getlist('interests'),
        'skills': request.form.getlist('skills'),
        'hobbies': request.form.getlist('hobbies'),
        'personality': request.form.get('personality'),
        'work_style': request.form.get('work_style'),
    }
    quiz = [int(request.form.get(f'quiz_q{i}', 3)) for i in range(1, 11)]
    for i, val in enumerate(quiz, 1):
        profile[f'quiz_q{i}'] = val
    data = {
        'age': profile['age'],
        'education_level': profile['education_level'],
        'percentage': profile['percentage'],
        'interests': profile['interests'],
        'skills': profile['skills'],
        'hobbies': profile['hobbies'],
        'personality': profile['personality'],
        'work_style': profile['work_style'],
    }
    for i in range(1, 11):
        data[f'quiz_q{i}'] = profile[f'quiz_q{i}']
    if clf and all([mlb_interests, mlb_skills, mlb_hobbies, le_personality, le_work_style, le_career]):
        try:
            X_interests = mlb_interests.transform([data['interests']])
            X_skills = mlb_skills.transform([data['skills']])
            X_hobbies = mlb_hobbies.transform([data['hobbies']])
            X_personality = le_personality.transform([data['personality']])
            X_work_style = le_work_style.transform([data['work_style']])
            X_all = np.hstack([
                [[data['age'], data['percentage']]],
                X_interests,
                X_skills,
                X_hobbies,
                X_personality.reshape(1, -1),
                X_work_style.reshape(1, -1),
                [[data[f'quiz_q{i}'] for i in range(1, 11)]]
            ])
            pred = clf.predict(X_all)[0]
            career = le_career.inverse_transform([pred])[0]
        except Exception as e:
            print(f"ML prediction failed: {e}")
            career = get_fallback_career_recommendation(data)
    else:
        career = get_fallback_career_recommendation(data)
    session['user_profile'] = profile
    session['predicted_career'] = career
    
    # Save result to database
    save_user_result(session['user_id'], career, profile)
    
    return redirect(url_for('results'))

@app.route('/results')
@login_required
def results():
    profile = session.get('user_profile')
    predicted_career = session.get('predicted_career')
    recommendations = []
    alternative_paths = []
    engineering_alternatives = None
    
    if predicted_career and predicted_career != "Unknown":
        # Get career details for the predicted career
        career_details = get_career_details(predicted_career)
        
        recommendations = [{
            'name': predicted_career,
            'match_score': 95,
            'description': career_details.get('description', 'This is your best-fit career path based on your profile and quiz.'),
            'salary_range': career_details.get('salary_range', '₹3-15 LPA'),
            'requirements': career_details.get('education', 'See details')
        }]
        
        # Check if student wants engineering with lower percentage
        if (profile and 
            profile.get('percentage', 0) >= 45 and 
            profile.get('percentage', 0) < 60 and
            ('Engineering' in profile.get('interests', []) or 
             'Technology' in profile.get('interests', []) or
             predicted_career == 'Engineering - Alternative Paths Available')):
            
            engineering_alternatives = get_engineering_alternative_paths(profile.get('percentage', 0))
        
        # Add general alternative paths for lower percentages
        elif profile and profile.get('percentage', 0) < 60:
            alternative_paths = [
                {
                    'name': 'Vocational Training',
                    'description': 'Short-term skill development programs',
                    'duration': '6-12 months',
                    'cost': '₹10,000-50,000',
                    'job_prospects': 'Good'
                },
                {
                    'name': 'IT Certification',
                    'description': 'Professional IT certifications',
                    'duration': '3-6 months',
                    'cost': '₹5,000-25,000',
                    'job_prospects': 'Excellent'
                },
                {
                    'name': 'Entrepreneurship',
                    'description': 'Start your own business',
                    'duration': 'Ongoing',
                    'cost': 'Varies',
                    'job_prospects': 'High potential'
                }
            ]
    
    return render_template('results.html', 
                         profile=profile, 
                         predicted_career=predicted_career, 
                         recommendations=recommendations, 
                         alternative_paths=alternative_paths,
                         engineering_alternatives=engineering_alternatives)

@app.route('/career/<career_name>')
def career_detail(career_name):
    career_info = get_career_details(career_name)
    return render_template('career_detail.html', career=career_info)

@app.route('/courses')
def courses():
    all_courses = get_all_courses()
    return render_template('courses.html', courses=all_courses)

@app.route('/skills')
def skills():
    all_skills = get_all_skills()
    return render_template('skills.html', skills=all_skills)

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/predict', methods=['POST'])
def predict():
    data = request.json
    # Extract and preprocess input
    age = data.get('age', 16)
    percentage = data.get('percentage', 70)
    interests = data.get('interests', [])
    skills = data.get('skills', [])
    hobbies = data.get('hobbies', [])
    personality = data.get('personality', 'Introvert')
    work_style = data.get('work_style', 'Analytical')
    quiz = [data.get(f'quiz_q{i}', 3) for i in range(1, 11)]
    # Transform input
    X_interests = mlb_interests.transform([interests])
    X_skills = mlb_skills.transform([skills])
    X_hobbies = mlb_hobbies.transform([hobbies])
    X_personality = le_personality.transform([personality])
    X_work_style = le_work_style.transform([work_style])
    X_all = np.hstack([
        [[age, percentage]],
        X_interests,
        X_skills,
        X_hobbies,
        X_personality.reshape(1, -1),
        X_work_style.reshape(1, -1),
        [quiz]
    ])
    # Predict
    pred = clf.predict(X_all)[0]
    career = le_career.inverse_transform([pred])[0]
    return {'career_path': career}

def get_fallback_career_recommendation(data):
    """Get fallback career recommendation when ML model fails"""
    interests = data.get('interests', [])
    skills = data.get('skills', [])
    percentage = data.get('percentage', 70)
    education_level = data.get('education_level', '10th')
    personality = data.get('personality', 'Introvert')
    work_style = data.get('work_style', 'Analytical')
    
    # Different career paths based on education level
    if education_level == '10th':
        return get_10th_grade_career_recommendation(interests, skills, percentage)
    elif education_level == '12th':
        return get_12th_grade_career_recommendation(interests, skills, percentage)
    else:
        # Default for other levels
        return get_general_career_recommendation(interests, skills, percentage)

def get_engineering_alternative_paths(percentage):
    """Get detailed alternative engineering paths for students with lower percentages"""
    if percentage >= 45 and percentage < 60:
        return {
            'primary_recommendation': 'Engineering - Alternative Paths Available',
            'description': f'With {percentage}% marks, you can still pursue engineering through alternative paths. Here are your options:',
            'alternative_paths': [
                {
                    'name': 'Diploma in Engineering',
                    'description': '3-year diploma course in various engineering branches',
                    'eligibility': '10th pass with 45%+',
                    'duration': '3 years',
                    'fees': '₹30,000-1,00,000 per year',
                    'entrance_exam': 'Polytechnic entrance exam (state-wise)',
                    'colleges': 'Government and Private Polytechnic colleges',
                    'advantages': [
                        'Direct admission to 2nd year B.Tech after diploma',
                        'Practical hands-on training',
                        'Lower fees compared to B.Tech',
                        'Good job opportunities after completion'
                    ],
                    'branches': [
                        'Diploma in Computer Engineering',
                        'Diploma in Mechanical Engineering', 
                        'Diploma in Civil Engineering',
                        'Diploma in Electrical Engineering',
                        'Diploma in Electronics & Communication'
                    ]
                },
                {
                    'name': 'ITI (Industrial Training Institute)',
                    'description': 'Vocational training in technical trades',
                    'eligibility': '10th pass with 35%+',
                    'duration': '1-2 years',
                    'fees': '₹5,000-20,000 per year',
                    'entrance_exam': 'Direct admission or merit-based',
                    'colleges': 'Government ITIs across India',
                    'advantages': [
                        'Free or very low fees in government ITIs',
                        'Practical skill development',
                        'Direct job placement assistance',
                        'Can pursue diploma after ITI'
                    ],
                    'trades': [
                        'Electrician',
                        'Fitter',
                        'Welder',
                        'Mechanic (Motor Vehicle)',
                        'Mechanic (Diesel)',
                        'Turner',
                        'Machinist'
                    ]
                },
                {
                    'name': 'Certificate Courses in Engineering',
                    'description': 'Short-term technical courses',
                    'eligibility': '10th pass',
                    'duration': '6 months - 1 year',
                    'fees': '₹10,000-50,000',
                    'entrance_exam': 'Direct admission',
                    'colleges': 'Private institutes and training centers',
                    'advantages': [
                        'Quick skill development',
                        'Lower investment',
                        'Can work while studying',
                        'Good foundation for further studies'
                    ],
                    'courses': [
                        'AutoCAD (Computer-Aided Design)',
                        'CNC Programming',
                        'PLC Programming',
                        'Welding Technology',
                        'Electrical Wiring',
                        'Refrigeration & AC'
                    ]
                },
                {
                    'name': 'Distance Learning Engineering',
                    'description': 'Part-time engineering courses',
                    'eligibility': '10th pass with 45%+',
                    'duration': '4-6 years',
                    'fees': '₹20,000-50,000 per year',
                    'entrance_exam': 'Direct admission',
                    'colleges': 'IGNOU, State Open Universities',
                    'advantages': [
                        'Can work while studying',
                        'Lower fees',
                        'Flexible schedule',
                        'Recognized degree'
                    ],
                    'limitations': [
                        'Limited practical exposure',
                        'May face challenges in job market',
                        'Less industry interaction'
                    ]
                }
            ],
            'success_stories': [
                'Many successful engineers started with diploma courses',
                'ITI graduates often get better practical skills',
                'Certificate courses can lead to good technical jobs',
                'Distance learning can be upgraded with experience'
            ],
            'next_steps': [
                'Research polytechnic colleges in your area',
                'Check ITI admission dates and requirements',
                'Explore certificate courses in your interest area',
                'Consider working part-time while studying',
                'Focus on practical skills and hands-on experience'
            ]
        }
    else:
        return {
            'primary_recommendation': 'Vocational Training - Skill Development',
            'description': f'With {percentage}% marks, focus on skill development and vocational training.',
            'alternative_paths': [
                {
                    'name': 'Basic Vocational Training',
                    'description': 'Foundation courses in technical skills',
                    'duration': '6 months - 1 year',
                    'fees': '₹5,000-15,000',
                    'focus': 'Basic technical skills and employability'
                }
            ]
        }

def get_10th_grade_career_recommendation(interests, skills, percentage):
    """Get career recommendations for 10th grade students"""
    if 'Technology' in interests or 'Programming' in skills or 'Engineering' in interests:
        if percentage >= 85:
            return 'Computer Science (PCM) - Engineering Path'
        elif percentage >= 75:
            return 'IT/Computer Applications - Diploma'
        elif percentage >= 60:
            return 'Web Development - Certificate Course'
        elif percentage >= 45:
            return 'Engineering - Alternative Paths Available'
        else:
            return 'Computer Operator - Vocational Training'
    
    elif 'Science' in interests:
        if percentage >= 90:
            return 'Medical (PCB) - Pre-Medical Path'
        elif percentage >= 80:
            return 'Engineering (PCM) - Technical Path'
        elif percentage >= 70:
            return 'Pharmacy - Diploma Course'
        elif percentage >= 45:
            return 'Engineering - Alternative Paths Available'
        else:
            return 'Lab Assistant - Vocational Training'
    
    elif 'Commerce' in interests or 'Business' in interests:
        if percentage >= 80:
            return 'Commerce (PCM/PCB) - Business Path'
        elif percentage >= 70:
            return 'Business Administration - Diploma'
        elif percentage >= 60:
            return 'Accounting - Certificate Course'
        else:
            return 'Retail Management - Vocational Training'
    
    elif 'Arts' in interests or 'Creativity' in skills:
        if percentage >= 75:
            return 'Design (Any Stream) - Creative Path'
        elif percentage >= 65:
            return 'Fashion Design - Diploma'
        elif percentage >= 55:
            return 'Graphic Design - Certificate Course'
        else:
            return 'Craft & Design - Vocational Training'
    
    else:
        # Default recommendations based on percentage
        if percentage >= 85:
            return 'Science (PCM) - Engineering Path'
        elif percentage >= 75:
            return 'Commerce - Business Path'
        elif percentage >= 65:
            return 'Arts - Creative Path'
        elif percentage >= 45:
            return 'Engineering - Alternative Paths Available'
        else:
            return 'Vocational Training - Skill Development'

def get_12th_grade_career_recommendation(interests, skills, percentage):
    """Get career recommendations for 12th grade students"""
    if 'Technology' in interests or 'Programming' in skills:
        if percentage >= 85:
            return 'B.Tech Computer Science'
        elif percentage >= 75:
            return 'BCA (Bachelor of Computer Applications)'
        elif percentage >= 65:
            return 'Diploma in Computer Engineering'
        else:
            return 'IT Certification Courses'
    
    elif 'Science' in interests:
        if percentage >= 90:
            return 'MBBS (Medical)'
        elif percentage >= 80:
            return 'B.Tech Engineering'
        elif percentage >= 70:
            return 'BSc (Bachelor of Science)'
        else:
            return 'Diploma in Science/Technology'
    
    elif 'Commerce' in interests or 'Business' in interests:
        if percentage >= 80:
            return 'BBA (Bachelor of Business Administration)'
        elif percentage >= 70:
            return 'B.Com (Bachelor of Commerce)'
        elif percentage >= 60:
            return 'Diploma in Business Management'
        else:
            return 'Certificate in Business Skills'
    
    elif 'Arts' in interests or 'Creativity' in skills:
        if percentage >= 75:
            return 'B.Des (Bachelor of Design)'
        elif percentage >= 65:
            return 'BA (Bachelor of Arts)'
        elif percentage >= 55:
            return 'Diploma in Design/Arts'
        else:
            return 'Certificate in Creative Arts'
    
    else:
        # Default recommendations based on percentage
        if percentage >= 85:
            return 'B.Tech Engineering'
        elif percentage >= 75:
            return 'BBA/B.Com'
        elif percentage >= 65:
            return 'BA/BSc'
        else:
            return 'Diploma/Certificate Courses'

def get_general_career_recommendation(interests, skills, percentage):
    """Get general career recommendations for other education levels"""
    if 'Technology' in interests or 'Programming' in skills:
        if percentage >= 80:
            return 'Software Engineer'
        elif percentage >= 60:
            return 'Web Developer'
        else:
            return 'IT Support Specialist'
    
    elif 'Science' in interests:
        if percentage >= 85:
            return 'Medical Doctor'
        elif percentage >= 70:
            return 'Pharmacist'
        else:
            return 'Lab Technician'
    
    elif 'Engineering' in interests or 'Technical Skills' in skills:
        if percentage >= 75:
            return 'Mechanical Engineer'
        elif percentage >= 60:
            return 'Civil Engineer'
        else:
            return 'Technician'
    
    elif 'Business' in interests or 'Leadership' in skills:
        if percentage >= 70:
            return 'Business Manager'
        elif percentage >= 60:
            return 'Sales Executive'
        else:
            return 'Customer Service Representative'
    
    elif 'Arts' in interests or 'Creativity' in skills:
        if percentage >= 65:
            return 'Graphic Designer'
        elif percentage >= 50:
            return 'UI/UX Designer'
        else:
            return 'Content Creator'
    
    else:
        # Default recommendations based on percentage
        if percentage >= 80:
            return 'Software Engineer'
        elif percentage >= 70:
            return 'Business Manager'
        elif percentage >= 60:
            return 'Web Developer'
        else:
            return 'Customer Service Representative'

def get_career_recommendations(profile):
    """Get career recommendations based on user profile"""
    recommendations = []
    
    # Simple recommendation logic based on interests and skills
    if 'Technology' in profile['interests'] or 'Programming' in profile['skills']:
        recommendations.append({
            'name': 'Software Engineer',
            'match_score': 85,
            'description': 'Develop software applications and systems',
            'salary_range': '₹4-15 LPA',
            'requirements': 'Computer Science degree, programming skills'
        })
    
    if 'Science' in profile['interests'] and profile['percentage'] >= 70:
        recommendations.append({
            'name': 'Medical Doctor',
            'match_score': 90,
            'description': 'Diagnose and treat patients',
            'salary_range': '₹8-25 LPA',
            'requirements': 'MBBS degree, NEET qualification'
        })
    
    if 'Business' in profile['interests'] or 'Leadership' in profile['skills']:
        recommendations.append({
            'name': 'Business Manager',
            'match_score': 80,
            'description': 'Manage business operations and teams',
            'salary_range': '₹6-20 LPA',
            'requirements': 'Business degree, leadership skills'
        })
    
    if 'Arts' in profile['interests'] or 'Creative' in profile['skills']:
        recommendations.append({
            'name': 'Graphic Designer',
            'match_score': 85,
            'description': 'Create visual designs and graphics',
            'salary_range': '₹3-12 LPA',
            'requirements': 'Design degree, creative skills'
        })
    
    if 'Engineering' in profile['interests'] and profile['percentage'] >= 75:
        recommendations.append({
            'name': 'Mechanical Engineer',
            'match_score': 88,
            'description': 'Design and build mechanical systems',
            'salary_range': '₹5-18 LPA',
            'requirements': 'Engineering degree, technical skills'
        })
    
    # Default recommendations if none match
    if not recommendations:
        recommendations = [
            {
                'name': 'General Career Counselor',
                'match_score': 70,
                'description': 'Help others find their career path',
                'salary_range': '₹3-10 LPA',
                'requirements': 'Psychology degree, counseling skills'
            }
        ]
    
    return recommendations

def get_alternative_paths(profile):
    """Get alternative career paths for students with lower percentages"""
    alternatives = []
    
    if profile['percentage'] < 60:
        alternatives.extend([
            {
                'name': 'Vocational Training',
                'description': 'Learn practical skills in trades like electrician, plumber, carpenter',
                'duration': '6 months - 2 years',
                'cost': '₹10,000 - 50,000',
                'job_prospects': 'High demand in construction and maintenance'
            },
            {
                'name': 'IT Certification Courses',
                'description': 'Learn programming, web development, or digital marketing',
                'duration': '3-12 months',
                'cost': '₹20,000 - 1,00,000',
                'job_prospects': 'Growing IT sector with good pay'
            },
            {
                'name': 'Entrepreneurship',
                'description': 'Start your own business or become a freelancer',
                'duration': 'Varies',
                'cost': '₹10,000 - 5,00,000',
                'job_prospects': 'Unlimited potential, requires dedication'
            },
            {
                'name': 'Government Skill Development',
                'description': 'Free or subsidized training programs by government',
                'duration': '3-6 months',
                'cost': 'Free to ₹5,000',
                'job_prospects': 'Government support and placement assistance'
            }
        ])
    
    return alternatives

def get_career_details(career_name):
    """Get detailed information about a specific career"""
    career_details = {
        # 10th Grade Career Paths
        'Computer Science (PCM) - Engineering Path': {
            'description': 'Choose PCM (Physics, Chemistry, Mathematics) in 12th to pursue engineering careers.',
            'skills_required': ['Mathematics', 'Physics', 'Chemistry', 'Problem Solving'],
            'education': '12th with PCM, then B.Tech',
            'salary_range': '₹4-20 LPA',
            'job_outlook': 'Excellent - High demand',
            'companies': ['Engineering Colleges', 'Universities'],
            'courses': ['B.Tech Computer Science', 'B.Tech IT', 'BCA']
        },
        'Medical (PCB) - Pre-Medical Path': {
            'description': 'Choose PCB (Physics, Chemistry, Biology) in 12th to pursue medical careers.',
            'skills_required': ['Biology', 'Chemistry', 'Physics', 'Patient Care'],
            'education': '12th with PCB, then MBBS/BDS',
            'salary_range': '₹8-30 LPA',
            'job_outlook': 'Excellent - Always in demand',
            'companies': ['Medical Colleges', 'Hospitals'],
            'courses': ['MBBS', 'BDS', 'BAMS', 'BHMS']
        },
        'Commerce (PCM/PCB) - Business Path': {
            'description': 'Choose Commerce stream in 12th to pursue business and management careers.',
            'skills_required': ['Mathematics', 'Business Studies', 'Economics', 'Leadership'],
            'education': '12th Commerce, then BBA/B.Com',
            'salary_range': '₹3-15 LPA',
            'job_outlook': 'Good - Growing demand',
            'companies': ['Business Schools', 'Universities'],
            'courses': ['BBA', 'B.Com', 'BMS', 'CA Foundation']
        },
        'Design (Any Stream) - Creative Path': {
            'description': 'Choose any stream in 12th to pursue creative and design careers.',
            'skills_required': ['Creativity', 'Art', 'Design Thinking', 'Communication'],
            'education': '12th any stream, then B.Des/BA',
            'salary_range': '₹3-12 LPA',
            'job_outlook': 'Good - Creative industry growth',
            'companies': ['Design Institutes', 'Art Colleges'],
            'courses': ['B.Des', 'BA Fine Arts', 'BA Design', 'Diploma in Design']
        },
        'Engineering - Alternative Paths Available': {
            'description': 'With your percentage, you can still pursue engineering through alternative paths like diploma courses, ITI, or certificate programs.',
            'skills_required': ['Mathematics', 'Physics', 'Problem Solving', 'Technical Aptitude'],
            'education': '10th pass with 45%+, then diploma/ITI/certificate courses',
            'salary_range': '₹2-8 LPA (after diploma/certificate)',
            'job_outlook': 'Good - Technical skills in high demand',
            'companies': ['Manufacturing Companies', 'Construction Firms', 'IT Companies', 'Government Departments'],
            'courses': ['Diploma in Engineering', 'ITI Courses', 'Technical Certificates', 'Distance Learning']
        },
        
        # 12th Grade Career Paths
        'B.Tech Computer Science': {
            'description': 'Bachelor of Technology in Computer Science - 4-year engineering degree.',
            'skills_required': ['Programming', 'Mathematics', 'Problem Solving', 'Logic'],
            'education': '12th PCM with good percentage',
            'salary_range': '₹4-20 LPA',
            'job_outlook': 'Excellent - High demand',
            'companies': ['TCS', 'Infosys', 'Wipro', 'Google', 'Microsoft'],
            'courses': ['B.Tech CS', 'B.Tech IT', 'BCA']
        },
        'MBBS (Medical)': {
            'description': 'Bachelor of Medicine and Bachelor of Surgery - 5.5-year medical degree.',
            'skills_required': ['Biology', 'Chemistry', 'Patient Care', 'Critical Thinking'],
            'education': '12th PCB with NEET qualification',
            'salary_range': '₹8-30 LPA',
            'job_outlook': 'Excellent - Always in demand',
            'companies': ['Hospitals', 'Medical Colleges', 'Research Institutes'],
            'courses': ['MBBS', 'BDS', 'BAMS', 'BHMS']
        },
        'BBA (Bachelor of Business Administration)': {
            'description': 'Bachelor of Business Administration - 3-year business management degree.',
            'skills_required': ['Leadership', 'Communication', 'Business Acumen', 'Analytics'],
            'education': '12th any stream with good percentage',
            'salary_range': '₹3-12 LPA',
            'job_outlook': 'Good - Growing demand',
            'companies': ['Corporate Companies', 'Startups', 'Consulting Firms'],
            'courses': ['BBA', 'BMS', 'B.Com', 'CA Foundation']
        },
        'B.Des (Bachelor of Design)': {
            'description': 'Bachelor of Design - 4-year design degree for creative careers.',
            'skills_required': ['Creativity', 'Design Thinking', 'Visual Communication', 'Art'],
            'education': '12th any stream with portfolio',
            'salary_range': '₹3-15 LPA',
            'job_outlook': 'Good - Creative industry growth',
            'companies': ['Design Studios', 'Advertising Agencies', 'Tech Companies'],
            'courses': ['B.Des', 'BA Design', 'Diploma in Design']
        },
        
        # General Career Paths
        'Software Engineer': {
            'description': 'Software engineers design, develop, and maintain software applications and systems.',
            'skills_required': ['Programming', 'Problem Solving', 'Teamwork', 'Communication'],
            'education': 'B.Tech in Computer Science or related field',
            'salary_range': '₹4-15 LPA',
            'job_outlook': 'Excellent - High demand',
            'companies': ['TCS', 'Infosys', 'Wipro', 'Google', 'Microsoft'],
            'courses': ['B.Tech Computer Science', 'BCA', 'MCA', 'Diploma in IT']
        },
        'Medical Doctor': {
            'description': 'Medical doctors diagnose and treat patients, providing healthcare services.',
            'skills_required': ['Medical Knowledge', 'Patient Care', 'Communication', 'Critical Thinking'],
            'education': 'MBBS degree from recognized medical college',
            'salary_range': '₹8-25 LPA',
            'job_outlook': 'Excellent - Always in demand',
            'companies': ['Hospitals', 'Clinics', 'Research Institutes', 'Private Practice'],
            'courses': ['MBBS', 'BDS', 'BAMS', 'BHMS']
        },
        'Business Manager': {
            'description': 'Business managers oversee operations and lead teams in organizations.',
            'skills_required': ['Leadership', 'Communication', 'Strategic Thinking', 'Problem Solving'],
            'education': 'MBA or Business Administration degree',
            'salary_range': '₹6-20 LPA',
            'job_outlook': 'Good - Growing demand',
            'companies': ['Corporate Companies', 'Startups', 'Consulting Firms'],
            'courses': ['MBA', 'BBA', 'B.Com', 'PGDM']
        }
    }
    
    return career_details.get(career_name, {
        'description': 'Career information not available.',
        'skills_required': [],
        'education': 'Varies',
        'salary_range': '₹3-10 LPA',
        'job_outlook': 'Good',
        'companies': [],
        'courses': []
    })

def get_all_courses():
    """Get all available courses"""
    return [
        # 12th Grade Courses
        {
            'name': 'B.Tech Computer Science',
            'duration': '4 years',
            'eligibility': '12th with PCM',
            'fees': '₹2-8 LPA',
            'careers': ['Software Engineer', 'Data Scientist', 'Web Developer']
        },
        {
            'name': 'MBBS',
            'duration': '5.5 years',
            'eligibility': '12th with PCB, NEET qualified',
            'fees': '₹10-50 LPA',
            'careers': ['Medical Doctor', 'Surgeon', 'Researcher']
        },
        {
            'name': 'BBA',
            'duration': '3 years',
            'eligibility': '12th in any stream',
            'fees': '₹2-8 LPA',
            'careers': ['Business Manager', 'Consultant', 'Entrepreneur']
        },
        {
            'name': 'B.Des (Design)',
            'duration': '4 years',
            'eligibility': '12th in any stream',
            'fees': '₹3-12 LPA',
            'careers': ['Graphic Designer', 'UI/UX Designer', 'Fashion Designer']
        },
        {
            'name': 'BCA',
            'duration': '3 years',
            'eligibility': '12th in any stream',
            'fees': '₹2-6 LPA',
            'careers': ['Software Developer', 'IT Professional', 'System Analyst']
        },
        {
            'name': 'B.Com',
            'duration': '3 years',
            'eligibility': '12th in any stream',
            'fees': '₹1-5 LPA',
            'careers': ['Accountant', 'Financial Analyst', 'Business Executive']
        },
        
        # 10th Grade Courses
        {
            'name': 'Diploma in Computer Engineering',
            'duration': '3 years',
            'eligibility': '10th pass',
            'fees': '₹1-3 LPA',
            'careers': ['Computer Technician', 'IT Support', 'Network Administrator']
        },
        {
            'name': 'Diploma in Business Management',
            'duration': '2 years',
            'eligibility': '10th pass',
            'fees': '₹1-2 LPA',
            'careers': ['Office Manager', 'Sales Executive', 'Administrative Assistant']
        },
        {
            'name': 'Certificate in Web Development',
            'duration': '6 months',
            'eligibility': '10th pass',
            'fees': '₹20,000-50,000',
            'careers': ['Web Developer', 'Frontend Developer', 'Freelancer']
        },
        {
            'name': 'Certificate in Graphic Design',
            'duration': '6 months',
            'eligibility': '10th pass',
            'fees': '₹15,000-40,000',
            'careers': ['Graphic Designer', 'Digital Artist', 'Content Creator']
        },
        {
            'name': 'Vocational Training - Electrician',
            'duration': '1 year',
            'eligibility': '10th pass',
            'fees': '₹10,000-30,000',
            'careers': ['Electrician', 'Maintenance Technician', 'Industrial Worker']
        },
        {
            'name': 'Vocational Training - Plumber',
            'duration': '1 year',
            'eligibility': '10th pass',
            'fees': '₹8,000-25,000',
            'careers': ['Plumber', 'Pipe Fitter', 'Maintenance Worker']
        }
    ]

def get_all_skills():
    """Get all available skills"""
    return [
        {
            'name': 'Programming',
            'category': 'Technical',
            'description': 'Ability to write and understand code',
            'careers': ['Software Engineer', 'Data Scientist', 'Web Developer']
        },
        {
            'name': 'Communication',
            'category': 'Soft Skills',
            'description': 'Effective verbal and written communication',
            'careers': ['Manager', 'Teacher', 'Sales Executive']
        },
        {
            'name': 'Leadership',
            'category': 'Management',
            'description': 'Ability to lead and motivate teams',
            'careers': ['Business Manager', 'Project Manager', 'Team Lead']
        },
        {
            'name': 'Creativity',
            'category': 'Artistic',
            'description': 'Ability to think creatively and innovatively',
            'careers': ['Designer', 'Artist', 'Content Creator']
        }
    ]

if __name__ == '__main__':
    app.run(debug=True, port=5000) 