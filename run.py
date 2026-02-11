"""
Application Entry Point

This script initializes and runs the DocEX Flask application.
It creates the application using the factory function and starts the development server.

Usage:
    python run.py

The script also ensures that all required directories and files exist
before starting the application.
"""

from app import create_app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True)