# Smart Telangana Government Services Assistant

## Project Overview
Smart Telangana Government Services Assistant is a student-developed web application built using Python and Flask. It helps users explore information about various Telangana Government services through a simple, organized and user-friendly interface.

## Features
- Explore 18 government service categories.
- Browse information about 53 government services.
- Search for government schemes and services.
- View detailed service information and related official portal links.
- User registration and login.
- Secure password hashing.
- Forgot password and password reset functionality.
- Save and remove favourite services.
- User profile management.
- CSRF protection for forms.
- Responsive user interface.

## Technologies Used
- **Backend:** Python, Flask
- **Frontend:** HTML, CSS
- **Database:** SQLite
- **Security:** Werkzeug password hashing, Flask-WTF CSRF protection
- **Tools:** Visual Studio Code, Git, GitHub

## Project Structure
```text
government-services-assistant/
│
├── app.py
├── database.py
├── .gitignore
│
├── templates/
│   ├── index.html
│   ├── category.html
│   ├── details.html
│   ├── results.html
│   ├── login.html
│   ├── register.html
│   ├── profile.html
│   ├── forgot_password.html
│   └── reset
