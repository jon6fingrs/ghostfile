#!/usr/bin/env python3
import os
import time
import argparse
import threading
import socket
from flask import Flask, request, send_from_directory, Response
from werkzeug.serving import make_server

# Optional: Use psutil for a more robust network interface listing if available.
try:
    import psutil
except ImportError:
    psutil = None

def get_lan_ips():
    """
    Return a list of LAN IP addresses by scanning network interfaces.
    Ignores loopback addresses and (if possible) virtual interfaces.
    Only returns IPs that are likely accessible on the LAN.
    """
    ips = set()
    if psutil:
        for interface, snics in psutil.net_if_addrs().items():
            # Skip common virtual interfaces (adjust the filter as needed)
            if any(virt in interface.lower() for virt in ["docker", "veth", "loopback"]):
                continue
            for snic in snics:
                if snic.family == socket.AF_INET:
                    ip = snic.address
                    if ip.startswith("127."):
                        continue
                    octets = ip.split('.')
                    try:
                        # Check for common private LAN IP ranges
                        if (ip.startswith("10.")) or (ip.startswith("192.168.")) or (
                            ip.startswith("172.") and 16 <= int(octets[1]) <= 31
                        ):
                            ips.add(ip)
                    except (IndexError, ValueError):
                        pass
    else:
        # Fallback using socket.gethostbyname_ex
        try:
            hostname = socket.gethostname()
            for ip in socket.gethostbyname_ex(hostname)[2]:
                if ip.startswith("127."):
                    continue
                octets = ip.split('.')
                try:
                    if (ip.startswith("10.")) or (ip.startswith("192.168.")) or (
                        ip.startswith("172.") and 16 <= int(octets[1]) <= 31
                    ):
                        ips.add(ip)
                except (IndexError, ValueError):
                    pass
        except Exception:
            pass
    return list(ips)

app = Flask(__name__)

# Global variable for the running server
http_server = None

# Will be set at startup:
UPLOAD_DIR = None

@app.route("/")
def serve_index():
    """Serve the index.html file from the same folder as this script."""
    script_dir = os.path.dirname(__file__)
    return send_from_directory(script_dir, "index.html")

@app.route("/upload", methods=["POST"])
def upload():
    """
    Handle the uploaded files, save them to UPLOAD_DIR,
    then schedule a shutdown of the server.
    Also prints and returns the full paths of the saved files.
    """
    uploaded_files = request.files.getlist("files")
    saved_paths = []
    for f in uploaded_files:
        if f and f.filename:
            # Save using an absolute path
            save_path = os.path.abspath(os.path.join(UPLOAD_DIR, f.filename))
            f.save(save_path)
            saved_paths.append(save_path)

    if saved_paths:
        print("[*] Files received:")
        for path in saved_paths:
            print(path)
    else:
        print("[*] No valid files received.")

    # Schedule the shutdown after sending the response
    threading.Thread(target=delayed_shutdown).start()

    response_text = "File(s) uploaded successfully. The server will now shut down...\n"
    if saved_paths:
        response_text += "\n".join(saved_paths)
    return Response(response_text, mimetype="text/plain")

def delayed_shutdown():
    """
    Wait briefly so the /upload response can be fully sent,
    then shut down the server.
    """
    time.sleep(1)
    if http_server:
        print("[*] Shutting down the server gracefully...")
        http_server.shutdown()

def run_server(host, port):
    """
    Create a WSGI server via make_server, store it globally, then serve forever.
    Also prints the available LAN IP addresses if bound to 0.0.0.0.
    """
    global http_server
    http_server = make_server(host, port, app)
    print(f"[*] Server is running on http://{host}:{port}")

    # If binding to all interfaces, list the LAN addresses.
    if host == "0.0.0.0":
        lan_ips = get_lan_ips()
        if lan_ips:
            print("[*] Accessible on the following LAN addresses:")
            for ip in lan_ips:
                print(f"    http://{ip}:{port}")
    http_server.serve_forever()
    print("[*] Server has shut down. Exiting...")

def main():
    """
    Parse command-line arguments, set up the UPLOAD_DIR, and start the server.
    """
    global UPLOAD_DIR

    parser = argparse.ArgumentParser(
        description="A Flask file uploader that stops after handling an upload."
    )
    parser.add_argument(
        "--dir",
        default="downloads",
        help="Directory to save uploaded files (default: %(default)s)."
    )
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Host/IP to bind to (default: %(default)s)."
    )
    parser.add_argument(
        "--port",
        default=5000,
        type=int,
        help="Port to listen on (default: %(default)s)."
    )
    args = parser.parse_args()

    # Set up the upload directory (as an absolute path)
    UPLOAD_DIR = os.path.join(os.getcwd(), args.dir)
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    print(f"[*] Upload directory is set to: {UPLOAD_DIR}")

    # Start the server (this call blocks until shutdown)
    run_server(args.host, args.port)

if __name__ == "__main__":
    main()
