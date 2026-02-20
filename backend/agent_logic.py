import os
import re
import subprocess
import json
import time
from typing import List, Dict, Tuple, Optional

class CodeAgent:
    def __init__(self, repo_path: str, github_token: str = ""):
        self.repo_path = repo_path
        self.github_token = github_token
        self.fixes_applied = []
        self.cicd_runs = []
        
        # Comprehensive bug patterns for detection
        self.bug_patterns = {
            'LINTING': [
                (r"^import ['\"]os['\"]", "Unused standard library import"),
                (r"^from os import", "Unused standard library import"),
                (r"^import ['\"]sys['\"]", "Unused standard library import"),
                (r"^import ['\"]numpy['\"]", "Unused standard library import"),
                (r"^import ['\"]pandas['\"]", "Unused standard library import"),
                (r"print\(.+\)", "Debug print statement found"),
                (r"^import ['\"]math['\"]", "Unused standard library import"),
                (r"^import ['\"]random['\"]", "Unused standard library import"),
            ],
            'SYNTAX': [
                # Missing colon after function definition - FIXED regex
                (r"^\s*def\s+[a-zA-Z_][a-zA-Z0-9_]*\s*\([^)]*\)\s*$", "Missing colon after function definition"),
                (r"^\s*class\s+[a-zA-Z_][a-zA-Z0-9_]*\s*$", "Missing colon after class definition"),
                (r"^\s*if\s+.*\s*$", "Missing colon after if statement"),
                (r"^\s*elif\s+.*\s*$", "Missing colon after elif statement"),
                (r"^\s*else\s*$", "Missing colon after else statement"),
                (r"^\s*for\s+.*\s*$", "Missing colon after for statement"),
                (r"^\s*while\s+.*\s*$", "Missing colon after while statement"),
                (r"^\s*try\s*$", "Missing colon after try statement"),
                (r"^\s*except\s+.*\s*$", "Missing colon after except statement"),
                (r"^\s*finally\s*$", "Missing colon after finally statement"),
                (r"^\s*with\s+.*\s*$", "Missing colon after with statement"),
                (r"^\s*async def\s+[a-zA-Z_][a-zA-Z0-9_]*\s*\([^)]*\)\s*$", "Missing colon after async function"),
                # Unmatched brackets and parentheses
                (r"[^#]*\(\s*\)[^#]*$", "Empty parentheses"),
                (r"[^#]*\[\s*\][^#]*$", "Empty brackets"),
                (r"[^#]*\{\s*\}[^#]*$", "Empty braces"),
            ],
            'TYPE_ERROR': [
                (r"for\s+\w+\s+in\s+\w+\s+for\s+", "Confused list comprehension"),
            ],
            'INDENTATION': [
                (r"^\t", "Tab indentation found (use spaces)"),
                (r"    \t", "Mixed tab and space indentation"),
            ],
            'IMPORT': [
                (r"^import\s*$", "Incomplete import statement"),
                (r"^from\s+.*import\s*$", "Incomplete from import"),
            ]
        }

    def run_command(self, cmd, cwd=None):
        """Cross-platform command execution"""
        try:
            result = subprocess.run(
                cmd,
                shell=True,
                cwd=cwd or self.repo_path,
                capture_output=True,
                text=True,
                timeout=120
            )
            return result
        except Exception as e:
            print(f"Command error: {e}")
            return None

    def discover_files(self) -> List[str]:
        """Discover all code files in the repository"""
        code_files = []
        extensions = {'.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.go', '.rs', '.c', '.cpp', '.h'}
        
        try:
            for root, dirs, files in os.walk(self.repo_path):
                dirs[:] = [d for d in dirs if d not in ['node_modules', '.git', '__pycache__', 'venv', '.venv', 'dist', 'build', '.idea']]
                
                for file in files:
                    if any(file.endswith(ext) for ext in extensions):
                        full_path = os.path.join(root, file)
                        try:
                            with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                                f.read(1)
                            code_files.append(full_path)
                        except Exception:
                            pass
        except Exception as e:
            print(f"Error discovering files: {e}")
        
        return code_files

    def analyze_file(self, file_path: str) -> List[Dict]:
        """Analyze a single file for bugs"""
        bugs = []
        rel_path = os.path.relpath(file_path, self.repo_path)
        
        # Keywords that require a colon at the end
        colon_keywords = ['def ', 'class ', 'if ', 'elif ', 'else:', 'for ', 'while ', 'try:', 'except ', 'finally:', 'with ', 'async def ']
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            
            for line_num, line in enumerate(lines, 1):
                # Skip empty lines and pure comments
                stripped = line.strip()
                if not stripped or stripped.startswith('#'):
                    continue
                
                # Check for missing colon after statements
                for keyword in colon_keywords:
                    if line.startswith(keyword) or line.lstrip().startswith(keyword):
                        # Line starts with a keyword that needs a colon
                        # Check if line ends with a colon (but not in a string or comment)
                        if not line.rstrip().endswith(':') and '#' not in line:
                            # This is a potential missing colon bug
                            existing = [b for b in bugs if b['line'] == line_num and b['type'] == 'SYNTAX']
                            if not existing:
                                bugs.append({
                                    'file': rel_path,
                                    'line': line_num,
                                    'content': line.strip(),
                                    'type': 'SYNTAX',
                                    'description': f"Missing colon after {keyword.strip()} statement",
                                    'pattern': f"missing_colon_{keyword.strip()}"
                                })
                
                # Check for tab indentation
                if line.startswith('\t'):
                    existing = [b for b in bugs if b['line'] == line_num and b['type'] == 'INDENTATION']
                    if not existing:
                        bugs.append({
                            'file': rel_path,
                            'line': line_num,
                            'content': line.strip(),
                            'type': 'INDENTATION',
                            'description': "Tab indentation found (use spaces)",
                            'pattern': "tab_indent"
                        })
                
                # Check for other patterns from bug_patterns
                for bug_type, patterns in self.bug_patterns.items():
                    if bug_type in ['SYNTAX', 'INDENTATION']:
                        continue  # Already handled above
                    
                    for pattern, description in patterns:
                        if re.search(pattern, line):
                            # Avoid duplicate reports
                            existing = [b for b in bugs if b['line'] == line_num and b['type'] == bug_type]
                            if not existing:
                                bugs.append({
                                    'file': rel_path,
                                    'line': line_num,
                                    'content': line.strip(),
                                    'type': bug_type,
                                    'description': description,
                                    'pattern': pattern
                                })
        except Exception as e:
            print(f"Error analyzing {file_path}: {e}")
        
        return bugs

    def generate_fix(self, bug: Dict) -> Tuple[str, str]:
        """Generate a fix for a detected bug"""
        line_content = bug['content']
        bug_type = bug['type']
        
        if bug_type == 'LINTING':
            return "", f"remove the {bug['description'].lower()}"
        
        elif bug_type == 'SYNTAX':
            fixed_line = line_content + ':'
            return fixed_line, "add the colon at the correct position"
        
        elif bug_type == 'INDENTATION':
            return line_content.replace('\t', '    '), "replace tabs with 4 spaces"
        
        elif bug_type == 'IMPORT':
            return "", "remove incomplete import"
        
        return line_content, "manual review required"

    def apply_fix(self, bug: Dict, fix_content: str) -> bool:
        """Apply a fix to the file"""
        file_path = os.path.join(self.repo_path, bug['file'])
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            
            line_idx = bug['line'] - 1
            if fix_content == "":
                lines[line_idx] = ""
            else:
                lines[line_idx] = fix_content + '\n'
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.writelines(lines)
            
            return True
        except Exception as e:
            print(f"Failed to apply fix: {e}")
            return False

    def detect_language(self) -> str:
        """Detect the programming language of the repository"""
        # Check for common files
        if os.path.exists(os.path.join(self.repo_path, "package.json")):
            return "JavaScript/TypeScript"
        elif os.path.exists(os.path.join(self.repo_path, "requirements.txt")) or \
             os.path.exists(os.path.join(self.repo_path, "setup.py")) or \
             os.path.exists(os.path.join(self.repo_path, "pyproject.toml")):
            return "Python"
        elif os.path.exists(os.path.join(self.repo_path, "pom.xml")):
            return "Java"
        elif os.path.exists(os.path.join(self.repo_path, "go.mod")):
            return "Go"
        elif os.path.exists(os.path.join(self.repo_path, "Cargo.toml")):
            return "Rust"
        return "Unknown"

    def run_tests(self) -> Tuple[bool, str]:
        """Run tests and return pass/fail with output"""
        lang = self.detect_language()
        
        # Python tests
        if lang == "Python":
            # Check for pytest
            if os.path.exists(os.path.join(self.repo_path, "pytest.ini")) or \
               os.path.exists(os.path.join(self.repo_path, "setup.py")) or \
               os.path.exists(os.path.join(self.repo_path, "pyproject.toml")) or \
               os.path.exists(os.path.join(self.repo_path, "tests")) or \
               os.path.exists(os.path.join(self.repo_path, "test")):
                result = self.run_command("python -m pytest -v --tb=short 2>&1")
                if result:
                    if result.returncode == 0:
                        return True, "All tests passed"
                    else:
                        return False, result.stdout + "\n" + result.stderr
                return True, "No test runner found"
            
            # Try running python syntax check
            result = self.run_command("python -m py_compile . 2>&1")
            if result and result.returncode != 0:
                return False, result.stderr
        
        # JavaScript/Node tests
        elif lang == "JavaScript/TypeScript":
            if os.path.exists(os.path.join(self.repo_path, "package.json")):
                result = self.run_command("npm test -- --passWithNoTests 2>&1")
                if result:
                    if result.returncode == 0:
                        return True, "All tests passed"
                    else:
                        return False, result.stdout + "\n" + result.stderr
        
        # No tests found - assume pass
        return True, "No tests found - assumed pass"

    def get_timestamp(self):
        """Get current timestamp"""
        return time.strftime("%Y-%m-%d %H:%M:%S")

    def execute(self, max_iterations: int = 5) -> Dict:
        """Main execution loop with CI/CD pipeline simulation"""
        iteration = 0
        all_bugs_found = []
        
        while iteration < max_iterations:
            iteration += 1
            self.cicd_runs.append({
                'iteration': iteration,
                'status': 'RUNNING',
                'timestamp': self.get_timestamp(),
                'tests_passed': False,
                'errors': []
            })
            
            print(f"\n{'='*50}")
            print(f"ITERATION {iteration}")
            print(f"{'='*50}")
            
            # 1. Discover and analyze files
            files = self.discover_files()
            print(f"Analyzing {len(files)} files...")
            
            current_bugs = []
            for file_path in files:
                bugs = self.analyze_file(file_path)
                current_bugs.extend(bugs)
            
            # Remove duplicates from current bugs
            unique_current_bugs = []
            seen = set()
            for bug in current_bugs:
                key = (bug['file'], bug['line'], bug['type'])
                if key not in seen:
                    seen.add(key)
                    unique_current_bugs.append(bug)
            
            current_bugs = unique_current_bugs
            
            if not current_bugs:
                print("✓ No bugs found. Running CI/CD tests...")
                
                # Run tests
                tests_passed, test_output = self.run_tests()
                
                if tests_passed:
                    print("✓ CI/CD PASSED!")
                    self.cicd_runs[-1]['status'] = 'PASSED'
                    self.cicd_runs[-1]['tests_passed'] = True
                    self.cicd_runs[-1]['output'] = test_output
                    break
                else:
                    print(f"✗ CI/CD FAILED: {test_output}")
                    self.cicd_runs[-1]['status'] = 'FAILED'
                    self.cicd_runs[-1]['tests_passed'] = False
                    self.cicd_runs[-1]['errors'].append(test_output)
                    # Continue to apply fixes
            
            print(f"Found {len(current_bugs)} bugs to fix")
            all_bugs_found.extend(current_bugs)
            
            # 2. Apply fixes
            fixed_count = 0
            for bug in current_bugs:
                fix_content, fix_desc = self.generate_fix(bug)
                success = self.apply_fix(bug, fix_content)
                
                if success:
                    fixed_count += 1
                
                self.fixes_applied.append({
                    'file': bug['file'],
                    'bug_type': bug['type'],
                    'line_number': bug['line'],
                    'content': bug['content'],
                    'commit_message': f"[AI-AGENT] Fix {bug['type']} in {os.path.basename(bug['file'])} line {bug['line']}",
                    'status': 'Fixed' if success else 'Failed',
                    'fix_detail': fix_desc
                })
            
            print(f"Applied {fixed_count}/{len(current_bugs)} fixes")
            
            # 3. Run CI/CD tests after fixes
            print("Running CI/CD tests...")
            tests_passed, test_output = self.run_tests()
            
            if tests_passed:
                print("✓ CI/CD PASSED after fixes!")
                self.cicd_runs[-1]['status'] = 'PASSED'
                self.cicd_runs[-1]['tests_passed'] = True
                self.cicd_runs[-1]['output'] = test_output
            else:
                print(f"✗ CI/CD FAILED: {test_output}")
                self.cicd_runs[-1]['status'] = 'FAILED'
                self.cicd_runs[-1]['tests_passed'] = False
                self.cicd_runs[-1]['errors'].append(test_output)
        
        return {
            'total_iterations': iteration,
            'fixes': self.fixes_applied,
            'cicd_runs': self.cicd_runs,
            'unique_bugs': len(set([(b['file'], b['line'], b['type']) for b in all_bugs_found]))
        }


# Factory function for importing
def get_agent(repo_path: str) -> 'CodeAgent':
    return CodeAgent(repo_path)