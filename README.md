# SAS QA Translation Framework

## Project Description
A specialized tool for analyzing legacy SAS codebases to assess complexity, flag migration risks, and generate translation blueprints for modern platforms like Python/Pandas or SQL.

**What it does**: Automates the initial analysis and risk assessment of SAS code.
**Why it's useful**: Replaces manual, error-prone code review with structured automated analysis, saving significant time during migration projects.

## 🚀 Getting Started

### Prerequisites
- Python 3.10+
- Anaconda/Miniconda (recommended for environment management)
- Git

### Installation & Setup
1.  **Clone the repository**
    ```bash
    git clone https://github.com/regger-zz/sas-translator.git
    cd sas-translator
    ```
2.  **Backend Setup**
    ```bash
    cd backend
    conda create -n sas-backend-env python=3.10 -y
    conda activate sas-backend-env
    pip install -r requirements.txt
    ```
3.  **Frontend Setup**
    ```bash
    cd ../frontend
    conda create -n sas-frontend-clean python=3.10 -y
    conda activate sas-frontend-clean
    pip install -r requirements.txt
    ```

## 💻 Usage

1.  **Start the Backend Service**
    ```bash
    cd backend
    conda activate sas-backend-env
    uvicorn main:app --reload --port 8000
    ```
2.  **Start the Frontend Service** (in a new terminal)
    ```bash
    cd frontend
    conda activate sas-frontend-clean
    python dash_app.py
    ```
3.  **Open your browser** to `http://localhost:8050`
4.  Log in with the demo credentials (`demo` / `demo`).
5.  Upload a `.sas` file and generate your analysis blueprint.

## 🏗️ Architecture
This project uses a modern, decoupled microservices architecture:
- **Backend**: FastAPI application providing a REST API, integrated with a high-performance **Rust-based `sas-lexer`** for SAS code parsing.
- **Frontend**: Dash (Plotly) web application providing a secure, interactive user interface.
- **Communication**: The frontend and backend communicate via synchronous HTTP REST API calls.