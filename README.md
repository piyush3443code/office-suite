# OfficeSuite: Mission Control & Node Monitor

[![Django](https://img.shields.io/badge/Django-5.2+-green.svg)](https://www.djangoproject.com/)
[![Kubernetes](https://img.shields.io/badge/Kubernetes-Enabled-blue.svg)](https://kubernetes.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

OfficeSuite is a premium dashboard designed for monitoring telecom application servers (TAS) and Kubernetes clusters. It provides a sleek, modern interface for tracking pod statuses, metrics, and node health.

## 🚀 Features

- **Mission Control Dashboard**: Real-time monitoring of TAS pods.
- **Node Monitor**: Live status updates for Kubernetes nodes.
- **Secure Authentication**: Robust signup and login flows with OTP-based password recovery.
- **Sleek UI**: Modern, responsive design with a focus on visual clarity and user experience.
- **Docker Ready**: Fully containerized for easy deployment.

## 🛠 Tech Stack

- **Backend**: Python 3.10+, Django 5.2
- **Frontend**: Vanilla HTML5, CSS3, JavaScript
- **Infrastructure**: Kubernetes (kubectl integration), Docker
- **Database**: SQLite (Development)

## 🏗 Setup Instructions

### 1. Prerequisites
- Python 3.10 or higher
- `kubectl` configured with cluster access (optional, mock data provided)
- Docker & Docker Compose (optional)

### 2. Local Installation
```bash
# Clone the repository
git clone https://github.com/yourusername/officesuite.git
cd officesuite

# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Start the server
python manage.py runserver
```

### 3. Docker Deployment
```bash
docker-compose up --build
```

## 🔒 Security

- **Environment-ready**: Designed to use environment variables for sensitive settings.
- **CSRF Protection**: Standard Django security middleware enabled.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---
Built with ❤️ by [Your Name/Team]
