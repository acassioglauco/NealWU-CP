#!/bin/bash

# Enhanced Test Runner Script with Performance and Flexibility Improvements

# Extended Constants
COMPILER="g++"
BASE_FLAGS="-std=c++20 -Wshadow -Wall -Wextra -O2 -Wno-unused-result"
TIME_LIMIT=1  # Time limit in seconds

# Logging Configuration
#LOG_DIR="test_logs"
#LOG_FILE="${LOG_DIR}/test_results_$(date +%Y%m%d_%H%M%S).log"

# Create log directory
#mkdir -p "$LOG_DIR"
#exec > >(tee -a "$LOG_FILE") 2>&1

# Enhanced Language Detection
declare -A LANGUAGE_COMPILERS=(
    [cc]="g++"
    [cpp]="g++"
    [c]="gcc"
    [py]="python3"
)

# Advanced Time Calculation Function
calculate_time_ms() {
    local start_time=$1
    local end_time=$2

    local elapsed_ns=$((end_time - start_time))
    local time_ms=$((elapsed_ns / 1000000))

    echo $time_ms
}

# Usage Instructions with More Detailed Guidance
show_usage() {
    echo "Usage: $0 <problem_name> [extra_flags]"
    echo "Optional flags:"
    echo "  --debug     Enable debug mode"
    echo "  --verbose   Show additional detailed information"
    exit 1
}

# Robust Input File Detection
check_input_files() {
    local problem=$1
    local input_files="${problem}-*.in"
    if ! compgen -G "$input_files" > /dev/null; then
        echo -e "\033[1;31m[ERROR] No input files found for pattern: ${input_files}\033[0m"
        exit 1
    fi
}

# Enhanced Flag Setup with More Flexibility
setup_flags() {
    local extra_flags=$1
    local debug_mode=$2
    local verbose_mode=$3
    local debug_flag=""
    local verbose_flag=""
    
    if [[ $debug_mode -eq 1 ]] || [[ "$extra_flags" == *"--debug"* ]]; then
        debug_flag="-DDEBUG"
    fi
    
    if [[ $verbose_mode -eq 1 ]] || [[ "$extra_flags" == *"--verbose"* ]]; then
        verbose_flag="-DVERBOSE"
    fi
    
    extra_flags=${extra_flags/--debug/}
    extra_flags=${extra_flags/--verbose/}
    
    echo "${BASE_FLAGS} ${debug_flag} ${verbose_flag} ${extra_flags}"
}

# Smart Compiler Detection
detect_compiler() {
    local problem="$1"
    local source_file=$(find . -maxdepth 1 -type f -name "${problem}.*" | head -1)
    local ext="${source_file##*.}"
    
    echo "${LANGUAGE_COMPILERS[$ext]:-$COMPILER}"
}

# Compilation with Enhanced Diagnostics
compile_program() {
    local problem=$1
    local flags=$2
    local cpp_version=$(echo "$BASE_FLAGS" | grep -oP "(?<=-std=c\+\+)[0-9]+")
    local compiler=$(detect_compiler "$problem")
    
    echo -e "\033[1;32m[DEBUG MODE]\033[0m Compiling ${problem}.cc with c++${cpp_version}."
    echo "[DEBUG] Executing compilation command: $compiler $flags ${problem}.cc -o $problem"
    
    $compiler $flags ${problem}.cc -o $problem
    if [ $? -ne 0 ]; then
        echo -e "\033[1;31m[ERROR] Failed to compile ${problem}.cc.\033[0m"
        exit 1
    fi
}

# Interactive Debugging Mode
run_interactive() {
    local problem=$1
    echo "[DEBUG MODE] Compilation finished. Program is ready for debugging."
    echo "Type the problem input and press Enter to continue..."
    ./$problem
}

# Advanced Output Comparison
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
    
    if [[ $output_length -ne $expected_length ]]; then
        echo -e "\033[1;31m[ERROR] Output has $output_length values, expected $expected_length values\033[0m"
        return 1
    fi
    
    local differences_found=0
    
    for ((i=0; i<output_length; i++)); do
        if [[ "${output_array[$i]}" != "${expected_array[$i]}" ]]; then
            echo -e "Mismatch at $((i+1))-th value: ${output_array[$i]} (run_sample_output-$testname.txt) vs ${expected_array[$i]} ($testname.out)"
            differences_found=1
        fi
    done
    
    return $differences_found
}

# Performance-Enhanced Test Case Runner
run_test_case() {
    local problem=$1
    local testcase=$2
    local testname=$(basename $testcase .in)
    local output_file="run_sample_output-${testname}.txt"
    
    echo "Running $testname:"
    
    local start_time=$(date +%s%N)

    timeout $TIME_LIMIT ./$problem < $testcase > "$output_file"
    local exit_status=$?

    local end_time=$(date +%s%N)

    if [ $exit_status -eq 124 ]; then
        echo -e "\033[1;31m[TLE] Time Limit Exceeded ($TIME_LIMIT seconds)\033[0m"
        return 1
    fi
    
    local time_ms=$(calculate_time_ms $start_time $end_time)
    local time_sec=$(printf "%.2f" $(echo "scale=2; $time_ms / 1000" | bc))

    local memory_output
    memory_output=$( ( /usr/bin/time -f "%M" ./$problem < $testcase > /dev/null ) 2>&1 )
    local memory=$memory_output

    echo "Memory: ${memory} KB"
    echo "Time: ${time_sec}s (${time_ms}ms)"

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

# Enhanced Results Presentation
show_results() {
    local passed=$1
    local total=$2
    
    if [[ $total -eq 0 ]]; then
        echo -e "\033[1;31m[ERROR] No valid test cases were found.\033[0m"
    else
        echo -e "\033[1;32m$passed / $total tests passed!\n\033[0m"
    fi
}

# Main Execution with Improved Flexibility
main() {
    if [ $# -lt 1 ]; then
        show_usage
    fi
    
    local problem=$1
    local extra_flags=${2:-}
    local INTERACTIVE_MODE=0
    local VERBOSE_MODE=0
    
    if [[ "$@" == *"--debug"* ]]; then
        INTERACTIVE_MODE=1
        echo "[DEBUG MODE] Debugging enabled!"
    fi
    
    if [[ "$@" == *"--verbose"* ]]; then
        VERBOSE_MODE=1
        echo "[VERBOSE MODE] Additional information enabled!"
    fi
    
    check_input_files "$problem"
    
    local FLAGS=$(setup_flags "$extra_flags" $INTERACTIVE_MODE $VERBOSE_MODE)
    echo "[DEBUG] Compilation flags: '$FLAGS'"
    
    compile_program "$problem" "$FLAGS"
    
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

# Execute main function with all arguments
main "$@"






