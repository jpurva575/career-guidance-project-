import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MultiLabelBinarizer, LabelEncoder
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
import joblib

# Load dataset
DATA_PATH = '../datasets/careers_dataset.csv'
df = pd.read_csv(DATA_PATH)

# Preprocess features
categorical_cols = ['interests', 'skills', 'hobbies', 'personality', 'work_style']
quiz_cols = [f'quiz_q{i}' for i in range(1, 11)]

# Split comma-separated columns into lists
def split_col(col):
    return col.fillna('').apply(lambda x: [i.strip() for i in x.split(',') if i.strip()])

for col in ['interests', 'skills', 'hobbies']:
    df[col] = split_col(df[col])

# MultiLabelBinarizer for multi-valued categorical columns
mlb_interests = MultiLabelBinarizer()
mlb_skills = MultiLabelBinarizer()
mlb_hobbies = MultiLabelBinarizer()

X = df[['age', 'percentage', 'interests', 'skills', 'hobbies', 'personality', 'work_style'] + quiz_cols]
y = df['career_path']

# Transform features
X_interests = mlb_interests.fit_transform(X['interests'])
X_skills = mlb_skills.fit_transform(X['skills'])
X_hobbies = mlb_hobbies.fit_transform(X['hobbies'])

# Encode personality and work_style
le_personality = LabelEncoder()
le_work_style = LabelEncoder()
X_personality = le_personality.fit_transform(X['personality'])
X_work_style = le_work_style.fit_transform(X['work_style'])

# Combine all features
X_all = np.hstack([
    X[['age', 'percentage']].values,
    X_interests,
    X_skills,
    X_hobbies,
    X_personality.reshape(-1, 1),
    X_work_style.reshape(-1, 1),
    X[quiz_cols].values
])

# Encode target
le_career = LabelEncoder()
y_enc = le_career.fit_transform(y)

# Train/test split
X_train, X_test, y_train, y_test = train_test_split(X_all, y_enc, test_size=0.2, random_state=42)

# Train model
clf = RandomForestClassifier(n_estimators=200, random_state=42)
clf.fit(X_train, y_train)

# Save model and encoders
joblib.dump({
    'model': clf,
    'mlb_interests': mlb_interests,
    'mlb_skills': mlb_skills,
    'mlb_hobbies': mlb_hobbies,
    'le_personality': le_personality,
    'le_work_style': le_work_style,
    'le_career': le_career
}, 'career_predictor.pkl')

print('Model trained and saved as career_predictor.pkl')