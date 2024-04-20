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
          # venvDir = "./.venv";
          packages = with pkgs; [
            python311
            poetry
            cowsay
          ] ++ (with pkgs.python311Packages; 
          [ 
            # pip
            # venvShellHook
            # requests
            # flask 
            # flask-login
            # google-auth
            # google-auth-oauthlib
            # python-dotenv
            # openai
            # langchain
            # psycopg2
          ]);

          # buildInputs = with pkgs; [
          #   # A Python interpreter including the 'venv' module is required to bootstrap
          #   # the environment.
          #   python311Packages.python
          #
          #   # This executes some shell code to initialize a venv in $venvDir before
          #   # dropping into the shell
          #   python311Packages.venvShellHook
          #
          #   # Those are dependencies that we would like to use from nixpkgs, which will
          #   # add them to PYTHONPATH and thus make them accessible from within the venv.
          #   python311Packages.numpy
          #   python311Packages.requests
          #
          #   # In this particular example, in order to compile any binary extensions they may
          #   # require, the Python modules listed in the hypothetical requirements.txt need
          #   # the following packages to be installed locally:
          #   taglib
          #   openssl
          #   git
          #   libxml2
          #   libxslt
          #   libzip
          #   zlib
          # ];

          # Run this command, only after creating the virtual environment
          # postVenvCreation = ''
          #   # unset SOURCE_DATE_EPOCH
          #   # pip install -r requirements.txt
          #   # poetry install 
          # '';

          shellHook = with pkgs; ''
            # export PIP_PREFIX=$(pwd)/_build/pip_packages # dir where built packages are stored
            # export PYTHONPATH="$PIP_PREFIX/${python311.sitePackages}:$PYTHONPATH"
            # export PATH="$PIP_PREFIX/bin:$PATH"
            # unset SOURCE_DATE_EPOCH

            cowsay "`${python311}/bin/python3 --version` environment activated"
            echo 
            echo 
          '';
        };
      });
    };
}
