# DiagnoseAI - Radiology Reporting Application

DiagnoseAI is a Flask-based web application that streamlines the ultrasound image analysis workflow for healthcare professionals. The system allows users to upload ultrasound images with clinical notes, receive AI-generated preliminary draft reports using GPT-4o, and review/finalize reports within the application.

## Features

- Secure user authentication with bcrypt password hashing
- Ultrasound image upload with clinical notes
- AI-powered draft report generation using OpenAI GPT-4o
- Report review and editing interface
- PDF and text report downloads
- Containerized deployment with Docker

## Technology Stack

- **Backend**: Flask (Python)
- **Database**: PostgreSQL 15
- **Authentication**: Flask-Login with bcrypt
- **AI Integration**: OpenAI GPT-4o API
- **Containerization**: Docker & Docker Compose
- **PDF Generation**: ReportLab

## Quick Start

### Prerequisites

- Docker and Docker Compose
- OpenAI API key

### Setup

1. Clone the repository and navigate to the project directory:
   ```bash
   cd DiagnoseAI
   ```

2. Copy the environment file and configure your settings:
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` and add your OpenAI API key:
   ```
   OPENAI_API_KEY=your-openai-api-key-here
   ```

3. Build and start the application:
   ```bash
   docker-compose up --build
   ```

4. The application will be available at `http://localhost:5003`

### Database Setup

When running for the first time, you'll need to create the database tables:

1. Access the web container:
   ```bash
   docker-compose exec web bash
   ```

2. Run the database migration:
   ```bash
   flask db migrate -m "Initial migration"
   flask db upgrade
   ```

## Development Setup

### Local Development

1. Create a Python virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up environment variables:
   ```bash
   export FLASK_APP=diagnoseai.py
   export FLASK_ENV=development
   export DATABASE_URL=postgresql://diagnoseai_user:diagnoseai_pass@localhost:5432/diagnoseai
   export OPENAI_API_KEY=your-openai-api-key-here
   ```

4. Initialize the database (requires PostgreSQL running):
   ```bash
   flask db init
   flask db migrate -m "Initial migration"
   flask db upgrade
   ```

5. Run the application:
   ```bash
   # Option 1: Using the startup script (recommended)
   python run_server.py
   
   # Option 2: Direct execution
   python main.py
   
   # Option 3: Using Flask CLI (runs on default port 5000)
   flask run
   ```

   The application will be available at `http://localhost:5003`

## Project Structure

```
DiagnoseAI/
├── app/
│   ├── __init__.py              # Flask app factory
│   ├── models.py                # SQLAlchemy models
│   ├── auth.py                  # Authentication routes (to be implemented)
│   ├── main.py                  # Main application routes (to be implemented)
│   ├── ai_service.py            # OpenAI integration (to be implemented)
│   └── templates/               # HTML templates (to be implemented)
├── static/
│   └── uploads/                 # Uploaded images
├── migrations/                  # Database migrations
├── requirements.txt             # Python dependencies
├── Dockerfile                   # Docker configuration
├── docker-compose.yml           # Docker Compose configuration
├── config.py                    # Application configuration
└── diagnoseai.py               # Application entry point
```

## Database Models

### User
- id (Primary Key)
- username (Unique)
- email (Unique)
- password_hash
- created_at

### Case
- id (Primary Key)
- user_id (Foreign Key to User)
- image_filename
- image_path
- clinical_notes
- status
- created_at, updated_at

### Report
- id (Primary Key)
- case_id (Foreign Key to Case)
- draft_json (AI response)
- draft_text (Formatted AI text)
- final_text (User-edited final report)
- is_finalized
- created_at, updated_at

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `SECRET_KEY` | Flask secret key for sessions | `dev-secret-key-change-in-production` |
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://diagnoseai_user:diagnoseai_pass@localhost:5432/diagnoseai` |
| `OPENAI_API_KEY` | OpenAI API key for GPT-4o | Required |
| `UPLOAD_FOLDER` | Directory for uploaded files | `static/uploads` |
| `MAX_CONTENT_LENGTH` | Maximum file upload size | `16777216` (16MB) |

## Security Considerations

- Passwords are hashed using bcrypt
- File uploads are validated and stored securely
- OpenAI API key is stored as environment variable
- Session cookies are configured with security flags
- Input validation and sanitization on all forms

## License

This project is for educational and demonstration purposes.