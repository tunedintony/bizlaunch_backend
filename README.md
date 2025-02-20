# Django Project Setup

Follow these steps to set up your Django project:

## 1. Create a Python Environment

Create a new Python environment using an appropriate version of Python (e.g., Python 3.9):

```bash
python3 -m venv venv
# Activate the environment:
# On Unix or macOS:
source venv/bin/activate
# On Windows:
venv\Scripts\activate
```

## 2. Install Requirements

Install the project dependencies:

```bash
pip install -r requirements.txt
```

## 3. Run Django Project

Start the Django development server:

```bash
python manage.py runserver
```

## 4. Install and Run Pre-commit Hooks

Install pre-commit hooks for code formatting and linting:

```bash
pip install pre-commit
pre-commit install
```

Run pre-commit hooks before committing changes:

```bash
pre-commit run --all-files
```

## 5. Install and Run Redis (if needed)

If your project requires Redis for caching or message queueing, install and run it:

On Ubuntu/Debian:

```bash
sudo apt-get update
sudo apt-get install redis-server
```

On macOS (using Homebrew):

```bash
brew install redis
```

Start the Redis server:

```bash
redis-server
```

## 6. Run Celery Worker (if needed)

If your project uses Celery for asynchronous task processing, start the Celery worker:

```bash
celery -A config worker --loglevel=info
```
