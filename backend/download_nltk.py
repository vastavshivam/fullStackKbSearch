#!/usr/bin/env python3
"""Download required NLTK data for the knowledge base system"""

import nltk
import os
import ssl

# Handle SSL certificate verification
try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    pass
else:
    ssl._create_default_https_context = _create_unverified_https_context

# Create nltk_data directory
os.makedirs('/home/ishaan/nltk_data', exist_ok=True)

print("Downloading NLTK data...")

# Download required NLTK data
downloads = ['punkt', 'punkt_tab', 'stopwords', 'averaged_perceptron_tagger']

for item in downloads:
    try:
        print(f"Downloading {item}...")
        nltk.download(item, download_dir='/home/ishaan/nltk_data')
        print(f"✅ Successfully downloaded {item}")
    except Exception as e:
        print(f"❌ Failed to download {item}: {e}")

print("\nNLTK data download process complete!")

# Test if the data is available
try:
    from nltk.tokenize import word_tokenize
    test_text = "This is a test sentence."
    tokens = word_tokenize(test_text)
    print(f"✅ Tokenization test successful: {tokens}")
except Exception as e:
    print(f"❌ Tokenization test failed: {e}")
