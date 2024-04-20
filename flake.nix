{
  description = "A Nix-flake-based Python development environment";

  inputs = { 
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
  };

  outputs = { self, nixpkgs }:
    let
      # supportedSystems = [ "x86_64-linux" "aarch64-linux" "x86_64-darwin" "aarch64-darwin" ];
      supportedSystems = [ "x86_64-linux" ];
      forEachSupportedSystem = f: nixpkgs.lib.genAttrs supportedSystems (system: f {
        pkgs = import nixpkgs { inherit system; };
      });
    in
    {
      devShells = forEachSupportedSystem ({ pkgs }: {
        default = pkgs.mkShell {
          packages = with pkgs; [
            python311
            poetry
            cowsay
          ]; 

          shellHook = with pkgs; ''
            cowsay "`${python311}/bin/python3 --version` environment activated"

            . ./.venv/bin/activate
            echo
            echo 
            cowsay "venv activated"
          '';
        };
      });
    };
}
