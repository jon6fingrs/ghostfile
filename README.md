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

## 💾 Running as a Standalone Binary

If you don't want to install Python, you can use the **prebuilt binary**.

#### 1️⃣ **Determine Your CPU Architecture**
Run the following command to check your system type:

```bash
uname -m
```

You will see one of the following:
- **`x86_64`** → Use the `ghostfile` binary.
- **`aarch64`** (ARM64, e.g., Raspberry Pi, Apple M1/M2) → Use the `ghostfile-arm64` binary.

#### 2️⃣ **Download the Correct Binary**

##### 🖥️ For x86_64 (Intel/AMD):
```bash
wget $(curl -s https://api.github.com/repos/jon6fingrs/ghostfile/releases/latest | grep "browser_download_url" | grep "ghostfile\"$" | cut -d '"' -f 4)
```

##### 🍏 For ARM64 (Raspberry Pi, Apple Silicon, AWS Graviton):
```bash
wget -O ghostfile $(curl -s https://api.github.com/repos/jon6fingrs/ghostfile/releases/latest | grep "browser_download_url" | grep "ghostfile-arm64" | cut -d '"' -f 4)
```

#### 3️⃣ **Make It Executable**
```bash
chmod +x ghostfile  # Or ghostfile-arm64 depending on your system
```

#### 4️⃣ **Move the Binary to Your PATH**

To use `ghostfile` from anywhere in the terminal, move it to a directory in your system's `PATH`.

##### 🐧 **Ubuntu/Debian**
```bash
sudo mv ghostfile /usr/local/bin/
```

##### 🎩 **Fedora**
```bash
sudo mv ghostfile /usr/bin/
```

##### 📦 **Arch Linux**
```bash
sudo mv ghostfile /usr/local/bin/
```

After moving the file, **verify that it's accessible**:
```bash
ghostfile --help
```

#### 5️⃣ **Run It**
```bash
ghostfile  # Or ghostfile-arm64 on ARM systems
```

By default, the binary:
- Runs on `0.0.0.0:5000` (accessible on your local network).
- Saves uploaded files to current directory.

---

## 📖 Command-Line Usage (`--help` Output)

Once installed, you can check available options using:

```bash
ghostfile --help
```

Example output:
```
Usage: ghostfile [OPTIONS]

Options:
  --dir TEXT      Specify a custom upload directory (default: ./downloads)
  --port INTEGER  Specify a custom port (default: 5000)
  --help          Show this message and exit.
```
---

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

## 📸 Screenshot

Here's a preview of GhostFile's simple web interface:

![GhostFile Screenshot](https://github.com/jon6fingrs/ghostfile/raw/main/ghostfile_screenshot.png)

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
