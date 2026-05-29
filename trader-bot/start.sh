#!/bin/bash

# Trading Bot Startup Script
# This script sets up the environment and starts the trading bot

set -e

echo "🤖 Starting AI Trading Bot Setup..."

# Check if we're in the right directory
if [ ! -f "requirements.txt" ]; then
    echo "❌ Error: requirements.txt not found. Please run this script from the trader-bot directory."
    exit 1
fi

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Check Python version
echo "🐍 Checking Python version..."
python3 --version
if [ $? -ne 0 ]; then
    print_error "Python 3 is not installed or not in PATH"
    exit 1
fi
print_status "Python 3 found"

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    print_info "Creating virtual environment..."
    python3 -m venv .venv
    print_status "Virtual environment created"
else
    print_status "Virtual environment already exists"
fi

# Activate virtual environment
print_info "Activating virtual environment..."
source .venv/bin/activate
print_status "Virtual environment activated"

# Upgrade pip
print_info "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
print_info "Installing dependencies..."
pip install -r requirements.txt
if [ $? -eq 0 ]; then
    print_status "Dependencies installed successfully"
else
    print_error "Failed to install dependencies"
    exit 1
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    print_warning ".env file not found"
    if [ -f ".env.example" ]; then
        print_info "Copying .env.example to .env..."
        cp .env.example .env
        print_warning "Please edit .env file with your API keys before running the bot"
    else
        print_error ".env.example file not found"
        exit 1
    fi
else
    print_status ".env file found"
fi

# Create necessary directories
print_info "Creating necessary directories..."
mkdir -p logs data config
print_status "Directories created"

# Check services (optional)
print_info "Checking external services..."

# Check MongoDB
if command -v mongod &> /dev/null; then
    print_status "MongoDB found"
    if pgrep -x "mongod" > /dev/null; then
        print_status "MongoDB is running"
    else
        print_warning "MongoDB is not running. You may need to start it:"
        echo "  brew services start mongodb-community"
    fi
else
    print_warning "MongoDB not found. Install with:"
    echo "  brew install mongodb-community"
fi

# Check Redis
if command -v redis-server &> /dev/null; then
    print_status "Redis found"
    if pgrep -x "redis-server" > /dev/null; then
        print_status "Redis is running"
    else
        print_warning "Redis is not running. You may need to start it:"
        echo "  brew services start redis"
    fi
else
    print_warning "Redis not found. Install with:"
    echo "  brew install redis"
fi

# Test imports
print_info "Testing Python imports..."
python3 -c "
import sys
sys.path.append('src')
try:
    from config import get_config
    from screener import StockScreener
    from broker import BrokerInterface
    print('✅ All imports successful')
except ImportError as e:
    print(f'❌ Import error: {e}')
    sys.exit(1)
"

if [ $? -eq 0 ]; then
    print_status "All imports working correctly"
else
    print_error "Import test failed"
    exit 1
fi

# Display startup options
echo ""
echo "🚀 Setup complete! Choose how to run the bot:"
echo ""
echo "1. Run trading bot only:"
echo "   python src/main.py --mode bot"
echo ""
echo "2. Run web interface only:"
echo "   python src/main.py --mode web"
echo ""
echo "3. Run both bot and web interface:"
echo "   python src/main.py --mode both"
echo ""
echo "4. Test individual modules:"
echo "   python src/screener.py"
echo "   python src/sentiment.py"
echo "   python src/broker.py"
echo ""
echo "5. Run tests:"
echo "   python -m pytest tests/"
echo ""
echo "📊 Web dashboard will be available at: http://localhost:8000"
echo ""

# Check if user wants to start the bot
read -p "Do you want to start the trading bot now? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    print_info "Starting trading bot..."
    
    # Check .env configuration
    if grep -q "your_.*_here" .env; then
        print_warning "Detected placeholder values in .env file"
        print_warning "The bot will run in MOCK mode"
        echo ""
    fi
    
    # Start the bot
    python src/main.py --mode both
else
    print_info "Setup complete. You can start the bot manually using the commands above."
fi

echo ""
print_status "Trading Bot setup completed!"
echo ""
echo "📖 For more information, see README.md"
echo "🆘 For troubleshooting, check the logs/ directory"
echo ""
