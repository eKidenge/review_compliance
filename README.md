# Review Compliance System

A Django-based web application for managing compliance review workflows, case records, data imports, user accounts, and audit activities through a centralized interface.

## Overview

The **Review Compliance System** provides a structured platform for organizing compliance-related cases and supporting review activities. It includes dedicated application modules for case management, data imports, dashboards, and audit functionality, alongside user account management and Django administration.

The project is built with Python and Django, using a modular application structure to keep its core functionality organized and maintainable.

## Key Features

- **User and Account Management** — User profiles, account administration, and account-related forms.
- **Role-Specific Dashboards** — Dedicated dashboard interfaces for administrators, clients, reviewers, and submitters.
- **Case Management** — Case listing, detailed case views, and supporting forms for managing case information.
- **Data Imports** — Import-related forms, services, and task modules for handling data ingestion workflows.
- **Audit Module** — A dedicated application for audit-related models and views.
- **Authentication** — Login, logout, and password-change functionality through Django's authentication system.
- **Administrative Interface** — Django Admin for managing registered application data and users.
- **Reusable Templates** — Shared base layouts, dashboard components, pagination, and error pages.

> The availability of individual permissions, automated audit logging, background task execution, and specific import formats depends on their implementation and configuration in the application.

## Technology Stack

- **Language:** Python
- **Web Framework:** Django
- **Database:** Determined by the project's Django database configuration
- **Frontend:** Django Templates, HTML, CSS, and JavaScript where implemented
- **Authentication:** Django authentication framework
- **Application Architecture:** Modular Django applications

## Project Structure

```text
review_compliance/
├── apps/
│   ├── audit/
│   │   ├── migrations/
│   │   ├── models.py
│   │   ├── urls.py
│   │   └── views.py
│   ├── cases/
│   │   ├── migrations/
│   │   ├── forms.py
│   │   ├── models.py
│   │   ├── urls.py
│   │   └── views.py
│   ├── dashboard/
│   │   ├── migrations/
│   │   ├── models.py
│   │   └── views.py
│   └── imports/
│       ├── migrations/
│       ├── forms.py
│       ├── services.py
│       ├── tasks.py
│       ├── models.py
│       ├── urls.py
│       └── views.py
├── review_compliance/
│   ├── settings.py
│   ├── urls.py
│   ├── asgi.py
│   └── wsgi.py
├── templates/
│   ├── accounts/
│   ├── cases/
│   ├── dashboard/
│   ├── errors/
│   ├── registration/
│   └── base.html
├── manage.py
└── README.md
```

*The tree above highlights the principal files and modules; it is not an exhaustive listing of every project file.*

## Getting Started

### Prerequisites

Install the following:

- Python 3.13 or a compatible Python version supported by the project's dependencies.
- Git.
- A terminal such as PowerShell, Command Prompt, or a Unix shell.

### 1. Clone the repository

```bash
git clone https://github.com/eKidenge/review_compliance.git
cd review_compliance
```

### 2. Create a virtual environment

**Windows PowerShell**

```powershell
python -m venv venv
.\venv\Scripts\python.exe -m pip install --upgrade pip
```

**Linux or macOS**

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

If the repository contains a `requirements.txt` file, install the dependencies with:

```bash
python -m pip install -r requirements.txt
```

On Windows, if you are using the virtual environment created above without activating it, run:

```powershell
.\venv\Scripts\python.exe -m pip install -r requirements.txt
```

If no dependency file exists yet, install Django and any additional packages required by the project. A dependency file should be maintained so other developers can reproduce the environment reliably.

### 4. Configure the environment

Review `review_compliance/settings.py` and configure the required environment variables, database connection, secret key, email settings, and other deployment-specific values as applicable.

Do not commit production secrets, passwords, API keys, or private environment files to version control.

### 5. Apply database migrations

```bash
python manage.py migrate
```

### 6. Create an administrator account

```bash
python manage.py createsuperuser
```

Follow the prompts to create the account.

### 7. Start the development server

```bash
python manage.py runserver
```

Open the application at:

http://127.0.0.1:8000/

For Windows, if the virtual environment is not activated, replace `python` with `.\venv\Scripts\python.exe` in the commands above.

## Application Routes

The following routes are exposed by the project URL configuration.

| Route | Purpose |
|---|---|
| `/` | Main dashboard entry point |
| `/admin/` | Django administration |
| `/imports/` | Data import module |
| `/cases/` | Case management module |
| `/audit/` | Audit module |
| `/accounts/login/` | Login |
| `/accounts/logout/` | Logout |
| `/accounts/password_change/` | Password change |

The exact pages accessible to each user depend on authentication, URL configuration, and the permissions implemented in the application.

## Development and Testing

Run Django's system checks before committing changes:

```bash
python manage.py check
```

Run the test suite:

```bash
python manage.py test
```

Create and review migrations after changing model definitions:

```bash
python manage.py makemigrations
python manage.py migrate
```

Run these commands from the directory containing `manage.py`.

## Security Considerations

Before deploying the application to production:

- Set `DEBUG = False`.
- Configure `ALLOWED_HOSTS` for the intended deployment domains.
- Store `SECRET_KEY` and other sensitive settings securely.
- Use HTTPS and secure cookie settings.
- Configure the production database and database credentials.
- Review authentication, authorization, and role-based access restrictions.
- Verify that audit records and imported data are protected against unauthorized access.
- Review file-upload validation and media-file access where applicable.
- Configure production static-file serving and error handling.
- Ensure development-only media serving is disabled in production.
- Keep dependencies updated and avoid committing credentials or local database files.

## Contributing

1. Fork the repository.
2. Create a feature branch.
3. Make your changes and add appropriate tests.
4. Run the Django system checks and test suite.
5. Commit your changes with a descriptive message.
6. Open a pull request describing the changes.

## License

No license has been specified in this repository's documentation. Add a `LICENSE` file before distributing the project under an open-source license.

## Maintainer

**Elisha Kidenge**

GitHub: [@eKidenge](https://github.com/eKidenge)

Repository: [review_compliance](https://github.com/eKidenge/review_compliance)
