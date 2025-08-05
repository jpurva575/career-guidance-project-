from flask import Flask, render_template, request, redirect, url_for, flash, session
import pandas as pd
import numpy as np
import os
from datetime import datetime
import joblib

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
try:
    ml_bundle = joblib.load(MODEL_PATH)
    clf = ml_bundle['model']
    mlb_interests = ml_bundle['mlb_interests']
    mlb_skills = ml_bundle['mlb_skills']
    mlb_hobbies = ml_bundle['mlb_hobbies']
    le_personality = ml_bundle['le_personality']
    le_work_style = ml_bundle['le_work_style']
    le_career = ml_bundle['le_career']
except Exception as e:
    clf = None
    mlb_interests = mlb_skills = mlb_hobbies = le_personality = le_work_style = le_career = None
    print('ML model not loaded:', e)

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/assessment')
def assessment():
    return render_template('assessment.html')

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if request.method == 'POST':
        session['user_profile'] = {
            'name': request.form.get('name'),
            'age': request.form.get('age'),
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
def submit_profile():
    profile = {
        'name': request.form.get('name'),
        'age': int(request.form.get('age', 16)),
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
        'percentage': profile['percentage'],
        'interests': profile['interests'],
        'skills': profile['skills'],
        'hobbies': profile['hobbies'],
        'personality': profile['personality'],
        'work_style': profile['work_style'],
    }
    for i in range(1, 11):
        data[f'quiz_q{i}'] = profile[f'quiz_q{i}']
    if clf:
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
    else:
        career = "Unknown"
    session['user_profile'] = profile
    session['predicted_career'] = career
    return redirect(url_for('results'))

@app.route('/results')
def results():
    profile = session.get('user_profile')
    predicted_career = session.get('predicted_career')
    recommendations = []
    alternative_paths = []
    if predicted_career:
        recommendations = [{
            'name': predicted_career,
            'match_score': 95,
            'description': 'This is your best-fit career path based on your profile and quiz.',
            'salary_range': 'Varies',
            'requirements': 'See details'
        }]
    return render_template('results.html', profile=profile, predicted_career=predicted_career, recommendations=recommendations, alternative_paths=alternative_paths)

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
        {
            'name': 'B.Tech Computer Science',
            'duration': '4 years',
            'eligibility': '10+2 with PCM',
            'fees': '₹2-8 LPA',
            'careers': ['Software Engineer', 'Data Scientist', 'Web Developer']
        },
        {
            'name': 'MBBS',
            'duration': '5.5 years',
            'eligibility': '10+2 with PCB, NEET qualified',
            'fees': '₹10-50 LPA',
            'careers': ['Medical Doctor', 'Surgeon', 'Researcher']
        },
        {
            'name': 'MBA',
            'duration': '2 years',
            'eligibility': 'Graduation in any field',
            'fees': '₹5-20 LPA',
            'careers': ['Business Manager', 'Consultant', 'Entrepreneur']
        },
        {
            'name': 'B.Des (Design)',
            'duration': '4 years',
            'eligibility': '10+2 in any stream',
            'fees': '₹3-12 LPA',
            'careers': ['Graphic Designer', 'UI/UX Designer', 'Fashion Designer']
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