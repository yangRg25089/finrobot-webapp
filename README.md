

# 🚀 FinRobot WebApp

A full-stack web application that visualizes and runs algorithmic trading strategies based on the [FinRobot](https://github.com/AI4Finance-Foundation/FinRobot) framework.

- **Backend**: FastAPI + FinRobot
- **Frontend**: React + Vite + Tailwind CSS

---

## 📁 Project Structure

```

finrobot-webapp/
├── backend/                # FastAPI backend
│   ├── main.py             # API entry
│   ├── tutorials\_wrapper/  # Wrapped strategies
│   └── ...
├── frontend/               # React + Tailwind + Vite
│   ├── src/                # UI logic
│   └── ...
├── requirements.txt        # Python dependencies
├── README.md
└── 概要设计.md              # Japanese design doc

````

---

## 🔧 Backend Setup (FastAPI + FinRobot)

### 1️⃣ Create conda environment

```bash
conda create --name finrobot python=3.10.14
conda activate finrobot
````

### 2️⃣ Clone FinRobot repo

```bash
git clone https://github.com/AI4Finance-Foundation/FinRobot.git
cd FinRobot
```

### 3️⃣ Install FinRobot

Install from PyPI (recommended):

```bash
cd ../finrobot-webapp/backend
pip install -U finrobot
```

Or install from source (if modifying internals):

```bash
pip install -e .
```

### 4️⃣ Install backend dependencies

```bash
pip install -r requirements.txt
```

---

## ⚙️ Frontend Setup (React + Tailwind + Vite)

```bash
cd frontend
npm install
npm run dev
```

Open: [http://localhost:5173](http://localhost:5173)

---

## 🚀 Backend Launch (Two Ways)

### ✅ Option A: Standard FastAPI run

```bash
cd backend
uvicorn main:app --reload --port 8000
```

Access API docs: [http://localhost:8000/docs](http://localhost:8000/docs)

---

### ✅ Option B: Use VSCode Launch Configuration

You can launch the backend directly from VSCode using `.vscode/launch.json`.


Make sure you're in the `finrobot` conda environment before starting.

---

## 📌 Notes

* Strategy scripts should be wrapped under `tutorials_wrapper/` with a unified interface:

  ```python
  def run(params) -> dict:
      return {
          "metrics": {...},
          "image_path": "/static/sma.png"
      }
  ```

* Output images go to: `backend/static/`

* Add your `OAI_CONFIG_LIST` and API keys under `backend/config_api_keys/`


---

## 🧾 License

MIT License
