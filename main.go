// GhostFile is a one-shot file upload server: it serves a small web page,
// accepts a single upload of one or more files, saves them, and exits.
package main

import (
	"context"
	_ "embed"
	"errors"
	"flag"
	"fmt"
	"io"
	"net"
	"net/http"
	"os"
	"os/signal"
	"path/filepath"
	"strconv"
	"strings"
	"syscall"
	"time"
)

// version is overridden at build time with -ldflags "-X main.version=...".
var version = "dev"

//go:embed index.html
var indexHTML string

func main() {
	dir := flag.String("dir", ".", "directory to save uploaded files")
	host := flag.String("host", "0.0.0.0", "host/IP to bind to")
	port := flag.Int("port", 5000, "port to listen on")
	keep := flag.Bool("keep", false, "keep running after an upload instead of exiting")
	showVersion := flag.Bool("version", false, "print version and exit")
	// Accepted for compatibility with the old Python version; ignored.
	flag.String("gui", "", "ignored (the GUI was removed in 3.0)")
	flag.Parse()

	if *showVersion {
		fmt.Println("ghostfile", version)
		return
	}

	if err := run(*dir, *host, *port, *keep); err != nil {
		fmt.Fprintln(os.Stderr, "[!]", err)
		os.Exit(1)
	}
}

func run(dir, host string, port int, keep bool) error {
	uploadDir, err := filepath.Abs(dir)
	if err != nil {
		return err
	}
	if err := os.MkdirAll(uploadDir, 0o755); err != nil {
		return err
	}

	addr := net.JoinHostPort(host, strconv.Itoa(port))
	ln, err := net.Listen("tcp", addr)
	if err != nil {
		return err
	}

	done := make(chan struct{}, 1)
	page := strings.ReplaceAll(indexHTML, "{{VERSION}}", version)

	mux := http.NewServeMux()
	mux.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path != "/" {
			http.NotFound(w, r)
			return
		}
		w.Header().Set("Content-Type", "text/html; charset=utf-8")
		io.WriteString(w, page)
	})
	mux.HandleFunc("/upload", func(w http.ResponseWriter, r *http.Request) {
		if r.Method != http.MethodPost {
			http.Error(w, "method not allowed", http.StatusMethodNotAllowed)
			return
		}
		saved, err := saveUploads(r, uploadDir)
		for _, p := range saved {
			fmt.Println("[*] Saved:", p)
		}
		w.Header().Set("Content-Type", "text/plain; charset=utf-8")
		switch {
		case err != nil:
			fmt.Fprintln(os.Stderr, "[!] Upload failed:", err)
			w.WriteHeader(http.StatusInternalServerError)
			fmt.Fprintf(w, "Upload failed: %v\n", err)
			return
		case len(saved) == 0:
			fmt.Println("[*] Upload contained no files; still waiting.")
			w.WriteHeader(http.StatusBadRequest)
			io.WriteString(w, "No files received. Go back and select some files.\n")
			return
		}
		if keep {
			fmt.Fprintf(w, "Uploaded %d file(s):\n%s\n", len(saved), strings.Join(saved, "\n"))
			return
		}
		fmt.Fprintf(w, "Uploaded %d file(s). The server is shutting down.\n%s\n", len(saved), strings.Join(saved, "\n"))
		select {
		case done <- struct{}{}:
		default:
		}
	})

	srv := &http.Server{Handler: mux, ReadHeaderTimeout: 10 * time.Second}

	fmt.Println("[*] Upload directory:", uploadDir)
	printURLs(host, port)

	errc := make(chan error, 1)
	go func() { errc <- srv.Serve(ln) }()

	sig, stop := signal.NotifyContext(context.Background(), os.Interrupt, syscall.SIGTERM)
	defer stop()

	select {
	case err := <-errc:
		return err
	case <-sig.Done():
		fmt.Println("\n[*] Interrupted, shutting down.")
	case <-done:
		fmt.Println("[*] Upload complete, shutting down.")
	}

	// Shutdown waits for in-flight responses (including the upload reply) to finish.
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()
	if err := srv.Shutdown(ctx); err != nil && !errors.Is(err, http.ErrServerClosed) {
		return err
	}
	return nil
}

// saveUploads streams every file part of a multipart request into dir and
// returns the absolute paths written. Existing files are never overwritten.
func saveUploads(r *http.Request, dir string) ([]string, error) {
	mr, err := r.MultipartReader()
	if err != nil {
		return nil, err
	}
	var saved []string
	for {
		part, err := mr.NextPart()
		if err == io.EOF {
			return saved, nil
		}
		if err != nil {
			return saved, err
		}
		name := filepath.Base(part.FileName())
		if part.FormName() != "files" || name == "." || name == string(filepath.Separator) {
			part.Close()
			continue
		}
		path, err := saveFile(part, dir, name)
		part.Close()
		if err != nil {
			return saved, err
		}
		saved = append(saved, path)
	}
}

func saveFile(src io.Reader, dir, name string) (string, error) {
	f, path, err := createUnique(dir, name)
	if err != nil {
		return "", err
	}
	if _, err := io.Copy(f, src); err != nil {
		f.Close()
		os.Remove(path)
		return "", err
	}
	return path, f.Close()
}

// createUnique creates dir/name, or "name (1).ext", "name (2).ext", ... if
// that already exists.
func createUnique(dir, name string) (*os.File, string, error) {
	ext := filepath.Ext(name)
	stem := strings.TrimSuffix(name, ext)
	for i := 0; ; i++ {
		candidate := name
		if i > 0 {
			candidate = fmt.Sprintf("%s (%d)%s", stem, i, ext)
		}
		path := filepath.Join(dir, candidate)
		f, err := os.OpenFile(path, os.O_WRONLY|os.O_CREATE|os.O_EXCL, 0o644)
		if errors.Is(err, os.ErrExist) {
			continue
		}
		return f, path, err
	}
}

func printURLs(host string, port int) {
	if host != "0.0.0.0" && host != "" && host != "::" {
		fmt.Printf("[*] Listening on http://%s\n", net.JoinHostPort(host, strconv.Itoa(port)))
		return
	}
	fmt.Printf("[*] Listening on all interfaces, port %d\n", port)
	for _, ip := range lanIPs() {
		fmt.Printf("    http://%s:%d\n", ip, port)
	}
}

// lanIPs lists the IPv4 addresses of interfaces that are up, skipping
// loopback, link-local and container bridge interfaces.
func lanIPs() []string {
	ifaces, err := net.Interfaces()
	if err != nil {
		return nil
	}
	var ips []string
	for _, iface := range ifaces {
		if iface.Flags&net.FlagUp == 0 || iface.Flags&net.FlagLoopback != 0 {
			continue
		}
		if n := iface.Name; strings.HasPrefix(n, "docker") || strings.HasPrefix(n, "veth") ||
			strings.HasPrefix(n, "br-") || strings.HasPrefix(n, "virbr") {
			continue
		}
		addrs, err := iface.Addrs()
		if err != nil {
			continue
		}
		for _, a := range addrs {
			ipnet, ok := a.(*net.IPNet)
			if !ok {
				continue
			}
			if ip4 := ipnet.IP.To4(); ip4 != nil && !ip4.IsLinkLocalUnicast() {
				ips = append(ips, ip4.String())
			}
		}
	}
	return ips
}
