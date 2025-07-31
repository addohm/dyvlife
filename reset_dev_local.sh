#!/bin/bash

# Get the file path of this script
root=$(dirname "$(realpath "$0")")
django_root="$root/django"

# Function to print deletion messages
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

# Process each item in the root directory
for item in "$django_root"/*; do
    # Delete the sqlite3 database
    if [[ "$(basename "$item")" == "db.sqlite3" ]]; then
        if [[ -f "$item" ]]; then
            rm -f "$item"
            log_action "$item"
        fi
    fi
    
    # Process directories
    if [[ -d "$item" ]]; then
        dir_name=$(basename "$item")
        echo "> $item"
        
        # Delete USER UPLOADED MEDIA folder contents
        if [[ "$dir_name" == "mediafiles" || "$dir_name" == "staticfiles" ]]; then
            for subitem in "$item"/*; do
                if [[ "$dir_name" == "mediafiles" && "$(basename "$subitem")" == "default.jpg" ]]; then
                    continue
                fi
                if [[ -d "$subitem" ]]; then
                    rm -rf "$subitem"
                    log_action "$subitem"
                    elif [[ -f "$subitem" ]]; then
                    rm -f "$subitem"
                    log_action "$subitem"
                fi
            done
        fi
        
        # Process subdirectories
        for subitem in "$item"/*; do
            if [[ -e "$subitem" ]]; then
                subitem_name=$(basename "$subitem")
                echo ">> $subitem"
                
                # Clear out the APP MIGRATIONS files
                if [[ "$subitem_name" == "migrations" && -d "$subitem" ]]; then
                    echo ">>> $subitem"
                    for file in "$subitem"/*; do
                        if [[ "$(basename "$file")" != "__init__.py" && -f "$file" ]]; then
                            rm -f "$file"
                            log_action "$file"
                        fi
                    done
                fi
                
                # Clear out the PYCACHE files
                if [[ "$subitem_name" == "__pycache__" && -d "$subitem" ]]; then
                    echo ">>> $subitem"
                    for file in "$subitem"/*; do
                        if [[ "$(basename "$file")" != "__init__.py" && -f "$file" ]]; then
                            rm -f "$file"
                            log_action "$file"
                        fi
                    done
                fi
            fi
        done
    fi
done

# Source the virtual environment
if [[ -z "$VIRTUAL_ENV" ]]; then
    # Try to find and activate the virtual environment
    if [[ -f "$root/env/bin/activate" ]]; then
        source "$root/env/bin/activate"
        elif [[ -f "$django_root/env/bin/activate" ]]; then
        source "$django_root/env/bin/activate"
    else
        echo "Could not find virtual environment to activate"
        exit 1
    fi
fi

if ask_yes_no "Do you want to migrate and run the django server?"; then
    if [[ -n "$VIRTUAL_ENV" ]]; then
        export DJANGO_SUPERUSER_USERNAME=admin
        export DJANGO_SUPERUSER_EMAIL=admin@proton.me
        export DJANGO_SUPERUSER_PASSWORD=admin
        python manage.py makemigrations
        python manage.py migrate
        python manage.py createsuperuser --noinput
        
        # Run server in the background, then wait for it with signal handling
        python manage.py runserver 8001 --settings=project.settings.development &
        SERVER_PID=$!
        
        # Trap Ctrl+C to only kill the server, not the script
        trap "kill -SIGINT $SERVER_PID" SIGINT
        
        # Wait for the server to exit
        wait $SERVER_PID
        echo "Server has been stopped."
    fi
fi

# Get the path to the current virtual environment's Python interpreter
if [ -n "$VIRTUAL_ENV" ]; then
    VENV_PYTHON_PATH="$VIRTUAL_ENV/bin/python"
    echo "Virtual environment Python path: $VENV_PYTHON_PATH"
    
    # Find all PIDs using this Python interpreter
    PIDS=$(pgrep -f "$VENV_PYTHON_PATH")
    
    if [ -n "$PIDS" ]; then
        echo "Found processes running in this virtual environment (PIDs):"
        for PID in $PIDS; do
            # Get more info about each process
            COMMAND=$(ps -p $PID -o cmd=)
            echo "Killing PID: $PID | Command: $COMMAND"
            kill $PID
        done
        
        # Wait a moment for processes to terminate
        sleep 1
        
        # Check for and force kill any remaining processes
        REMAINING_PIDS=$(pgrep -f "$VENV_PYTHON_PATH")
        if [ -n "$REMAINING_PIDS" ]; then
            echo "Some processes didn't terminate, forcing kill..."
            for PID in $REMAINING_PIDS; do
                COMMAND=$(ps -p $PID -o cmd=)
                echo "Force killing PID: $PID | Command: $COMMAND"
                kill -9 $PID
            done
        fi
        
        echo "All processes in virtual environment terminated."
    else
        echo "No active processes found running in this virtual environment"
    fi
else
    echo "Not currently in a virtual environment - nothing to kill"
fi