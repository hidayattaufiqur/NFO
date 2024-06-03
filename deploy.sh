#!/run/current-system/sw/bin/zsh
echo "changing dir..."
cd Fun/Projects/ontology-BE

echo "pulling from repo..."
git pull 

echo "injecting .env..."
mv env .env

echo "init/installing deps using poetry..."
nix develop --command bash -c "poetry install"

echo "restarting systemd unit..."
sudo systemctl restart ontology-be

echo "systemd unit status..."
sudo systemctl status ontology-be

echo "done!!!"
