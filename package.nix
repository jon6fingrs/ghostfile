{ lib, buildGoModule, version ? "3.1.0" }:

buildGoModule {
  pname = "ghostfile";
  inherit version;

  src = lib.fileset.toSource {
    root = ./.;
    fileset = lib.fileset.unions [
      ./go.mod
      ./main.go
      ./main_test.go
      ./send.go
      ./index.html
      ./ghostfile.png
      ./packaging/ghostfile.desktop
    ];
  };

  vendorHash = null;

  env.CGO_ENABLED = 0;
  ldflags = [ "-s" "-w" "-X main.version=${version}" ];

  postInstall = ''
    ln -s ghostfile $out/bin/ghostfile-send
    install -Dm644 packaging/ghostfile.desktop $out/share/applications/ghostfile.desktop
    install -Dm644 ghostfile.png $out/share/pixmaps/ghostfile.png
  '';

  meta = {
    description = "Ephemeral one-shot file upload server";
    homepage = "https://github.com/jon6fingrs/ghostfile";
    license = lib.licenses.mit;
    mainProgram = "ghostfile";
    platforms = lib.platforms.unix;
  };
}
