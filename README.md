# Pathfinder - Career Guidance Web Application

## Overview

Pathfinder is a comprehensive career counseling web application designed to help students discover their perfect career path after 10th grade. The application uses intelligent algorithms to analyze students' interests, skills, hobbies, and academic performance to provide personalized career recommendations.

## Features

### 🎯 Core Features
- **Smart Assessment**: Multi-factor analysis including interests, skills, hobbies, and academic performance
- **Performance Analysis**: Percentage-based career recommendations with alternative paths for lower scores
- **Personalized Matching**: Career suggestions based on unique user profiles
- **Comprehensive Database**: 500+ career options, 100+ courses, and 50+ skills categories

### 📊 Key Functionalities
- **Profile Assessment**: Complete user profile creation with detailed information
- **Career Recommendations**: Intelligent matching based on user data
- **Alternative Paths**: Solutions for students with lower academic performance
- **Course Guide**: Detailed information about educational courses and requirements
- **Skills Development**: Comprehensive skill assessment and development plans
- **Career Details**: In-depth information about specific careers

### 🎨 User Interface
- **Modern Design**: Beautiful, responsive UI with Bootstrap 5
- **6+ Pages**: Home, Assessment, Profile, Results, Courses, Skills, About, Contact
- **Interactive Elements**: Forms, modals, progress bars, and dynamic content
- **Mobile Responsive**: Works perfectly on all devices

## Technology Stack

- **Backend**: Python Flask
- **Frontend**: HTML5, CSS3, JavaScript, Bootstrap 5
- **Data**: CSV datasets for careers, skills, and courses
- **Icons**: Font Awesome 6
- **Styling**: Custom CSS with modern gradients and animations

## Installation & Setup

### Prerequisites
- Python 3.8 or higher
- pip (Python package installer)

### Step 1: Clone the Repository
```bash
git clone <repository-url>
cd pathfinder
```

### Step 2: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 3: Run the Application
```bash
python pathfinder_app.py
```

### Step 4: Access the Application
Open your web browser and navigate to:
```
http://localhost:5000
```

## Project Structure

```
pathfinder/
├── pathfinder_app.py          # Main Flask application
├── requirements.txt           # Python dependencies
├── README.md                 # Project documentation
├── datasets/                 # Data files
│   ├── careers_dataset.csv   # Career information
│   ├── skills_dataset.csv    # Skills data
│   └── courses_dataset.csv   # Course information
└── templates/               # HTML templates
    ├── base.html            # Base template
    ├── home.html            # Home page
    ├── assessment.html      # Assessment page
    ├── profile.html         # Profile form
    ├── results.html         # Results page
    ├── courses.html         # Courses page
    ├── skills.html          # Skills page
    ├── career_detail.html   # Career details
    ├── about.html           # About page
    └── contact.html         # Contact page
```

## Pages Overview

### 1. Home Page (`/`)
- Hero section with call-to-action
- Feature highlights
- Statistics and impact
- Quick start guide

### 2. Assessment Page (`/assessment`)
- Assessment tools overview
- Process explanation
- Features and benefits
- Tips for better assessment

### 3. Profile Page (`/profile`)
- Comprehensive user form
- Personal information
- Interests and skills selection
- Hobbies and personality assessment
- Academic performance input

### 4. Results Page (`/results`)
- Profile summary
- Performance analysis with progress bars
- Career recommendations with match scores
- Alternative paths for lower percentages
- Action buttons and tips

### 5. Courses Page (`/courses`)
- Course categories
- Detailed course information
- Search and filter options
- Course selection tips

### 6. Skills Page (`/skills`)
- Skill categories
- Detailed skill information
- Development plans
- Learning resources

### 7. Career Detail Page (`/career/<name>`)
- Comprehensive career information
- Skills required
- Related courses
- Career path progression
- Pros and cons

### 8. About Page (`/about`)
- Mission statement
- Features overview
- Team information
- Statistics and impact

### 9. Contact Page (`/contact`)
- Contact form
- Contact information
- Social media links
- FAQ section
- Office location

## Key Features Explained

### Percentage-Based Recommendations
The application analyzes the user's 10th grade percentage and provides:
- **High-Performance Careers** (80%+): Medical, Engineering, etc.
- **Standard Careers** (60%+): Business, Arts, Technology, etc.
- **Alternative Paths** (<60%): Vocational training, certifications, entrepreneurship

### Alternative Career Paths
For students with lower percentages, the system recommends:
- **Vocational Training**: Electrician, plumber, carpenter
- **IT Certification Courses**: Programming, web development, digital marketing
- **Entrepreneurship**: Start own business or freelancing
- **Government Skill Development**: Free or subsidized training programs

### Smart Assessment
The system considers multiple factors:
- **Interests**: Technology, Science, Arts, Business, Engineering, etc.
- **Skills**: Programming, Communication, Leadership, Creativity, etc.
- **Hobbies**: Reading, Gaming, Sports, Drawing, Music, etc.
- **Personality**: Introvert, Extrovert, Ambivert
- **Work Style**: Analytical, Creative, Leadership, Patient, Precise, Social

## Data Structure

### Careers Dataset
- Career name, category, description
- Required skills and education
- Salary range and job outlook
- Minimum percentage requirements
- Related interests and work styles

### Skills Dataset
- Skill name and category
- Description and difficulty level
- Learning time and resources
- Related careers

### Courses Dataset
- Course name and category
- Duration, eligibility, fees
- Top colleges and entrance exams
- Career prospects and minimum percentage

## Customization

### Adding New Careers
1. Edit `datasets/careers_dataset.csv`
2. Add new career entries with required fields
3. Update the recommendation logic in `pathfinder_app.py`

### Adding New Skills
1. Edit `datasets/skills_dataset.csv`
2. Add new skill entries with required fields
3. Update the skills display logic

### Modifying Recommendations
Edit the `get_career_recommendations()` function in `pathfinder_app.py` to customize the recommendation algorithm.

## Browser Compatibility

- Chrome (recommended)
- Firefox
- Safari
- Edge
- Mobile browsers

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is created for educational purposes as a mini project.

## Support

For support or questions:
- Email: info@pathfinder.com
- Phone: +91 98765 43210
- Visit the Contact page in the application

## Future Enhancements

- User authentication and profiles
- Advanced personality tests
- Integration with job portals
- Real-time career counseling chat
- Mobile app development
- AI-powered recommendation improvements
- Multi-language support

---

**Pathfinder** - Your trusted companion in career guidance and exploration! 🚀 "# career-guidance-project-" 
