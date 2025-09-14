# Secure-Kanban-Board
This project is a desktop Kanban task manager built with Python, PyQt6, and Flask. It features a secure admin login system with bcrypt password hashing, JWT token-based authentication, and XML logging of user actions. The backend is implemented as a REST API with Flask to manage users, authentication, and secure data access.

## Key Features

- **Secure login and registration for admins using bcrypt**  
- **JWT tokenisation for protected endpoints**  
- **XML logging to track actions and events**  
- **Flask REST API backend with endpoints for user and session management**  
- **PyQt6 frontend providing a graphical Kanban board interface**

## Testing

- **Unit tests:** Verified core functions such as admin registration, login, and token generation
- **Static analysis:** Checked code with linters and type hints to catch potential issues
- **Functional testing:** Tested frontend interactions, REST API endpoints, and XML logging

## Build & Run

1. **Clone the repository**  
2. **Install dependencies**
- pip install Flask flask-jwt-extended bcrypt PyQt6 requests
3. ***Run the Flask backend**
- python path/to/flask_backend.py
4. **Run the PyQt6 frontend**
-python SkanbanBoard.py

## Future Improvements

- Deploy the multi-user system to a proper server for real-world use
- Replace JSON storage with a proper database for scalability
- Implement additional security features (password reset, rate limiting, HTTPS)

  

