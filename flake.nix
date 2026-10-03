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

      nixosModules.default = { config, lib, pkgs, ... }:
        let cfg = config.programs.ghostfile;
        in {
          options.programs.ghostfile = {
            enable = lib.mkEnableOption "GhostFile";
            package = lib.mkOption {
              type = lib.types.package;
              default = self.packages.${pkgs.stdenv.hostPlatform.system}.default;
              description = "The ghostfile package to install.";
            };
            openFirewall = lib.mkOption {
              type = lib.types.bool;
              default = false;
              description = "Open the TCP port GhostFile listens on.";
            };
            port = lib.mkOption {
              type = lib.types.port;
              default = 5000;
              description = "Port to open in the firewall when openFirewall is set.";
            };
          };

          config = lib.mkIf cfg.enable {
            environment.systemPackages = [ cfg.package ];
            networking.firewall.allowedTCPPorts = lib.mkIf cfg.openFirewall [ cfg.port ];
          };
        };
    };
}
