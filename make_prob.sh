#!/bin/bash

# Constants
COMPILER="g++"
BASE_FLAGS="-std=c++20 -Wshadow -Wall -Wextra -O2 -Wno-unused-result"
TIME_LIMIT=1  # Time limit in seconds

# Function to display usage instructions
show_usage() {
    echo "Usage: $0 <problem_name> [extra_flags]"
    exit 1
}

# Function to get source file extension and path
get_source_file() {
    local problem=$1
    local cpp_file="${problem}.cpp"
    local cc_file="${problem}.cc"
    
    if [[ -f $cpp_file ]]; then
        echo $cpp_file
    elif [[ -f $cc_file ]]; then
        echo $cc_file
    else
        echo ""
    fi
}

# Function to check if input files exist
check_input_files() {
    local problem=$1
    local input_files="${problem}-*.in"
    if ! ls $input_files 1> /dev/null 2>&1; then
        echo "[ERROR] No input files found for pattern: ${input_files}"
        exit 1
    fi
}

# Function to check if source file exists
check_source_file() {
    local problem=$1
    local source_file=$(get_source_file "$problem")
    
    if [[ -z $source_file ]]; then
        echo "[ERROR] No source file found. Expected ${problem}.cpp or ${problem}.cc"
        exit 1
    fi
    
    echo $source_file
}

# Function to setup compilation flags
setup_flags() {
    local extra_flags=$1
    local debug_mode=$2
    local debug_flag=""
    
    if [[ $debug_mode -eq 1 ]] || [[ "$extra_flags" == *"--debug"* ]]; then
        debug_flag="-DDEBUG"
    fi
    
    extra_flags=${extra_flags/--debug/}
    
    echo "${BASE_FLAGS} ${debug_flag} ${extra_flags}"
}

# Function to compile the program
compile_program() {
    local problem=$1
    local flags=$2
    local source_file=$3
    local extension="${source_file##*.}"
    local cpp_version=$(echo "$BASE_FLAGS" | grep -oP "(?<=-std=c\+\+)[0-9]+")
    
    echo -e "\033[1;32m[DEBUG MODE]\033[0m Compiling ${source_file} with c++${cpp_version}."
    echo "[DEBUG] Executing compilation command: $COMPILER $flags ${source_file} -o $problem"
    
    $COMPILER $flags ${source_file} -o $problem
    if [ $? -ne 0 ]; then
        echo "[ERROR] Failed to compile ${source_file}."
        exit 1
    fi
}

# Function to run interactive mode
run_interactive() {
    local problem=$1
    echo "[DEBUG MODE] Compilation finished. Program is ready for debugging."
    echo "Type the problem input and press Enter to continue..."
    ./$problem
}

# Function to compare outputs line by line
compare_outputs() {
    local output_file=$1
    local expected_file=$2
    local testname=$3
    
    mapfile -t output_words < <(cat "$output_file" | tr -d '\r' | tr '\n' ' ' | tr -s ' ' | sed 's/ $//')
    mapfile -t expected_words < <(cat "$expected_file" | tr -d '\r' | tr '\n' ' ' | tr -s ' ' | sed 's/ $//')
    
    IFS=' ' read -ra output_array <<< "${output_words[0]}"
    IFS=' ' read -ra expected_array <<< "${expected_words[0]}"
    
    local output_length=${#output_array[@]}
    local expected_length=${#expected_array[@]}
    
    # Verificar se há diferença no número de valores
    if [[ $output_length -ne $expected_length ]]; then
        echo -e "\033[1;31m[ERROR] Output has ${output_length} values but expected ${expected_length}\033[0m"
        return 1
    fi
    
    local differences_found=0
    
    for ((i=0; i<output_length; i++)); do
        if [[ "${output_array[$i]}" != "${expected_array[$i]}" ]]; then
            echo -e "\033[1;31mMismatch at $((i+1))-th value: ${output_array[$i]} (run_sample_output-$testname.txt) vs ${expected_array[$i]} ($testname.out)\033[0m"
            differences_found=1
        fi
    done
    
    return $differences_found
}

# Function to run a single test case
run_test_case() {
    local problem=$1
    local testcase=$2
    local testname=$(basename $testcase .in)
    local output_file="run_sample_output-${testname}.txt"
    
    echo "Running $testname:"
    
    timeout $TIME_LIMIT ./$problem < $testcase > "$output_file"
    local exit_status=$?
    
    if [ $exit_status -eq 124 ]; then
        echo -e "\033[1;31m[TLE] Time Limit Exceeded ($TIME_LIMIT seconds)\033[0m"
        return 1
    fi
    
    /usr/bin/time -f "Memory: %M KB\nTime: %es" -o "${testname}.time" ./$problem < $testcase > /dev/null 2>&1
    cat "${testname}.time"
    
    local answer_file="${testname}.ans"
    if [[ ! -f $answer_file ]]; then
        answer_file="${testname}.out"
    fi
    
    if [[ -f $answer_file ]]; then
        echo "------------------------------------------"
        echo "Output:"
        cat "$output_file"
        echo "------------------------------------------"
        echo "Expected:"
        cat "$answer_file"
        echo "------------------------------------------"
        
        if ! compare_outputs "$output_file" "$answer_file" "$testname"; then
            echo -e "\033[1;31mFailed!\n\033[0m"
            return 1
        fi
        
        echo -e "\033[1;32mPassed!\n\033[0m"
        return 0
    else
        echo "[WARNING] Expected output file missing: ${testname}.ans or ${testname}.out"
        return 1
    fi
}

# Function to display final results
show_results() {
    local passed=$1
    local total=$2
    
    if [[ $total -eq 0 ]]; then
        echo "[ERROR] No valid test cases were found."
    else
        echo -e "\033[1;32m$passed / $total tests passed!\n\033[0m"
    fi
}

# Main execution
main() {
    if [ $# -lt 1 ]; then
        show_usage
    fi
    
    local problem=$1
    local extra_flags=${2:-}
    local INTERACTIVE_MODE=0
    
    if [[ "$@" == *"--debug"* ]]; then
        INTERACTIVE_MODE=1
        echo "[DEBUG MODE] Debugging enabled!"
    fi
    
    check_input_files "$problem"
    
    local source_file=$(check_source_file "$problem")
    local FLAGS=$(setup_flags "$extra_flags" $INTERACTIVE_MODE)
    echo "[DEBUG] Compilation flags: '$FLAGS'"
    
    compile_program "$problem" "$FLAGS" "$source_file"
    
    if [ $INTERACTIVE_MODE -eq 1 ]; then
        run_interactive "$problem"
        exit 0
    fi
    
    local passed=0
    local total=0
    
    for testcase in ${problem}-*.in; do
        total=$((total + 1))
        if run_test_case "$problem" "$testcase"; then
            passed=$((passed + 1))
        fi
    done
    
    show_results $passed $total
    
    rm -f $problem run_sample_output-${problem}-*.txt ${problem}-*.time
}

main "$@"






