#!/usr/bin/env python3
import os
import time
import argparse
import threading
from flask import Flask, request, send_from_directory, Response
from werkzeug.serving import make_server

app = Flask(__name__)

# We store the server in a module/global variable so routes can shut it down
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
    """
    uploaded_files = request.files.getlist("files")
    for f in uploaded_files:
        if f and f.filename:
            save_path = os.path.join(UPLOAD_DIR, f.filename)
            f.save(save_path)

    # Use a separate thread to allow the response to complete 
    # before actually killing the server
    threading.Thread(target=delayed_shutdown).start()

    return Response(
        "File(s) uploaded successfully. The server will now shut down...",
        mimetype="text/plain"
    )

def delayed_shutdown():
    """
    Wait briefly so the /upload response can be fully sent,
    then call http_server.shutdown() to stop serving.
    """
    time.sleep(1)
    if http_server:
        print("[*] Shutting down the server gracefully...")
        http_server.shutdown()

def run_server(host, port):
    """
    Create a WSGI server via make_server, store it globally, serve_forever().
    """
    global http_server
    http_server = make_server(host, port, app)
    print(f"[*] Server is running on http://{host}:{port}")
    http_server.serve_forever()
    print("[*] Server has shut down. Exiting...")

def main():
    """
    Parses command-line arguments, sets up the UPLOAD_DIR, then starts the server.
    """
    global UPLOAD_DIR

    parser = argparse.ArgumentParser(description="A Flask file uploader that stops after handling an upload.")
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

    # Prepare the upload directory
    UPLOAD_DIR = os.path.join(os.getcwd(), args.dir)
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    print(f"[*] Upload directory is set to: {UPLOAD_DIR}")

    # Start the server; it will block here until .shutdown() is called
    run_server(args.host, args.port)

if __name__ == "__main__":
    main()
