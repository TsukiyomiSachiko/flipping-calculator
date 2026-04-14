#!/bin/bash

# PostgreSQL Auto-Start Helper
# WSL doesn't auto-start services, so this helps you start Postgres easily

echo "🐘 Starting PostgreSQL..."

# Check if already running
if sudo service postgresql status | grep -q "online"; then
    echo "✅ PostgreSQL is already running!"
else
    # Start PostgreSQL
    sudo service postgresql start
    
    # Wait a moment
    sleep 2
    
    # Check status
    if sudo service postgresql status | grep -q "online"; then
        echo "✅ PostgreSQL started successfully!"
    else
        echo "❌ Failed to start PostgreSQL"
        sudo service postgresql status
        exit 1
    fi
fi

echo ""
echo "Connection info:"
echo "  Host: localhost"
echo "  Port: 5432"
echo "  Database: osrs_flipping"
echo "  User: flipping_user"
