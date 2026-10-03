{
  description = "GhostFile - ephemeral one-shot file upload server";

  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";

  outputs = { self, nixpkgs }:
    let
      systems = [ "x86_64-linux" "aarch64-linux" "x86_64-darwin" "aarch64-darwin" ];
      forAllSystems = f: nixpkgs.lib.genAttrs systems (system: f nixpkgs.legacyPackages.${system});
      version = "3.0.0";
    in
    {
      packages = forAllSystems (pkgs: rec {
        ghostfile = pkgs.callPackage ./package.nix { inherit version; };
        default = ghostfile;
      });

      overlays.default = final: _prev: {
        ghostfile = final.callPackage ./package.nix { inherit version; };
      };

      nixosModules.default = { pkgs, lib, ... }: {
        imports = [ ./module.nix ];
        programs.ghostfile.package = lib.mkDefault self.packages.${pkgs.stdenv.hostPlatform.system}.default;
      };
    };
}
