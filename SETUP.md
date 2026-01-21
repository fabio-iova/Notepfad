# Notenpfad - Setup Guide

This guide explains how to initialize and run the Notenpfad application on a new computer.

## Prerequisites

Before starting, ensure you have the following installed on your machine:

- **Git**: For cloning the repository.
- **Python (3.9+)**: For the backend server.
- **Node.js (16+) & npm**: For the frontend application.

## 1. Project Initialization

First, get the project code onto your machine.

```bash
git clone <repository-url>
cd notenpfad
```

## 2. Backend Setup

The backend is built with FastAPI (Python).

1.  **Navigate to the backend directory:**
    ```bash
    cd backend
    ```

2.  **Create a virtual environment:**
    ```bash
    # Mac/Linux
    python3 -m venv venv

    # Windows
    python -m venv venv
    ```

3.  **Activate the virtual environment:**
    ```bash
    # Mac/Linux
    source venv/bin/activate

    # Windows (Command Prompt)
    venv\Scripts\activate.bat

    # Windows (PowerShell)
    .\venv\Scripts\Activate.ps1
    ```

4.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

5.  **Start the Backend Server:**
    ```bash
    python -m uvicorn main:app --reload --port 8000
    ```
    *The backend should now be running at `http://127.0.0.1:8000`. Keep this terminal window open.*

## 3. Frontend Setup

The frontend is built with React and Vite.

1.  **Open a new terminal window** (do not close the backend terminal).

2.  **Navigate to the frontend directory:**
    ```bash
    cd frontend
    ```
    *(If you are in the backend folder, go up one level first: `cd ../frontend`)*

3.  **Install dependencies:**
    ```bash
    npm install
    ```

4.  **Start the Frontend Server:**
    ```bash
    npm run dev
    ```

5.  **Access the Application:**
    Open your browser and navigate to the URL shown in the terminal (usually `http://localhost:5173`).

## Default Login Credentials

If the database is empty, the system will auto-generate these default users on startup:

- **Admin (Parent)**
    - Username: `admin`
    - Password: `****`
    - *Has access to Kids management and settings.*

- **Sole (Student)**
    - Username: `sole`
    - Password: `****`
    - *Standard student view.*

## Troubleshooting

- **Backend not starting?**
  - Ensure you activated the virtual environment (`(venv)` should appear in your terminal prompt).
  - Check if port 8000 is already in use.

- **Frontend not starting?**
  - Ensure you ran `npm install` first.
  - Check if port 5173 is in use.

- **Database Issues?**
  - If you want a fresh start, you can delete the `backend/database.db` file. It will be recreated automatically when you restart the backend.
