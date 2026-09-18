# Chat-App

A real-time chat application built with Flask, Flask-SocketIO, SQLite, HTML, CSS, and JavaScript.

---

# Requirements

You can run this project in two ways.

## Option 1: Docker

You need:

* Git
* Docker
* Docker Compose

For **Windows and macOS**, Docker Desktop is required.

For **Linux**, Docker Engine and Docker Compose are sufficient. Docker Desktop is not required.



---

## Option 2: uv

You need:

* Git
* Python
* uv

Docker is **not required** when using this method.

---

# Environment Variables

Before running the application using either method, create a `.env` file in the root directory of the project.

Your project should contain:

```text
Chat-App/
├── .env
├── Dockerfile
├── compose.yaml
├── pyproject.toml
├── uv.lock
├── app.py
└── ...
```

Add your secret key to `.env`:

```env
SECRET_KEY="your-secret-key-here"
```

Replace `your-secret-key-here` with your own secret key.

For example:

```env
SECRET_KEY="a-long-random-secret-key"
```

Do **not** commit your `.env` file to GitHub.

Make sure `.env` is included in `.gitignore`:

```gitignore
.env
```

---

# Running with Docker

## 1. Clone the repository

```bash
git clone https://github.com/Aryanpatil2502/Chat-App
cd Chat-App
```

## 2. Create the `.env` file

Create `.env` in the root directory and add:

```env
SECRET_KEY="your-secret-key-here"
```

## 3. Start the application

```bash
docker compose up --build
```

Docker will build the image using the project's `Dockerfile` and start the application.

Once the application is running, open:

```text
http://localhost:5000
```

## 4. Stop the application

```bash
docker compose down
```

---

# Running with uv

## 1. Clone the repository

```bash
git clone https://github.com/Aryanpatil2502/Chat-App
cd Chat-App
```

## 2. Create the `.env` file

Create `.env` in the root directory and add:

```env
SECRET_KEY="your-secret-key-here"
```

## 3. Install dependencies

Run:

```bash
uv sync
```

`uv` will create the virtual environment and install the dependencies specified by the project.

## 4. Start the application

```bash
uv run app.py
```

Once the application is running, open:

```text
http://localhost:5000
```

---

# If Docker Is Not Installed

## Windows

Install Docker Desktop and start it.

Then verify:

```powershell
docker --version
docker compose version
```

## macOS

Install Docker Desktop and start it.

Then verify:

```bash
docker --version
docker compose version
```

## Ubuntu 

Install Docker Engine and Docker Compose:

```bash
sudo apt update
sudo apt install docker.io docker-compose-v2
```

Start Docker:

```bash
sudo systemctl enable --now docker
```

Verify:

```bash
docker --version
docker compose version
```

If Docker requires `sudo`, use:

```bash
sudo docker compose up --build
```

---



---

# If uv Is Not Installed

## Windows

Open PowerShell and run:

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Restart PowerShell and verify:

```powershell
uv --version
```

---

## macOS

Run:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Restart your terminal and verify:

```bash
uv --version
```

---

## Ubuntu 
If `curl` is not installed:

```bash
sudo apt update
sudo apt install curl
```

Install `uv`:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Restart your terminal or run:

```bash
source ~/.bashrc
```

Verify:

```bash
uv --version
```

---

# SQLite Database

This application uses SQLite.

You do not need to manually create the database if it does not already exist. The application will initialize the database when required.

When running the application with Docker, make sure the Docker volume configured in `compose.yaml` is not deleted if you want to preserve your existing database.

---
