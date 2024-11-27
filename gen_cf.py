#!/usr/bin/env python3

import os
import re
import sys
from typing import Union, List

class Colors:
    """ANSI color codes for terminal output"""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    END = '\033[0m'

    @staticmethod
    def style(text: str, *styles: str) -> str:
        """Apply multiple styles to text"""
        return ''.join(styles) + text + Colors.END

    @classmethod
    def success(cls, text: str) -> str:
        return cls.style(text, cls.OKGREEN)

    @classmethod
    def error(cls, text: str) -> str:
        return cls.style(text, cls.FAIL)

    @classmethod
    def warning(cls, text: str) -> str:
        return cls.style(text, cls.WARNING)

class TestCaseGenerator:
    def __init__(self, problem_identifier: str):
        """
        Initialize the test case generator for a specific problem
        
        Args:
            problem_identifier (str): The identifier for the problem (from .cc filename or directory)
        """
        self.problem_identifier = problem_identifier

    def _get_next_test_case_number(self) -> int:
        """
        Calculate the next available test case number
        
        Returns:
            int: Next available test case number, starting from 2
        """
        existing_files = os.listdir('.')
        test_case_numbers = [
            int(re.search(r'-(\d+)\.in$', f).group(1))
            for f in existing_files
            if re.match(rf'^{re.escape(self.problem_identifier)}-\d+\.in$', f)
        ]
        return max(test_case_numbers, default=1) + 1

    def generate_test_case(self, input_content: Union[str, List], output_content: Union[str, List] = None):
        """
        Generate input and output test case files
        
        Args:
            input_content (Union[str, List]): Content for input test case
            output_content (Union[str, List], optional): Content for output test case
        """
        # Get next test case number
        test_case_number = self._get_next_test_case_number()

        # Create input filename and write input content
        input_filename = f"{self.problem_identifier}-{test_case_number}.in"
        input_text = input_content if isinstance(input_content, str) else '\n'.join(map(str, input_content))
        
        with open(input_filename, 'w') as f:
            f.write(input_text.strip() + '\n')
        print(Colors.success(f"Created input file: {input_filename}"))

        # Create output file if output content is provided
        if output_content is not None:
            output_filename = f"{self.problem_identifier}-{test_case_number}.out"
            output_text = output_content if isinstance(output_content, str) else '\n'.join(map(str, output_content))
            
            with open(output_filename, 'w') as f:
                f.write(output_text.strip() + '\n')
            print(Colors.success(f"Created output file: {output_filename}"))

def get_problem_identifier() -> str:
    """
    Automatically detect problem identifier from .cc file or current directory
    
    Returns:
        str: Problem identifier
    """
    # Try to find .cc file in current directory
    cc_files = [f for f in os.listdir('.') if f.endswith('.cc')]
    if cc_files:
        # Use the first .cc file's name (without extension) as identifier
        return os.path.splitext(cc_files[0])[0]
    
    # If no .cc file, use current directory name
    return os.path.basename(os.getcwd())

def main():
    # Get problem identifier automatically
    problem_identifier = get_problem_identifier()
    
    print(Colors.HEADER + " Test Case Generator " + Colors.END)
    
    # Create generator
    generator = TestCaseGenerator(problem_identifier)
    
    # Read input content from stdin
    print(Colors.WARNING + "Enter input test case content (press Ctrl+D or Ctrl+Z when done):" + Colors.END)
    input_content = []
    try:
        while True:
            line = input()
            input_content.append(line)
    except EOFError:
        input_content = '\n'.join(input_content)
    
    # Optional: read output content
    print(Colors.WARNING + "Enter output test case content (optional, press Ctrl+D or Ctrl+Z when done):" + Colors.END)
    output_content = []
    try:
        while True:
            line = input()
            output_content.append(line)
    except EOFError:
        output_content = '\n'.join(output_content) if output_content else None
    
    # Generate test case
    generator.generate_test_case(input_content, output_content)

if __name__ == '__main__':
    main()



    
