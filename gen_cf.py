#!/usr/bin/env python3

import os
import re
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
    def __init__(self, problem_letter: str):
        """
        Initialize the test case generator for a specific problem letter
        
        Args:
            problem_letter (str): The letter or identifier for the problem
        """
        self.problem_letter = problem_letter

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
            if re.match(rf'^{self.problem_letter}-\d+\.in$', f)
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
        input_filename = f"{self.problem_letter}-{test_case_number}.in"
        input_text = input_content if isinstance(input_content, str) else '\n'.join(map(str, input_content))
        
        with open(input_filename, 'w') as f:
            f.write(input_text.strip() + '\n')
        print(Colors.success(f"Created input file: {input_filename}"))

        # Create output file if output content is provided
        if output_content is not None:
            output_filename = f"{self.problem_letter}-{test_case_number}.out"
            output_text = output_content if isinstance(output_content, str) else '\n'.join(map(str, output_content))
            
            with open(output_filename, 'w') as f:
                f.write(output_text.strip() + '\n')
            print(Colors.success(f"Created output file: {output_filename}"))

def main():
    print(Colors.HEADER + " Test Case Generator " + Colors.END)
    
    # Get problem letter
    while True:
        problem_letter = input(Colors.OKBLUE + "Enter problem letter (A-Z): " + Colors.END).strip().upper()
        if re.match(r'^[A-Z]$', problem_letter):
            break
        print(Colors.error("Invalid input. Please enter a single letter A-Z."))
    
    # Create generator
    generator = TestCaseGenerator(problem_letter)
    
    # Main interaction loop
    while True:
        print("\nChoose input method:")
        print("1. Manual input with manual output")
        print("2. Input as list with list output")
        print("3. Exit")
        
        choice = input(Colors.OKBLUE + "Enter your choice (1-3): " + Colors.END).strip()
        
        if choice == '1':
            print(Colors.WARNING + "Enter input test case content (press Ctrl+D or Ctrl+Z when done):" + Colors.END)
            input_content = []
            try:
                while True:
                    line = input()
                    input_content.append(line)
            except EOFError:
                input_content = '\n'.join(input_content)
                
                # Get output content
                print(Colors.WARNING + "Enter output test case content (press Ctrl+D or Ctrl+Z when done):" + Colors.END)
                output_content = []
                try:
                    while True:
                        line = input()
                        output_content.append(line)
                except EOFError:
                    output_content = '\n'.join(output_content) if output_content else None
                    
                generator.generate_test_case(input_content, output_content)
        
        elif choice == '2':
            print(Colors.WARNING + "Enter input list elements separated by space (can mix types):" + Colors.END)
            input_line = input().strip()
            # Convert input to appropriate types
            input_content = []
            for item in input_line.split():
                try:
                    input_content.append(int(item))
                except ValueError:
                    try:
                        input_content.append(float(item))
                    except ValueError:
                        input_content.append(item)
            
            # Optional output list
            print(Colors.WARNING + "Enter output list elements (optional, press Enter to skip):" + Colors.END)
            output_line = input().strip()
            output_content = None
            if output_line:
                output_content = []
                for item in output_line.split():
                    try:
                        output_content.append(int(item))
                    except ValueError:
                        try:
                            output_content.append(float(item))
                        except ValueError:
                            output_content.append(item)
            
            generator.generate_test_case(input_content, output_content)
        
        elif choice == '3':
            print(Colors.HEADER + "Exiting Test Case Generator. 👋" + Colors.END)
            break
        
        else:
            print(Colors.error("Invalid choice. Please try again."))

if __name__ == '__main__':
    main()





    
