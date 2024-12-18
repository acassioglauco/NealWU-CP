#!/usr/bin/env python3
"""Download and setup problems from Competitive Companion

Usage:
  download_prob.py --echo
  download_prob.py [<name>... | -n <number> | -b <batches> | --timeout <timeout>] [--dryrun]

Options:
  -h --help     Show this screen.
  --echo        Just echo received responses and exit.
  --dryrun      Don't actually create any problems

Download limit options:
  -n COUNT, --number COUNT   Number of problems.
  -b COUNT, --batches COUNT  Number of batches. (Default 1 batch)
  -t TIME, --timeout TIME    Timeout for listening to problems. in seconds
"""

from docopt import docopt
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass
from typing import List, Optional, Dict
import http.server
import json
import subprocess
import re
import os
import shutil

class Colors:
    """ANSI color codes for terminal output"""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

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

@dataclass
class ProblemMetadata:
    """Problem metadata from Competitive Companion"""
    name: str
    group: str
    url: str
    time_limit: int
    memory_limit: int
    batch_id: str
    batch_size: int
    tests: List[Dict[str, str]]

    @classmethod
    def from_json(cls, data: dict) -> 'ProblemMetadata':
        return cls(
            name=data['name'],
            group=cls.format_group_name(data['group']),
            url=data['url'],
            time_limit=data['timeLimit'],
            memory_limit=data['memoryLimit'],
            batch_id=data['batch']['id'],
            batch_size=data['batch']['size'],
            tests=data['tests']
        )

    @staticmethod
    def format_group_name(group: str) -> str:
        """Format group name according to the online judge"""
        # Extract the judge name from the group
        judges = {
            'Codeforces': r'Codeforces',
            'AtCoder': r'AtCoder',
            'CodeChef': r'CodeChef',
            'SPOJ': r'SPOJ',
            'UVA': r'UVA',
            'Kattis': r'Kattis',
            'BRSPOJ': r'BRSPOJ',
            'VJudge': r'VJudge'
        }

        # Remove any leading/trailing spaces and dashes
        group = group.strip(' -')

        for judge, pattern in judges.items():
            if re.search(pattern, group, re.IGNORECASE):
                # Extract the contest part (everything after the judge name and possible dash)
                contest_part = re.sub(f'^{pattern}\s*-?\s*', '', group, flags=re.IGNORECASE)
                return f"{judge}/{contest_part}"

        # If no known judge is found, return the group name as is
        return group

class ProblemHandler:
    """Handles problem creation and file management"""
    
    TEMPLATE_FILE = '/home/parallels/Sublime/template.cc'
    
    def __init__(self, base_dir: Path = Path('.')):
        self.base_dir = base_dir
        self.created_files = []  # Changed to list to track individual files
        self.failed_files = []

    def generate_file_header(self, metadata: ProblemMetadata) -> str:
        """Generate file header with problem information"""
        current_time = datetime.now().strftime("%d/%m/%Y às %H:%M:%S")
        return f"""// author: glaucoacassioc
// created on: {current_time}

// Problem: {metadata.name}
// URL: {metadata.url}
// Time Limit: {metadata.time_limit} ms
// Memory Limit: {metadata.memory_limit} MB

"""

    def create_problem_files(self, metadata: ProblemMetadata, manual_mode: bool = False) -> None:
        """Create all necessary problem files"""
        try:
            # Create contest directory
            contest_dir = self.base_dir / metadata.group
            contest_dir.mkdir(parents=True, exist_ok=True)
            
            # Track created directories
            if not contest_dir.exists():
                for parent in contest_dir.parents:
                    if not parent.exists():
                        self.created_files.append(str(parent))
                self.created_files.append(str(contest_dir))
            
            # Extract problem letter/number from the name
            problem_id = metadata.name.split()[0].split('.')[0]
            
            # Create source file
            if manual_mode:
                source_file = contest_dir / 'sol.cc'
            else:
                file_name = f"{problem_id}.cc"
                source_file = contest_dir / file_name

            if not source_file.exists():
                shutil.copyfile(self.TEMPLATE_FILE, source_file)
                with open(source_file, 'r+') as f:
                    content = f.read()
                    f.seek(0)
                    f.write(self.generate_file_header(metadata) + content)
                self.created_files.append(str(source_file))
                print(Colors.success(f"Create mode {source_file}"))

            # Copy gen_cf.py to the contest directory
            gen_cf_source = Path('/home/parallels/Sublime/gen_cf.py')
            gen_cf_dest = contest_dir / 'gen_cf.py'
            
            if gen_cf_source.exists():
                shutil.copyfile(gen_cf_source, gen_cf_dest)
                self.created_files.append(str(gen_cf_dest))
                #print(Colors.success(f"Create mode {gen_cf_dest}"))
            else:
                print(Colors.warning(f"gen_cf.py not found at {gen_cf_source}"))

            # Create test cases
            self._save_test_cases(contest_dir, metadata.tests, problem_id)
            
            # Abrir arquivos e pasta no Sublime
            self.open_in_sublime(contest_dir)
            
        except Exception as e:
            print(Colors.error(f"Failed to make problem {metadata.name}: {e}"))
            self.failed_files.append(metadata.name)

    def _save_test_cases(self, contest_dir: Path, tests: List[Dict[str, str]], problem_id: str) -> None:
        """Save test cases to files using problem ID as prefix"""
        for i, test in enumerate(tests, 1):
            # Create input file
            in_file = contest_dir / f'{problem_id}-{i}.in'
            if not in_file.exists():
                with open(in_file, 'w') as f:
                    f.write(test['input'])
                self.created_files.append(str(in_file))
                print(Colors.success(f"Create input file: {in_file}"))

            # Create output file
            out_file = contest_dir / f'{problem_id}-{i}.out'
            if not out_file.exists():
                with open(out_file, 'w') as f:
                    f.write(test['output'])
                self.created_files.append(str(out_file))
                print(Colors.success(f"Create output file: {out_file}"))

    def open_in_sublime(self, directory: Path):
        """Open the created problem directory in Sublime Text"""
        try:
            # Listar arquivos .cc no diretório e ordenar
            cc_files = sorted(
                list(directory.rglob('*.cc')), 
                key=lambda f: f.name  # Ordena pelo nome do arquivo
            )
            
            # Comando para abrir Sublime com a pasta do contest
            # e adicionar todos os arquivos .cc em abas
            if cc_files:
                subprocess.run(['subl', '-a', str(directory)] + [str(f) for f in cc_files], check=True)
            else:
                print(Colors.warning(f"No .cc file found in the directory {directory}"))
        except subprocess.CalledProcessError as e:
            print(f"Error while executing Sublime command: {e}")
        except Exception as e:
            print(f"Unknown error while opening Sublime: {e}")

    def print_summary(self):
        """Print summary of files created and any failures"""
        print(Colors.success(f"\nTotal files created: {len(self.created_files)}"))
        if self.failed_files:
            for name in self.failed_files:
                print(Colors.error(f"Failed to make problem {name}"))

