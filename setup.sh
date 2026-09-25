#!/bin/bash
set -e

echo "Setting up Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

echo "Installing dependencies..."
pip install -r requirements.txt

echo "Downloading spaCy model (en_core_web_md)..."
python -m spacy download en_core_web_md

echo "Downloading sentence-transformers model (all-MiniLM-L6-v2) offline..."
python -c "
from sentence_transformers import SentenceTransformer
import os
os.environ['TRANSFORMERS_OFFLINE'] = '0' # allow download
model = SentenceTransformer('all-MiniLM-L6-v2')
model.save('./models/all-MiniLM-L6-v2')
"

echo "Setup complete. Run 'source venv/bin/activate' to activate the environment."
