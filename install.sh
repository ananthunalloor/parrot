
#!/usr/bin/env bash
# install.sh: Sets up virtual environment and installs dependencies

# Create virtual environment
py -m venv .venv

# Activate
source .venv/bin/activate

# Upgrade pip and install
pip install --upgrade pip
pip install -r requirements.txt

echo "Setup complete. Activate with 'source .venv/bin/activate' and run './start.sh' to launch."``` 
