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
		"a.txt":          "new",
		"../../evil.txt": "escaped?",
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
	if len(saved) != 2 {
		t.Fatalf("saved %v, want 2 files", saved)
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
}
