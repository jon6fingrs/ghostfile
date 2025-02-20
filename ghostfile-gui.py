#!/usr/bin/env python3
import os
import time
import argparse
import threading
import socket
import sys
import tkinter as tk
from tkinter import filedialog
from tkinter.scrolledtext import ScrolledText
import shutil

# -----------------------------------------------------------------------------
# Preliminary argument parsing for the --gui flag.
# This flag takes precedence over terminal detection.
# -----------------------------------------------------------------------------
pre_parser = argparse.ArgumentParser(add_help=False)
pre_parser.add_argument("--gui", choices=["true", "false"], help="Force GUI mode (true) or CLI mode (false)")
pre_args, remaining_args = pre_parser.parse_known_args()

if pre_args.gui == "true":
    mode = "gui"
elif pre_args.gui == "false":
    mode = "cli"
else:
    mode = "gui" if not sys.stdout.isatty() else "cli"

# Remove the --gui flag from sys.argv for further parsing.
sys.argv = [sys.argv[0]] + remaining_args

# -----------------------------------------------------------------------------
# GhostFile Server Code
# -----------------------------------------------------------------------------

# Optionally use psutil for robust network interface listing.
try:
    import psutil
except ImportError:
    psutil = None

from flask import Flask, request, send_from_directory, Response
from werkzeug.serving import make_server

def get_lan_ips():
    """
    Return a list of LAN IP addresses by scanning network interfaces.
    Ignores loopback and common virtual interfaces.
    """
    ips = set()
    if psutil:
        for interface, snics in psutil.net_if_addrs().items():
            if any(virt in interface.lower() for virt in ["docker", "veth", "loopback"]):
                continue
            for snic in snics:
                if snic.family == socket.AF_INET:
                    ip = snic.address
                    if ip.startswith("127."):
                        continue
                    octets = ip.split('.')
                    try:
                        if (ip.startswith("10.")) or (ip.startswith("192.168.")) or (
                            ip.startswith("172.") and 16 <= int(octets[1]) <= 31):
                            ips.add(ip)
                    except (IndexError, ValueError):
                        pass
    else:
        try:
            hostname = socket.gethostname()
            for ip in socket.gethostbyname_ex(hostname)[2]:
                if ip.startswith("127."):
                    continue
                octets = ip.split('.')
                try:
                    if (ip.startswith("10.")) or (ip.startswith("192.168.")) or (
                        ip.startswith("172.") and 16 <= int(octets[1]) <= 31):
                        ips.add(ip)
                except (IndexError, ValueError):
                    pass
        except Exception:
            pass
    return list(ips)

# Create the Flask app.
app = Flask(__name__)
http_server = None   # This will hold the server instance.
UPLOAD_DIR = None    # Will be set in CLI mode or via the GUI.

