#!/bin/bash
#
# Use this script during development when containerized
# when resetting the containerized state to base

# Exit immediately if any command fails
set -e

# Get the file path of this script
root=$(dirname "$(realpath "$0")")
django_root="$root/django"

# Function to print action messages
log_action() {
    echo "==> $1"
}


# Function to ask yes/no question
ask_yes_no() {
    while true; do
        read -p "$1 [y/n]: " yn
        case $yn in
            [Yy]* ) return 0;;
            [Nn]* ) return 1;;
            * ) echo "Please answer yes or no.";;
        esac
    done
}

log_action "Clearing out staticfiles..."
rm -rf "${django_root}/staticfiles/"*

if ask_yes_no "Do you want to clear out staticfiles and mediafiles?"; then
    log_action "Cleaning media files (except default.jpg)..."
    find "${django_root}/mediafiles/" -mindepth 1 -not -name 'default.jpg' -delete
fi

log_action "Rebuilding a new django image..."
docker compose -f "${root}/docker-compose.yaml" build django

log_action "Stopping current django container..."
docker compose -f "${root}/docker-compose.yaml" stop django

log_action "Removing old django container..."
docker compose -f "${root}/docker-compose.yaml" rm -f django

log_action "Bringing up new container..."
docker compose -f "${root}/docker-compose.yaml" up -d --no-deps --force-recreate django

echo "Reset complete."


