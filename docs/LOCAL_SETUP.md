# DiagnoseAI - Local Development Setup

This guide will help you run DiagnoseAI locally on your laptop using SQLite database.

## Prerequisites

- Python 3.11+ 
- Virtual environment (already set up in `venv/`)
- OpenAI API key (optional for testing basic functionality)

## Quick Start

1. **Activate the virtual environment:**
   ```bash
   source venv/bin/activate
   ```

2. **Run the application:**
   ```bash
   python run_local.py
   ```

3. **Access the application:**
   - Open your browser to: http://127.0.0.1:5003
   - Login with: `admin` / `admin123`

## Configuration

The application is configured for local development with:

- **Database**: SQLite (`instance/diagnoseai.db`)
- **Environment**: Development mode with debug enabled
- **Upload folder**: `instance/uploads/`
- **Default admin user**: admin / admin123

## Environment Variables

The `.env` file contains:
```bash
SECRET_KEY=your-secret-key-change-in-production
FLASK_APP=main.py
FLASK_ENV=development
DATABASE_URL=sqlite:////Users/abdullahwaheed/Downloads/radiology-ai-application/DiagnoseAI/instance/diagnoseai.db
OPENAI_API_KEY=your-openai-api-key-here
UPLOAD_FOLDER=static/uploads
MAX_CONTENT_LENGTH=16777216
```

## Features Available

✅ **User Authentication** - Register, login, logout  
✅ **Patient Management** - Add and manage patients  
✅ **Case Management** - Create cases with ultrasound images  
✅ **Report Generation** - AI-powered draft reports (requires OpenAI API key)  
✅ **Report Editing** - Review and finalize reports  
✅ **File Downloads** - Export reports as PDF or text  

## Testing Without OpenAI API Key

You can test most functionality without an OpenAI API key:
- User registration and authentication
- Patient management
- Case creation and image upload
- Manual report creation and editing

AI-powered draft report generation requires a valid OpenAI API key.

## Database Management

### Reset Database
```bash
rm instance/diagnoseai.db
source venv/bin/activate
flask db upgrade
python scripts/create_admin_user.py
```

### Create Additional Users
```bash
source venv/bin/activate
python scripts/create_admin_user.py
```

## Troubleshooting

### Port 5003 in use
The application will automatically kill any process using port 5003.

### Database errors
If you encounter database errors, try resetting the database (see above).

### Missing dependencies
```bash
source venv/bin/activate
pip install -r requirements.txt
```

## Development

- **Debug mode**: Enabled by default
- **Auto-reload**: Changes to Python files will restart the server
- **Logs**: Displayed in the terminal
- **Database**: SQLite file at `instance/diagnoseai.db`

## Branch Information

This setup is on the `jan6` branch, configured specifically for local development with SQLite database instead of PostgreSQL.