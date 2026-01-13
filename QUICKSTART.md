# 🚀 DiagnoseAI Quick Start Guide

Get DiagnoseAI running in under 5 minutes!

## Prerequisites

- Python 3.9+
- OpenAI API Key ([Get one here](https://platform.openai.com/api-keys))

## Installation

### 1. Clone & Setup

```bash
cd DiagnoseAI
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure

```bash
cp .env.example .env
```

Edit `.env` and add your OpenAI API key:
```
OPENAI_API_KEY=sk-your-actual-api-key-here
```

### 3. Run

```bash
python run_local.py
```

🎉 **Done!** Open http://127.0.0.1:5003

**Default Login:** `admin` / `admin123`

## Common Commands

| Task | Command |
|------|---------|
| **Local Development** | `python run_local.py` |
| **Network Access** | `python run_network.py` |
| **Internet Access** | `python run_internet.py` |
| **Run Tests** | `pytest` |
| **Check API Key** | `python scripts/test_api_key.py` |
| **Create Admin User** | `python scripts/create_admin_user.py` |

## Troubleshooting

### Port Already in Use
```bash
python scripts/clear_port.py
```

### API Key Issues
```bash
python scripts/debug_env.py
python scripts/test_api_key.py
```

### Network Problems
```bash
python scripts/check_network.py
```

### Database Issues
```bash
# Reset database
rm instance/diagnoseai.db
python run_local.py  # Will recreate automatically
```

## Next Steps

- 📖 Read [docs/LOCAL_SETUP.md](docs/LOCAL_SETUP.md) for detailed setup
- 🌐 See [docs/NETWORK_SETUP.md](docs/NETWORK_SETUP.md) to share with others
- 🧪 Check [docs/AI_TESTING_GUIDE.md](docs/AI_TESTING_GUIDE.md) for AI testing
- 🚢 Review [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) for production deployment

## Features Overview

### Patient Management
1. Click **"Patients"** → **"New Patient"**
2. Enter patient details
3. Save and manage patient records

### Case Management
1. Click **"Cases"** → **"New Case"**
2. Select patient
3. Upload ultrasound images (up to 4)
4. Add clinical notes
5. Generate AI report

### AI Testing
1. Click **"AI Testing"**
2. Upload test images
3. Select view type
4. Analyze and rate AI performance
5. View test history and results

## Support

- 📚 Full documentation in `docs/` folder
- 🐛 Issues? Check existing GitHub issues
- 💡 Questions? Create a new issue

---

**Happy diagnosing! 🏥**
