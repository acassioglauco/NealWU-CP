#!/usr/bin/env bash

# Configuration
TEMPLATE_DIR='.template'
PARENT_FILE='$PARENT'
DEFAULT_TEMPLATE="/home/parallels/Sublime/template.cc"

# Utility function to search up directories for template
search_up() {
    while [[ $PWD != "/" ]]; do
        if [[ -e "$1" ]]; then
            pwd
            if [[ ! -e "$1/$2" ]]; then
                break
            fi
        fi
        cd ..
    done
}

# Select appropriate rename command
if hash rename.ul 2>/dev/null; then
    RENAME=rename.ul
else
    RENAME=rename
fi

# Find all template directories
IFS=$'\n'
TEMPLATE_DIRS=($(search_up "$TEMPLATE_DIR" "$PARENT_FILE" || tac))
unset IFS
TEMPLATE_DIRS=(${TEMPLATE_DIRS[@]/%/\/"$TEMPLATE_DIR"})

create_problem() {
    local filepath="$1"
    local PROBLEM_NAME=$(basename "$filepath")
    
    if [[ -e "$filepath" ]]; then
        echo "Warning: $filepath already exists. Skipping."
        return
    fi

    # Create directory
    mkdir -p "$filepath"
    
    # Remove parent file if it exists
    rm -f "$filepath/$PARENT_FILE"
    
    # Create source file using .cc extension
    cat "$DEFAULT_TEMPLATE" > "$filepath/sol.cc"
    echo "Created '$PROBLEM_NAME/sol.cc' file"
    
    # Run setup script if it exists
    if [[ -e "$filepath/setup" ]]; then
        echo "Running setup script..."
        (cd "$filepath" && ./setup)
    fi
}

# Main execution
for problem in "$@"; do
    create_problem "$problem"
done

