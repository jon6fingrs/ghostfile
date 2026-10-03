package main

import (
	"flag"
	"fmt"
	"io"
	"io/fs"
	"mime/multipart"
	"net"
	"net/http"
	"net/textproto"
	"os"
	"path/filepath"
	"strings"
)

// isSendInvocation reports whether the binary was run as "ghostfile-send"
// (e.g. through a symlink).
func isSendInvocation() bool {
	name := strings.TrimSuffix(filepath.Base(os.Args[0]), ".exe")
	return name == "ghostfile-send"
}

// sendMain implements "ghostfile send HOST[:PORT] PATH...".
func sendMain(args []string) int {
	fset := flag.NewFlagSet("ghostfile send", flag.ContinueOnError)
	fset.Usage = func() {
		fmt.Fprintf(fset.Output(), "Usage: ghostfile send HOST[:PORT] FILE_OR_DIR...\n\n"+
			"Upload files to a running ghostfile server (default port 5000).\n"+
			"Directories are sent recursively, keeping their structure.\n")
	}
	if err := fset.Parse(args); err != nil {
		return 2
	}
	if fset.NArg() < 2 {
		fset.Usage()
		return 2
	}

	url := uploadURL(fset.Arg(0))
	files, err := collectFiles(fset.Args()[1:])
	if err != nil {
		fmt.Fprintln(os.Stderr, "[!]", err)
		return 1
	}
	if len(files) == 0 {
		fmt.Fprintln(os.Stderr, "[!] nothing to send")
		return 1
	}

	fmt.Printf("[*] Sending %d file(s) to %s\n", len(files), url)
	if err := send(url, files); err != nil {
		fmt.Fprintln(os.Stderr, "[!]", err)
		return 1
	}
	return 0
}

// uploadURL turns "host", "host:port" or a full URL into the upload endpoint.
func uploadURL(target string) string {
	target = strings.TrimSuffix(target, "/")
	if !strings.Contains(target, "://") {
		if _, _, err := net.SplitHostPort(target); err != nil {
			target = net.JoinHostPort(strings.Trim(target, "[]"), "5000")
		}
		target = "http://" + target
	}
	if !strings.HasSuffix(target, "/upload") {
		target += "/upload"
	}
	return target
}

type sendFile struct {
	path string // on local disk
	name string // relative path sent to the server, slash-separated
}

// collectFiles expands the arguments into files to send. A file is sent under
// its base name; a directory "photos" is sent as "photos/...".
func collectFiles(args []string) ([]sendFile, error) {
	var files []sendFile
	for _, arg := range args {
		info, err := os.Stat(arg)
		if err != nil {
			return nil, err
		}
		if !info.IsDir() {
			files = append(files, sendFile{arg, filepath.Base(arg)})
			continue
		}
		root := filepath.Clean(arg)
		base := filepath.Base(root)
		err = filepath.WalkDir(root, func(p string, d fs.DirEntry, err error) error {
			if err != nil || !d.Type().IsRegular() {
				return err
			}
			rel, err := filepath.Rel(root, p)
			if err != nil {
				return err
			}
			files = append(files, sendFile{p, filepath.ToSlash(filepath.Join(base, rel))})
			return nil
		})
		if err != nil {
			return nil, err
		}
	}
	return files, nil
}

// send streams all files to the server in a single multipart request.
func send(url string, files []sendFile) error {
	pr, pw := io.Pipe()
	mw := multipart.NewWriter(pw)
	go func() {
		pw.CloseWithError(writeParts(mw, files))
	}()

	resp, err := http.Post(url, mw.FormDataContentType(), pr)
	if err != nil {
		pr.CloseWithError(err)
		return err
	}
	defer resp.Body.Close()
	body, _ := io.ReadAll(resp.Body)
	fmt.Print(string(body))
	if resp.StatusCode != http.StatusOK {
		return fmt.Errorf("server returned %s", resp.Status)
	}
	return nil
}

var quoteEscaper = strings.NewReplacer(`\`, `\\`, `"`, `\"`)

func writeParts(mw *multipart.Writer, files []sendFile) error {
	for _, f := range files {
		h := make(textproto.MIMEHeader)
		h.Set("Content-Disposition", `form-data; name="files"; filename="`+quoteEscaper.Replace(f.name)+`"`)
		h.Set("Content-Type", "application/octet-stream")
		w, err := mw.CreatePart(h)
		if err != nil {
			return err
		}
		src, err := os.Open(f.path)
		if err != nil {
			return err
		}
		_, err = io.Copy(w, src)
		src.Close()
		if err != nil {
			return err
		}
		fmt.Println("   ", f.name)
	}
	return mw.Close()
}
