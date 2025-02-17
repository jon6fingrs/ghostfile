# GhostFile: Ephemeral File Upload Server

GhostFile is a **simple, temporary file upload server** that **automatically shuts down** after the first successful upload. It is **not** meant to be a long-running service but rather an on-demand tool.

## 🔥 Features
- **Simple to use**: Start the server, upload files, and it **shuts down automatically**.
- **Multiple file support**: Drag and drop or select multiple files before uploading.
- **Dark/Light Mode UI**: Aesthetic and easy to use.
- **No unnecessary persistence**: Designed for **on-demand use**, not for continuous hosting.
- **Works with Docker**: Run with or without containerization.

---

## 📦 Installation & Usage

### 🔧 Running Directly (Bare Metal)

#### 1️⃣ Install Dependencies
GhostFile requires **Python 3.7+** and Flask.

```bash
git clone https://github.com/jon6fingrs/ghostfile.git
cd ghostfile
pip install -r requirements.txt
```

#### 2️⃣ Start the Server
```bash
python3 upload_server.py
```
By default, this:
- Runs on **0.0.0.0:5000** (accessible on your local network).
- Saves uploaded files in **`./downloads`**.

#### 3️⃣ Upload Files
1. Open a browser and visit:
   ```
   http://127.0.0.1:5000
   ```
   OR use your **LAN IP** (e.g., `http://192.168.1.100:5000`).
2. Select or **drag & drop** files.
3. Click **Upload**.
4. The server **automatically shuts down** after handling the upload.

#### Optional Arguments:
- **Specify a different upload directory**:
  ```bash
  python3 upload_server.py --dir my_custom_folder
  ```
- **Change the port**:
  ```bash
  python3 upload_server.py --port 8080
  ```

---

## 🐳 Running with Docker

### 🚀 Running the Server
```bash
docker run --rm -t -v ./downloads:/app/downloads -p 5000:5000 thehelpfulidiot/ghostfile:latest
```

### 🔄 Explanation:
- `--rm` → Automatically removes the container after it stops.
- `-t` → Allocates a pseudo-TTY for better terminal output.
- `-v ./downloads:/app/downloads` → Mounts the **host directory** as the upload folder inside the container.
- `-p 5000:5000` → Exposes port **5000** (change as needed).

---

## ⚠️ Purpose & Limitations

GhostFile **is not** a persistent file upload service. It is meant for:
✔️ **Quick temporary file transfers**  
✔️ **One-time uploads**  
✔️ **On-demand use**  

Once a file is uploaded, **the server stops itself** to prevent unintended long-term use.

> **Do not** use GhostFile for unattended file hosting.

---

## 🤝 Contributing

Want to improve GhostFile?  
Fork the repo and submit a pull request!

---

## 📜 License
MIT License - Free to use, modify, and distribute.