@app.route("/")
def serve_index():
    """Serve index.html from the script's directory."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    return send_from_directory(script_dir, "index.html")

@app.route("/upload", methods=["POST"])
def upload():
    """
    Handle uploaded files: save them to UPLOAD_DIR, print their paths immediately,
    then schedule a shutdown.
    """
    uploaded_files = request.files.getlist("files")
    saved_paths = []
    for f in uploaded_files:
        if f and f.filename:
            save_path = os.path.abspath(os.path.join(UPLOAD_DIR, f.filename))
            f.save(save_path)
            saved_paths.append(save_path)
    if saved_paths:
        print("[*] Files received:", flush=True)
        for path in saved_paths:
            print(path, flush=True)
    else:
        print("[*] No valid files received.", flush=True)
    threading.Thread(target=delayed_shutdown).start()
    response_text = "File(s) uploaded successfully. The server will now shut down...\n"
    if saved_paths:
        response_text += "\n".join(saved_paths)
    return Response(response_text, mimetype="text/plain")

def delayed_shutdown():
    """Wait briefly, then shut down the server."""
    time.sleep(1)
    if http_server:
        print("[*] Shutting down the server gracefully...", flush=True)
        http_server.shutdown()

def run_server(host, port):
    """
    Create a WSGI server via make_server, print status messages,
    and serve forever. This call blocks until shutdown.
    """
    global http_server
    http_server = make_server(host, port, app)
    print(f"[*] Server is running on http://{host}:{port}", flush=True)
    if host == "0.0.0.0":
        lan_ips = get_lan_ips()
        if lan_ips:
            print("[*] Accessible on the following LAN addresses:", flush=True)
            for ip in lan_ips:
                print(f"    http://{ip}:{port}", flush=True)
    http_server.serve_forever()
    print("[*] Server has shut down. Exiting...", flush=True)

def start_ghostfile_server(host, port, upload_dir):
    """
    Set UPLOAD_DIR, ensure the directory exists, and start the server.
    Used by both CLI and GUI modes.
    """
    global UPLOAD_DIR
    UPLOAD_DIR = os.path.join(os.getcwd(), upload_dir)
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    print(f"[*] Upload directory is set to: {UPLOAD_DIR}", flush=True)
    run_server(host, port)

def main():
    """
    CLI entry point:
      Parse command-line arguments and run the ghostfile server.
    """
    # Determine default upload directory based on where the script is run from.
    script_dir = os.path.dirname(os.path.abspath(__file__))
    working_dir = os.getcwd()
    if script_dir == working_dir:
        default_upload_dir = "downloads"
    else:
        default_upload_dir = "."
    parser = argparse.ArgumentParser(
        description="A Flask file uploader that stops after handling an upload."
    )
    parser.add_argument("--dir", default=default_upload_dir,
                        help="Directory to save uploaded files (default: %(default)s).")
    parser.add_argument("--host", default="0.0.0.0",
                        help="Host/IP to bind to (default: %(default)s).")
    parser.add_argument("--port", default=5000, type=int,
                        help="Port to listen on (default: %(default)s).")
    args = parser.parse_args()
    start_ghostfile_server(args.host, args.port, args.dir)

# -----------------------------------------------------------------------------
# GUI Wrapper Code
# -----------------------------------------------------------------------------

class TextRedirector:
    """A simple stream that redirects writes to a Tkinter widget."""
    def __init__(self, widget):
        self.widget = widget
    def write(self, s):
        self.widget.insert(tk.END, s)
        self.widget.see(tk.END)
    def flush(self):
        pass

class GhostFileGUI:
    def __init__(self, master):
        self.master = master
        master.title("GhostFile GUI Wrapper")
        master.iconname("GhostFile GUI")
        
        # Upload Directory field
        tk.Label(master, text="Upload Directory:").grid(row=0, column=0, sticky="e", padx=5, pady=5)
        self.dir_entry = tk.Entry(master, width=50)
        self.dir_entry.grid(row=0, column=1, padx=5, pady=5)
        # GUI mode defaults to home directory.
        self.dir_entry.insert(0, os.path.expanduser("~"))
        self.dir_browse = tk.Button(master, text="Browse", command=self.browse_directory)
        self.dir_browse.grid(row=0, column=2, padx=5, pady=5)
        
        # Host field
        tk.Label(master, text="Host:").grid(row=1, column=0, sticky="e", padx=5, pady=5)
        self.host_entry = tk.Entry(master, width=50)
        self.host_entry.grid(row=1, column=1, padx=5, pady=5)
        self.host_entry.insert(0, "0.0.0.0")
        
        # Port field
        tk.Label(master, text="Port:").grid(row=2, column=0, sticky="e", padx=5, pady=5)
        self.port_entry = tk.Entry(master, width=50)
        self.port_entry.grid(row=2, column=1, padx=5, pady=5)
        self.port_entry.insert(0, "5000")
        
        # Start and Stop buttons
        self.start_button = tk.Button(master, text="Start Server", command=self.start_server)
        self.start_button.grid(row=3, column=0, padx=5, pady=5)
        self.stop_button = tk.Button(master, text="Stop Server", command=self.stop_server, state=tk.DISABLED)
        self.stop_button.grid(row=3, column=1, padx=5, pady=5)
        
        # Terminal output area
        self.terminal = ScrolledText(master, height=15, width=80)
        self.terminal.grid(row=4, column=0, columnspan=3, padx=5, pady=5)
        
        # Redirect stdout/stderr to the terminal widget.
        sys.stdout = TextRedirector(self.terminal)
        sys.stderr = TextRedirector(self.terminal)
        
        self.server_thread = None

    def browse_directory(self):
        # Determine initial directory: use current text if valid; otherwise, use home directory.
        current_text = self.dir_entry.get().strip()
        if os.path.isdir(current_text):
            initial_dir = current_text
        else:
            initial_dir = os.path.expanduser("~")
        dir_path = filedialog.askdirectory(title="Select Upload Directory", initialdir=initial_dir)
        if dir_path:
            self.dir_entry.delete(0, tk.END)
            self.dir_entry.insert(0, dir_path)

    def start_server(self):
        upload_dir = self.dir_entry.get().strip() or os.path.expanduser("~")
        host = self.host_entry.get().strip() or "0.0.0.0"
        port = int(self.port_entry.get().strip() or "5000")
        self.server_thread = threading.Thread(
            target=start_ghostfile_server, args=(host, port, upload_dir), daemon=True
        )
        self.server_thread.start()
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)

    def stop_server(self):
        global http_server
        if http_server:
            http_server.shutdown()
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        print("Server stopped.", flush=True)

# -----------------------------------------------------------------------------
# Main Entry Point
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    if "--gui" in sys.argv:
        sys.argv.remove("--gui")
        root = tk.Tk(className="GhostFileGUI")
        root.title("GhostFile GUI Wrapper")
        root.iconname("GhostFile GUI")
        gui = GhostFileGUI(root)
        root.mainloop()
    else:
        if mode == "gui":
            root = tk.Tk(className="GhostFileGUI")
            root.title("GhostFile GUI Wrapper")
            root.iconname("GhostFile GUI")
            gui = GhostFileGUI(root)
            root.mainloop()
        else:
            main()
