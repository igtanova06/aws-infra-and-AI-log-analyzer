#!/bin/bash
set -e

# Load environment variables from .env file if it exists
if [ -f /var/www/html/.env ]; then
    echo "Loading environment variables from .env file..."
    export $(cat /var/www/html/.env | grep -v '^#' | grep -v '^$' | xargs)
fi

# Execute the main command
exec "$@"