class CompetitiveCompanionServer:
    """Server to receive problems from Competitive Companion"""
    
    def __init__(self, port: int = 10046):
        self.port = port
        
    def listen_once(self, timeout: Optional[float] = None) -> Optional[dict]:
        """Listen for one problem submission"""
        json_data = None

        class Handler(http.server.BaseHTTPRequestHandler):
            def do_POST(self):
                nonlocal json_data
                json_data = json.load(self.rfile)
                self.send_response(200)
                self.end_headers()

        with http.server.HTTPServer(('127.0.0.1', self.port), Handler) as server:
            server.timeout = timeout
            server.handle_request()

        return json_data

    def listen_many(self, *, num_items: Optional[int] = None,
                   num_batches: Optional[int] = None,
                   timeout: Optional[float] = None) -> List[dict]:
        """Listen for multiple problem submissions"""
        if num_items is not None:
            return [self.listen_once() for _ in range(num_items)]

        if num_batches is not None:
            results = []
            batches = {}
            
            while len(batches) < num_batches or any(need for need, _ in batches.values()):
                data = self.listen_once()
                if data is None:
                    break
                    
                results.append(data)
                batch_id = data['batch']['id']
                batch_size = data['batch']['size']
                
                if batch_id not in batches:
                    batches[batch_id] = [batch_size, batch_size]
                batches[batch_id][0] -= 1

            return results

        results = [self.listen_once()]
        while True:
            data = self.listen_once(timeout=timeout)
            if data is None:
                break
            results.append(data)
        
        return results

def print_initial_instructions():
    """Print instructions for using Competitive Companion"""
    instructions = f"""{Colors.HEADER}🏁 Competitive Companion Problem Downloader 🏁{Colors.END}

{Colors.OKBLUE}SETUP INSTRUCTIONS:{Colors.END}

1. {Colors.OKGREEN}Install Competitive Companion Browser Extension{Colors.END}
   - Available for Chrome and Firefox
   - Search "Competitive Companion" in your browser's extension store

2. {Colors.OKGREEN}Configure Extension Port{Colors.END}
   - Open Competitive Companion extension settings
   - Set Local Port to: {Colors.WARNING}10046{Colors.END}

3. {Colors.OKGREEN}Workflow{Colors.END}
   - Start this script
   - Go to an online judge (Codeforces, AtCoder, etc.)
   - Open a problem page
   - Click Competitive Companion extension icon

{Colors.HEADER}USAGE EXAMPLES:{Colors.END}
   {Colors.OKBLUE}• Download 1 problem:     {Colors.END}python3 download_prob.py
   {Colors.OKBLUE}• Download 3 problems:    {Colors.END}python3 download_prob.py -n 3
   {Colors.OKBLUE}• Download 2 batches:     {Colors.END}python3 download_prob.py -b 2
   {Colors.OKBLUE}• Dry run (preview only): {Colors.END}python3 download_prob.py --dryrun

{Colors.WARNING}Waiting for Competitive Companion problem...{Colors.END}
"""
    print(instructions)

def main():
    arguments = docopt(__doc__)
    
    # If no specific arguments are provided, show instructions
    if all(not arguments[key] for key in ['--echo', '<name>', '--number', '--batches', '--timeout']):
        print_initial_instructions()
    
    server = CompetitiveCompanionServer()
    handler = ProblemHandler()

    if arguments['--echo']:
        while True:
            data = server.listen_once()
            print(json.dumps(data, indent=2))
    else:
        dryrun = arguments['--dryrun']

        def process_problem(data: dict, manual_name: Optional[str] = None):
            if dryrun:
                print(f"Would create problem: {data['name']}")
                return
                
            metadata = ProblemMetadata.from_json(data)
            handler.create_problem_files(metadata, manual_mode=manual_name is not None)

        if names := arguments['<name>']:
            datas = server.listen_many(num_items=len(names))
            for data, name in zip(datas, names):
                process_problem(data, name)
        elif cnt := arguments['--number']:
            datas = server.listen_many(num_items=int(cnt))
            for data in datas:
                process_problem(data)
        elif batches := arguments['--batches']:
            datas = server.listen_many(num_batches=int(batches))
            for data in datas:
                process_problem(data)
        elif timeout := arguments['--timeout']:
            datas = server.listen_many(timeout=float(timeout))
            for data in datas:
                process_problem(data)
        else:
            datas = server.listen_many(num_batches=1)
            for data in datas:
                process_problem(data)

        handler.print_summary()

if __name__ == '__main__':
    main()



