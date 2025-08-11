#!/bin/bash
# Setup script for Knowledge Base + Gemini Integration

echo "🚀 Setting up Knowledge Base + Gemini Integration..."

# Navigate to backend directory
cd /home/ishaan/Documents/fullStackKbSearch/backend

# Install new Python dependencies
echo "📦 Installing new dependencies..."
pip install python-dotenv==1.0.0
pip install google-generativeai==0.3.2

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p vector_stores
mkdir -p uploads

# Check if .env file exists and has GEMINI_API_KEY
if [ -f ".env" ]; then
    if grep -q "GEMINI_API_KEY" .env; then
        echo "✅ Gemini API key found in .env file"
    else
        echo "⚠️ Please add GEMINI_API_KEY to your .env file"
    fi
else
    echo "⚠️ No .env file found. Please create one with GEMINI_API_KEY"
fi

echo "✅ Setup completed!"
echo ""
echo "🔧 Next steps:"
echo "1. Upload some PDF/TXT files through the admin dashboard"
echo "2. Test the chat widget to see AI responses based on uploaded knowledge"
echo "3. Check the backend logs to see vector search and Gemini API calls"
