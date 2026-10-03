#!/bin/sh
# Build a .deb from an already-compiled binary.
# Usage: packaging/build-deb.sh <binary> <version> <arch> <outdir>
#   e.g. packaging/build-deb.sh build/ghostfile-linux-amd64 3.0.0 amd64 build
set -eu

bin=$1 version=$2 arch=$3 out=$4
root=$(mktemp -d)
chmod 755 "$root"
trap 'rm -rf "$root"' EXIT

install -Dm755 "$bin" "$root/usr/bin/ghostfile"
install -Dm644 packaging/ghostfile.desktop "$root/usr/share/applications/ghostfile.desktop"
install -Dm644 ghostfile.png "$root/usr/share/pixmaps/ghostfile.png"
install -Dm644 LICENSE "$root/usr/share/doc/ghostfile/copyright"

mkdir -p "$root/DEBIAN"
cat > "$root/DEBIAN/control" <<CONTROL
Package: ghostfile
Version: $version
Section: utils
Priority: optional
Architecture: $arch
Maintainer: thehelpfulidiot <admin@thehelpfulidiot.com>
Homepage: https://github.com/jon6fingrs/ghostfile
Description: Ephemeral one-shot file upload server
 Serves a small web page, accepts one upload of one or more files,
 saves them to a directory and exits.
CONTROL

mkdir -p "$out"
dpkg-deb --root-owner-group -Zxz --build "$root" "$out/ghostfile_${version}_${arch}.deb"
