{
  description = "A Nix-flake-based Python development environment";

  inputs = { 
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    poetry2nix.url = "github:nix-community/poetry2nix";
    poetry2nix.inputs.nixpkgs.follows = "nixpkgs";
  };

  outputs = { self, nixpkgs, poetry2nix }:
    let
      lib = nixpkgs.lib;
      # supportedSystems = [ "x86_64-linux" "aarch64-linux" "x86_64-darwin" "aarch64-darwin" ];
      supportedSystems = [ "x86_64-linux" ];
      forEachSupportedSystem = f: nixpkgs.lib.genAttrs supportedSystems (system: f {
        pkgs = import nixpkgs { inherit system; };
      });
      pkgs = nixpkgs.legacyPackages.${supportedSystems};
      inherit (poetry2nix.lib.mkPoetry2Nix { inherit pkgs; }) mkPoetryApplication;
      myPythonApp = mkPoetryApplication { projectDir = ./.; };
    in
    {
      apps."x86_64-linux" .default = {
        type = "app";
        # replace <script> with the name in the [tool.poetry.scripts] section of your pyproject.toml
        program = "${myPythonApp}/bin/main";
      };
      devShells = forEachSupportedSystem ({ pkgs }: {
        default = pkgs.mkShell {
          # environment = {
          #   sessionVariables = {
          #     LD_LIBRARY_PATH = "${pkgs.stdenv.cc.cc.lib}/lib";
          #   };
          # };
          packages = with pkgs; [
            python311
            poetry
            cowsay
            python311Packages.virtualenv
          ]; 

          LD_LIBRARY_PATH = lib.makeLibraryPath [
            pkgs.stdenv.cc.cc
            pkgs.zlib
          ];

          buildInputs = with pkgs; [
            stdenv.cc.cc
          ];

          shellHook = with pkgs; ''
            cowsay "`${python311}/bin/python3 --version` environment activated"

            python -m venv ./.venv

            . ./.venv/bin/activate
            echo
            echo 
            cowsay "venv activated"
            unset SOURCE_DATE_EPOCH
          '';
        };


      });
    };
}
