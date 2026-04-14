#!/bin/bash

echo "🗄️  Setting up OSRS Flipping Database..."
echo ""

# Run commands as postgres user
sudo -u postgres psql <<EOF

-- Create database
CREATE DATABASE osrs_flipping;

-- Create user with password
CREATE USER flipping_user WITH PASSWORD 'flipping_dev_password';

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE osrs_flipping TO flipping_user;

-- Connect to database and grant schema privileges
\c osrs_flipping

GRANT ALL ON SCHEMA public TO flipping_user;

-- Show databases
\l

EOF

echo ""
echo "✅ Database created!"
echo ""
echo "Database: osrs_flipping"
echo "User: flipping_user"
echo "Password: flipping_dev_password"
echo ""
echo "Connection string:"
echo "postgresql://flipping_user:flipping_dev_password@localhost/osrs_flipping"
