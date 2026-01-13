# 🏥 DiagnoseAI - AI-Powered Radiology Reporting System

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.0.3-green.svg)](https://flask.palletsprojects.com/)
[![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4o-orange.svg)](https://openai.com/)
[![License](https://img.shields.io/badge/License-Educational-yellow.svg)](LICENSE)

DiagnoseAI is a comprehensive Flask-based web application designed to streamline ultrasound image analysis workflows for healthcare professionals. The system enables users to upload ultrasound images, receive AI-generated preliminary reports using GPT-4o, manage patient records, and conduct AI performance testing.

## ✨ Key Features

### 🔐 Authentication & User Management
- Secure user authentication with bcrypt password hashing
- Role-based access control
- Session management with Flask-Login

### 📊 Patient & Case Management
- Complete patient record management
- Multi-image case support (up to 4 images per case)
- Clinical notes and metadata tracking
- Case status workflow (pending, reviewed, finalized)

### 🤖 AI-Powered Analysis
- GPT-4o integration for ultrasound image analysis
- Automated preliminary report generation
- Support for multiple ultrasound views (Left Lobe TR, Portal Vein, etc.)
- Structured JSON and formatted text reports

### 📝 Report Management
- Interactive report editing interface
- Draft and final report versions
- PDF and text export capabilities
- Report history and versioning

### 🧪 AI Testing & Evaluation
- Dedicated AI testing module for performance evaluation
- Batch image testing capabilities
- Star rating system for AI accuracy
- Detailed test result analytics with images
- Test history and comparison tools

### 🌐 Flexible Deployment Options
- **Local Development**: SQLite database for quick setup
- **Network Access**: Share on local WiFi network
- **Internet Access**: ngrok integration for remote access
- **Production**: Docker, Kubernetes, AWS, Railway support

## 🚀 Quick Start

### Option 1: Local Development (Fastest)

```bash
# 1. Clone and navigate to the project
cd DiagnoseAI

# 2. Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env and add your OpenAI API key

# 5. Run the application
python run_local.py
```

Access at: **http://127.0.0.1:5003**  
Login: `admin` / `admin123`

### Option 2: Network Access (Share with Others)

```bash
# Start server accessible on your local network
python run_network.py
```

Share the displayed network URL with others on the same WiFi.

### Option 3: Internet Access (Remote Access)

```bash
# Install ngrok (one-time setup)
brew install ngrok/ngrok/ngrok
ngrok config add-authtoken YOUR_TOKEN

# Start with internet access
python run_internet.py
```

Share the generated public URL for worldwide access.

## 📋 Prerequisites

- **Python**: 3.9 or higher
- **Database**: SQLite (local) or PostgreSQL (production)
- **OpenAI API Key**: Required for AI features
- **Optional**: Docker, ngrok (for specific deployment modes)

## 🛠️ Technology Stack

| Category | Technology |
|----------|-----------|
| **Backend** | Flask 3.0.3, Python 3.9+ |
| **Database** | PostgreSQL 15 / SQLite |
| **Authentication** | Flask-Login, bcrypt |
| **AI Integration** | OpenAI GPT-4o API |
| **Image Processing** | Pillow 11.0.0 |
| **PDF Generation** | ReportLab 4.2.5 |
| **Frontend** | HTML5, CSS3, JavaScript |
| **Deployment** | Docker, Kubernetes, Gunicorn |

## 📁 Project Structure

```
DiagnoseAI/
├── app/                          # Main application package
│   ├── __init__.py              # Flask app factory
│   ├── models.py                # Database models (User, Patient, Case, Report)
│   ├── auth.py                  # Authentication routes
│   ├── main.py                  # Main application routes
│   ├── forms.py                 # WTForms form definitions
│   ├── ai_service.py            # OpenAI GPT-4o integration
│   └── templates/               # Jinja2 HTML templates
│       ├── base.html            # Base template
│       ├── auth/                # Authentication templates
│       └── main/                # Main app templates
├── static/                       # Static assets
│   └── uploads/                 # Uploaded ultrasound images
├── tests/                        # Test suite
│   ├── conftest.py              # Pytest configuration
│   ├── test_auth.py             # Authentication tests
│   ├── test_upload.py           # Upload functionality tests
│   ├── test_ai_service.py       # AI service tests
│   └── test_ai_integration.py   # Integration tests
├── scripts/                      # Utility scripts
│   ├── batch_ai_test.py         # Batch AI testing
│   ├── check_network.py         # Network diagnostics
│   ├── test_api_key.py          # API key validation
│   ├── debug_env.py             # Environment debugging
│   ├── migrate_db.py            # Database migration
│   ├── create_admin_user.py     # Admin user creation
│   └── clear_port.py            # Port management
├── deployment/                   # Deployment configurations
│   ├── docker/                  # Docker configs
│   │   ├── Dockerfile
│   │   └── docker-compose.yml
│   ├── kubernetes/              # Kubernetes manifests
│   │   ├── deployment.yaml
│   │   ├── service.yaml
│   │   └── ingress.yaml
│   └── nginx/                   # Nginx configurations
├── docs/                         # Documentation
│   ├── LOCAL_SETUP.md           # Local development guide
│   ├── NETWORK_SETUP.md         # Network access guide
│   ├── INTERNET_ACCESS.md       # Internet access guide
│   ├── DEPLOYMENT.md            # Production deployment
│   ├── AI_TESTING_GUIDE.md      # AI testing documentation
│   ├── POSTGRESQL_SETUP.md      # PostgreSQL setup
│   └── aws-deploy.md            # AWS deployment guide
├── database/                     # Database scripts
│   ├── init-db.sql              # Database initialization
│   └── create-tables.sql        # Table creation scripts
├── migrations/                   # Alembic database migrations
├── instance/                     # Instance-specific files (SQLite DB)
├── .env.example                  # Environment template
├── .env.production               # Production environment template
├── requirements.txt              # Python dependencies
├── config.py                     # Application configuration
├── main.py                       # Application entry point
├── run_local.py                  # Local development runner
├── run_network.py                # Network access runner
├── run_internet.py               # Internet access runner
└── README.md                     # This file
```

## 🗄️ Database Models

### User
- `id`: Primary key
- `username`: Unique username
- `email`: Unique email address
- `password_hash`: Bcrypt hashed password
- `created_at`: Account creation timestamp

### Patient
- `id`: Primary key
- `name`: Patient full name
- `date_of_birth`: Patient DOB
- `medical_record_number`: Unique MRN
- `contact_info`: Contact information
- `created_at`: Record creation timestamp

### Case
- `id`: Primary key
- `patient_id`: Foreign key to Patient
- `user_id`: Foreign key to User (creator)
- `clinical_notes`: Clinical observations
- `status`: Case status (pending/reviewed/finalized)
- `image_paths`: JSON array of image paths (up to 4)
- `created_at`, `updated_at`: Timestamps

### Report
- `id`: Primary key
- `case_id`: Foreign key to Case
- `draft_json`: Raw AI response JSON
- `draft_text`: Formatted AI-generated text
- `final_text`: User-edited final report
- `is_finalized`: Finalization status
- `created_at`, `updated_at`: Timestamps

### AITestResult
- `id`: Primary key
- `user_id`: Foreign key to User
- `image_filename`: Test image filename
- `image_path`: Path to test image
- `view_type`: Ultrasound view type
- `ai_response_json`: Raw AI analysis
- `ai_response_text`: Formatted analysis
- `rating`: User rating (1-5 stars)
- `comments`: User feedback
- `created_at`: Test timestamp

## ⚙️ Configuration

### Environment Variables

Create a `.env` file based on `.env.example`:

```bash
# Flask Configuration
SECRET_KEY=your-secret-key-change-in-production
FLASK_APP=main.py
FLASK_ENV=development

# Database Configuration
# SQLite (Local Development)
DATABASE_URL=sqlite:////path/to/DiagnoseAI/instance/diagnoseai.db

# PostgreSQL (Production)
# DATABASE_URL=postgresql://user:password@host:5432/diagnoseai

# OpenAI API Configuration
OPENAI_API_KEY=sk-your-openai-api-key-here

# File Upload Configuration
UPLOAD_FOLDER=static/uploads
MAX_CONTENT_LENGTH=16777216  # 16MB
```

### Database Setup

#### SQLite (Local Development)
```bash
# Automatic setup on first run
python run_local.py
```

#### PostgreSQL (Production)
```bash
# 1. Create database
createdb diagnoseai

# 2. Run migrations
flask db upgrade

# 3. Create admin user
python scripts/create_admin_user.py
```

## 🧪 Testing

### Run All Tests
```bash
pytest
```

### Run Specific Test Suites
```bash
# Authentication tests
pytest tests/test_auth.py

# Upload functionality
pytest tests/test_upload.py

# AI service tests
pytest tests/test_ai_service.py

# Integration tests
pytest tests/test_ai_integration.py
```

### AI Performance Testing
```bash
# Interactive AI testing
python scripts/batch_ai_test.py

# Or use the web interface: AI Testing → Test Results
```

## 📚 Documentation

Comprehensive guides are available in the `docs/` directory:

- **[LOCAL_SETUP.md](docs/LOCAL_SETUP.md)** - Complete local development setup
- **[NETWORK_SETUP.md](docs/NETWORK_SETUP.md)** - Share on local network
- **[INTERNET_ACCESS.md](docs/INTERNET_ACCESS.md)** - Remote access with ngrok
- **[DEPLOYMENT.md](docs/DEPLOYMENT.md)** - Production deployment guide
- **[AI_TESTING_GUIDE.md](docs/AI_TESTING_GUIDE.md)** - AI testing and evaluation
- **[POSTGRESQL_SETUP.md](docs/POSTGRESQL_SETUP.md)** - PostgreSQL configuration
- **[aws-deploy.md](docs/aws-deploy.md)** - AWS deployment instructions

## 🚢 Deployment Options

### Docker
```bash
cd deployment/docker
docker-compose up -d
```

### Kubernetes
```bash
kubectl apply -f deployment/kubernetes/
```

### Railway
```bash
# One-click deploy using railway.json
railway up
```

### AWS
```bash
# See docs/aws-deploy.md for detailed instructions
./deployment/aws-deploy.sh
```

## 🔒 Security Features

- ✅ Bcrypt password hashing
- ✅ CSRF protection on all forms
- ✅ Secure session management
- ✅ File upload validation
- ✅ SQL injection prevention (SQLAlchemy ORM)
- ✅ XSS protection (Jinja2 auto-escaping)
- ✅ Environment-based secrets management
- ✅ HTTPS support in production

## 🤝 Contributing

This is an educational project. Contributions, issues, and feature requests are welcome!

## 📄 License

This project is for educational and demonstration purposes.

## 🙏 Acknowledgments

- OpenAI for GPT-4o API
- Flask community for excellent documentation
- Healthcare professionals for domain expertise

## 📞 Support

For issues, questions, or suggestions:
- Check the documentation in `docs/`
- Review existing issues on GitHub
- Create a new issue with detailed information

---

**Built with ❤️ for healthcare professionals**
