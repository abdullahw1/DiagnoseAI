# Contributing to DiagnoseAI

Thank you for your interest in contributing to DiagnoseAI! This document provides guidelines and instructions for contributing.

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Coding Standards](#coding-standards)
- [Testing](#testing)
- [Submitting Changes](#submitting-changes)

## Code of Conduct

- Be respectful and inclusive
- Focus on constructive feedback
- Help others learn and grow
- Maintain professional communication

## Getting Started

### 1. Fork and Clone

```bash
# Fork the repository on GitHub
# Then clone your fork
git clone https://github.com/YOUR_USERNAME/DiagnoseAI.git
cd DiagnoseAI
```

### 2. Set Up Development Environment

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install development dependencies
pip install pytest pytest-flask black flake8 mypy
```

### 3. Configure Environment

```bash
cp .env.example .env
# Add your OpenAI API key to .env
```

### 4. Run Tests

```bash
pytest
```

## Development Workflow

### Branch Naming

- `feature/description` - New features
- `fix/description` - Bug fixes
- `docs/description` - Documentation updates
- `refactor/description` - Code refactoring
- `test/description` - Test additions/updates

### Example Workflow

```bash
# Create a new branch
git checkout -b feature/add-new-view-type

# Make your changes
# ... edit files ...

# Run tests
pytest

# Format code
black .

# Commit changes
git add .
git commit -m "Add support for new ultrasound view type"

# Push to your fork
git push origin feature/add-new-view-type

# Create Pull Request on GitHub
```

## Coding Standards

### Python Style

- Follow PEP 8 guidelines
- Use Black for code formatting: `black .`
- Use meaningful variable and function names
- Add docstrings to functions and classes

### Example

```python
def analyze_ultrasound_image(image_path: str, view_type: str) -> dict:
    """
    Analyze an ultrasound image using AI.
    
    Args:
        image_path: Path to the ultrasound image file
        view_type: Type of ultrasound view (e.g., 'Left Lobe TR')
    
    Returns:
        Dictionary containing AI analysis results
    
    Raises:
        ValueError: If image_path is invalid
        OpenAIError: If AI analysis fails
    """
    # Implementation here
    pass
```

### File Organization

- Keep files focused and single-purpose
- Place new utilities in appropriate folders:
  - `app/` - Core application code
  - `scripts/` - Utility scripts
  - `tests/` - Test files
  - `docs/` - Documentation

## Testing

### Writing Tests

```python
# tests/test_new_feature.py
import pytest
from app import create_app

def test_new_feature():
    """Test description."""
    app = create_app()
    with app.test_client() as client:
        response = client.get('/new-endpoint')
        assert response.status_code == 200
```

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_auth.py

# Run with coverage
pytest --cov=app tests/

# Run specific test
pytest tests/test_auth.py::test_login
```

## Submitting Changes

### Pull Request Process

1. **Update Documentation**
   - Update README.md if needed
   - Add/update docstrings
   - Update relevant docs in `docs/`

2. **Ensure Tests Pass**
   ```bash
   pytest
   ```

3. **Format Code**
   ```bash
   black .
   flake8 .
   ```

4. **Commit Messages**
   - Use clear, descriptive commit messages
   - Start with a verb (Add, Fix, Update, Remove)
   - Reference issues if applicable

   ```
   Add support for DICOM image format
   
   - Implement DICOM parser
   - Add tests for DICOM handling
   - Update documentation
   
   Fixes #123
   ```

5. **Create Pull Request**
   - Provide clear description of changes
   - Link related issues
   - Add screenshots for UI changes
   - Request review from maintainers

### PR Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation update
- [ ] Refactoring

## Testing
- [ ] All tests pass
- [ ] Added new tests
- [ ] Manual testing completed

## Checklist
- [ ] Code follows style guidelines
- [ ] Documentation updated
- [ ] No breaking changes
- [ ] Commit messages are clear
```

## Areas for Contribution

### High Priority

- 🐛 Bug fixes
- 📝 Documentation improvements
- ✅ Test coverage expansion
- 🔒 Security enhancements

### Feature Ideas

- Support for additional image formats (DICOM, TIFF)
- Multi-language support
- Advanced reporting features
- Integration with PACS systems
- Mobile-responsive improvements
- Batch processing capabilities

### Documentation Needs

- Video tutorials
- API documentation
- Deployment guides for more platforms
- Troubleshooting guides
- Best practices documentation

## Questions?

- Check existing issues and discussions
- Review documentation in `docs/`
- Create a new issue for questions
- Tag maintainers for urgent matters

## Recognition

Contributors will be recognized in:
- README.md contributors section
- Release notes
- Project documentation

Thank you for contributing to DiagnoseAI! 🏥
