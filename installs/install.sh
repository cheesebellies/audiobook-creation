cd "$(dirname "$0")"
cd ..

brew install python@3.11
brew install sox

mkdir -p books voices

python3.11 -m venv .venv
source .venv/bin/activate

python -m pip install --upgrade pip
pip install -r requirements.txt
pip install torch torchaudio
python -m spacy download en_core_web_sm