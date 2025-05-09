
# Django Project

This is a simple Django project setup. It is built with Python and the Django framework.

## Table of Contents

- [Installation](#installation)
- [Setup](#setup)
- [Usage](#usage)
- [Contributing](#contributing)
- [License](#license)

## Installation

### Prerequisites

1. Python 3.x
2. Django 3.x or higher
3. pip (Python package manager)

### Steps

1. Clone the repository:
    ```bash
    git clone <repository_url>
    ```

2. Navigate to the project directory:
    ```bash
    cd server
    ```

3. Create and activate a virtual environment:
    ```bash
    python3 -m venv venv
    source venv/bin/activate  # For Linux/Mac
    venv/scripts/activate     # For Windows
    ```

4. Install the required dependencies:
    ```bash
    pip install -r requirements.txt
    ```

## Setup

1. Apply migrations:
    ```bash
    python manage.py migrate
    ```

2. Create a superuser to access the admin panel:
    ```bash
    python manage.py createsuperuser
    ```

3. Run the development server:
    ```bash
    python manage.py runserver
    ```

4. Navigate to `http://127.0.0.1:8000/` in your browser.

## Usage

1. Access the Django application by visiting `http://127.0.0.1:8000/`.
2. Log in to the Django admin panel at `http://127.0.0.1:8000/admin` using the superuser credentials.

## Contributing

We welcome contributions! Please fork the repository, create a new branch, and submit a pull request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
