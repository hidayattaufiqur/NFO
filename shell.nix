with import <nixpkgs> { };
let
  pythonPackages = python311Packages;
in pkgs.mkShell 
rec {
  name = "impurePythonEnv";
  venvDir = "./.venv";

  NIX_LD_LIBRARY_PATH = lib.makeLibraryPath [
    stdenv.cc.cc
    zlib
  ];

  NIX_LD = lib.fileContents "${stdenv.cc}/nix-support/dynamic-linker";

  buildInputs = [
    # A Python interpreter including the 'venv' module is required to bootstrap
    # the environment.
    pythonPackages.python

    # This executes some shell code to initialize a venv in $venvDir before
    # dropping into the shell
    pythonPackages.venvShellHook

    # Those are dependencies that we would like to use from nixpkgs, which will
    # add them to PYTHONPATH and thus make them accessible from within the venv.
    pythonPackages.requests

    # In this particular example, in order to compile any binary extensions they may
    # require, the Python modules listed in the hypothetical requirements.txt need
    # the following packages to be installed locally:

    postgresql # must be installed so psycop library under PostgresChatMessageHistory would work. 
    libpqxx
    taglib
    openssl
    git
    libxml2
    libxslt
    libzip
    zlib
    stdenv.cc.cc
  ];


  # Run this command, only after creating the virtual environment
  postVenvCreation = ''
    unset SOURCE_DATE_EPOCH
    pip install -r requirements.txt
  '';

  # shellHook = ''
  #   export LD_LIBRARY_PATH=$NIX_LD_LIBRARY_PATH
  # '';

  # Now we can execute any commands within the virtual environment.
  # This is optional and can be left out to run pip manually.
  postShellHook = ''
    # allow pip to install wheels
    unset SOURCE_DATE_EPOCH
    # fixes libstdc++ issues and libgl.so issues
  '';
}

