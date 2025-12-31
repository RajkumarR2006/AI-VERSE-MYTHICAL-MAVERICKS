# 🚀 AI-VERSE: Mythical Mavericks

**An Intelligent Financial RAG System for Startup Funding Analysis.**

> **Hackathon Submission** | **Team:** Mythical Mavericks

AI-VERSE is a Retrieval-Augmented Generation (RAG) system designed to demystify financial data. By combining a high-performance Next.js frontend with a Python-based RAG backend, we enable users to query complex startup funding datasets using natural language and receive accurate, cited, and hallucination-free answers.

---

## 🌟 Key Features

- **🧠 Intelligent Retrieval:** Uses advanced semantic search to find relevant financial records from large CSV datasets.
- **✅ Zero-Hallucination Protocol:** Implements a 3-layer verification system to ensure answers are strictly grounded in the provided data.
- **⚡ High-Speed Inference:** Optimized query pipeline achieving <0.2s average latency.
- **📊 Dynamic Evaluation:** Includes a dedicated evaluation module (`evaluate_rag_system.py`) to benchmark answer quality against ground truth.
- **🌐 Modern UI:** A responsive, interactive dashboard built with Next.js 14 and Tailwind CSS.

---

## 🛠️ Tech Stack

### **Frontend** (`/funding-frontend`)
- **Framework:** Next.js 14 (App Router)
- **Language:** TypeScript
- **Styling:** Tailwind CSS
- **State Management:** React Hooks

### **Backend** (`/gema-rag`)
- **Language:** Python 3.10+
- **AI Model:** LLaMA-3 (via Groq API)
- **Embeddings:** SentenceTransformers (HuggingFace)
- **Server:** FastAPI / Uvicorn (Local Inference Engine)
- **Data Processing:** Pandas & NumPy

### **Development Tools**
- **IDE:** VS Code (Visual Studio Code)
- **Version Control:** Git & GitHub
- **Tunneling:** Cloudflare Tunnel

---

## 📂 Project Structure

This is a **monorepo** containing both the client and server applications:

```
AI-VERSE-MYTHICAL-MAVERICKS/
├── 📂 funding-frontend/      # Next.js Client Application
│   ├── app/                  # Frontend Pages & Components
│   └── public/               # Static Assets
│
├── 📂 gema-rag/              # Python RAG Backend
│   ├── data/                 # Raw Dataset (CSVs) & Index Files
│   ├── src/                  # Core Logic (answer_question.py, evaluation)
│   └── .env                  # API Keys (Not included in repo)
│
└── 📄 README.md              # Project Documentation
```

---

## 🚀 Getting Started

Follow these steps to run the project locally using VS Code.

### **Step 1: Backend Setup (Python)**

Open the `gema-rag` folder in VS Code terminal:

```bash
cd gema-rag
```

Create a virtual environment (optional but recommended):

```bash
python -m venv venv
.\venv\Scripts\activate   # On Windows
source venv/bin/activate # On macOS/Linux
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Create a `.env` file in the `gema-rag` folder and add your API key:

```
GROQ_API_KEY=your_actual_api_key_here
```

Run the backend server (ensure your main script exposes an API or run the CLI demo):

```bash
python src/answer_question.py
```

### **Step 2: Frontend Setup (Next.js)**

Open a new terminal in VS Code and navigate to the frontend folder:

```bash
cd funding-frontend
```

Install Node dependencies:

```bash
npm install
```

Run the development server:

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

---

## 🌐 Networking Setup (Cloudflare Tunnel)

To enable the Next.js frontend to communicate securely with the local FastAPI backend (and to demonstrate the project live), we utilize Cloudflare Tunnel.

### **Why We Use It**

We use the Cloudflare executable (`cloudflared`) to create a secure, high-performance tunnel that exposes our local inference engine (localhost:8000) to the public internet. This provides three critical benefits:

- **HTTPS Encryption:** Automatically provides a secure SSL endpoint, which is often required by modern frontend frameworks and browser security policies.
- **Seamless Integration:** Bridges the gap between our local Python backend and the Next.js frontend without requiring complex router port forwarding.
- **Production Simulation:** Allows us to demonstrate the system in a live environment that mimics cloud hosting, with zero deployment latency.

### **Installation & Setup**

> **Note:** The executable file is NOT included in this repository to keep the download size small.

1. **Download:** Download the `cloudflared-windows-amd64.exe` from the [official Cloudflare downloads page](https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/).

2. **Rename:** Rename the downloaded file to `cloudflared.exe`.

3. **Placement:** Place the file in the root directory of this project (the folder containing `src/`, `data/`, and `README.md`).

4. **Run:** Open a terminal in the root folder and execute:

```bash
.\cloudflared.exe tunnel --url http://127.0.0.1:8000
```

5. **Connect:** Copy the `.trycloudflare.com` URL provided in the terminal and update your frontend configuration with this new endpoint.

---


## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details

---

## 🤝 Contributors

[Rajkumar R](https://github.com/RajkumarR2006) | Srishanth S | [Suman Maitreya M](https://github.com/Suman-Maitreya) | S Ajay Vikram 

---

## 📧 Contact

For questions or feedback about this project, please reach out to the Mythical Mavericks team.
