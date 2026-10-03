package main

import (
	"bytes"
	"mime/multipart"
	"net/http/httptest"
	"os"
	"path/filepath"
	"testing"
)

func TestSaveUploads(t *testing.T) {
	dir := t.TempDir()
	if err := os.WriteFile(filepath.Join(dir, "a.txt"), []byte("existing"), 0o644); err != nil {
		t.Fatal(err)
	}

	var body bytes.Buffer
	mw := multipart.NewWriter(&body)
	for name, content := range map[string]string{
		"a.txt":             "new",
		"../../evil.txt":    "escaped?",
		"photos/2024/b.jpg": "nested",
		"/abs/c.txt":        "absolute",
	} {
		w, _ := mw.CreateFormFile("files", name)
		w.Write([]byte(content))
	}
	mw.WriteField("other", "ignored")
	mw.Close()

	req := httptest.NewRequest("POST", "/upload", &body)
	req.Header.Set("Content-Type", mw.FormDataContentType())

	saved, err := saveUploads(req, dir)
	if err != nil {
		t.Fatal(err)
	}
	if len(saved) != 4 {
		t.Fatalf("saved %v, want 4 files", saved)
	}

	check := func(name, want string) {
		t.Helper()
		got, err := os.ReadFile(filepath.Join(dir, name))
		if err != nil || string(got) != want {
			t.Errorf("%s = %q, %v; want %q", name, got, err, want)
		}
	}
	check("a.txt", "existing")
	check("a (1).txt", "new")
	check("evil.txt", "escaped?")
	check("photos/2024/b.jpg", "nested")
	check("abs/c.txt", "absolute")
}

func TestUploadURL(t *testing.T) {
	for in, want := range map[string]string{
		"192.168.1.5":                "http://192.168.1.5:5000/upload",
		"192.168.1.5:8080":           "http://192.168.1.5:8080/upload",
		"nas.lan":                    "http://nas.lan:5000/upload",
		"http://nas.lan:5000/":       "http://nas.lan:5000/upload",
		"http://nas.lan:5000/upload": "http://nas.lan:5000/upload",
		"[::1]":                      "http://[::1]:5000/upload",
	} {
		if got := uploadURL(in); got != want {
			t.Errorf("uploadURL(%q) = %q, want %q", in, got, want)
		}
	}
}
