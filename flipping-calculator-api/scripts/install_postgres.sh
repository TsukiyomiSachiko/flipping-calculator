#!/bin/bash

echo "🐘 Installing PostgreSQL in WSL..."

# Update package list
sudo apt update

# Install PostgreSQL
sudo apt install -y postgresql postgresql-contrib

# Start PostgreSQL service
sudo service postgresql start

# Check status
sudo service postgresql status

echo ""
echo "✅ PostgreSQL installed!"
echo ""
echo "Next steps:"
echo "1. Run: sudo -u postgres psql"
echo "2. Create database and user (see setup_database.sh)"
