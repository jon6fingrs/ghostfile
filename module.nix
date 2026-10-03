# NixOS module for GhostFile. Works with or without flakes:
#   imports = [ "${builtins.fetchTarball "https://github.com/jon6fingrs/ghostfile/archive/main.tar.gz"}/module.nix" ];
#   programs.ghostfile.enable = true;
{ config, lib, pkgs, ... }:

let
  cfg = config.programs.ghostfile;
in
{
  options.programs.ghostfile = {
    enable = lib.mkEnableOption "GhostFile, an ephemeral one-shot file upload server";

    package = lib.mkOption {
      type = lib.types.package;
      default = pkgs.callPackage ./package.nix { };
      defaultText = lib.literalExpression "pkgs.callPackage ./package.nix { }";
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
}
