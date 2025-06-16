#!/usr/bin/env python3
"""
🔍 PYTHON REQUIREMENTS SCANNER
Scans all .py files in the project and updates requirements.txt with non-standard libraries.
Only adds packages that are NOT part of Python's standard library.
"""

import os
import ast
import sys
import datetime
from pathlib import Path
import importlib.util
# Python standard library modules (comprehensive list for Python 3.8+)
STANDARD_LIBRARY = {
    'abc', 'aifc', 'argparse', 'array', 'ast', 'asynchat', 'asyncio', 'asyncore',
    'atexit', 'audioop', 'base64', 'bdb', 'binascii', 'binhex', 'bisect', 'builtins',
    'bz2', 'calendar', 'cgi', 'cgitb', 'chunk', 'cmath', 'cmd', 'code', 'codecs', 'config'
    'codeop', 'collections', 'colorsys', 'compileall', 'concurrent', 'configparser',
    'contextlib', 'copy', 'copyreg', 'cProfile', 'crypt', 'csv', 'ctypes', 'curses',
    'dataclasses', 'datetime', 'dbm', 'decimal', 'difflib', 'dis', 'distutils',
    'doctest', 'email', 'encodings', 'ensurepip', 'enum', 'errno', 'faulthandler',
    'fcntl', 'filecmp', 'fileinput', 'fnmatch', 'formatter', 'fractions', 'ftplib',
    'functools', 'gc', 'getopt', 'getpass', 'gettext', 'glob', 'grp', 'gzip',
    'hashlib', 'heapq', 'hmac', 'html', 'http', 'imaplib', 'imghdr', 'imp',
    'importlib', 'inspect', 'io', 'ipaddress', 'itertools', 'json', 'keyword',
    'lib2to3', 'linecache', 'locale', 'logging', 'lzma', 'mailbox', 'mailcap',
    'marshal', 'math', 'mimetypes', 'mmap', 'modulefinder', 'msilib', 'msvcrt',
    'multiprocessing', 'netrc', 'nntplib', 'numbers', 'operator', 'optparse', 'os',
    'ossaudiodev', 'parser', 'pathlib', 'pdb', 'pickle', 'pickletools', 'pipes',
    'pkgutil', 'platform', 'plistlib', 'poplib', 'posix', 'pprint', 'profile',
    'pstats', 'pty', 'pwd', 'py_compile', 'pyclbr', 'pydoc', 'queue', 'quopri',
    'random', 're', 'readline', 'reprlib', 'resource', 'rlcompleter', 'runpy',
    'sched', 'secrets', 'select', 'selectors', 'shelve', 'shlex', 'shutil', 'signal',
    'site', 'smtpd', 'smtplib', 'sndhdr', 'socket', 'socketserver', 'sqlite3',
    'ssl', 'stat', 'statistics', 'string', 'stringprep', 'struct', 'subprocess',
    'sunau', 'symbol', 'symtable', 'sys', 'sysconfig', 'syslog', 'tabnanny',
    'tarfile', 'telnetlib', 'tempfile', 'termios', 'test', 'textwrap', 'threading',
    'time', 'timeit', 'tkinter', 'token', 'tokenize', 'trace', 'traceback',
    'tracemalloc', 'tty', 'turtle', 'turtledemo', 'types', 'typing', 'unicodedata',
    'unittest', 'urllib', 'uu', 'uuid', 'venv', 'warnings', 'wave', 'weakref',
    'webbrowser', 'winreg', 'winsound', 'wsgiref', 'xdrlib', 'xml', 'xmlrpc',
    'zipapp', 'zipfile', 'zipimport', 'zlib'
}

# Package name mappings (import name -> pip package name)
PACKAGE_MAPPINGS = {
    'yaml': 'PyYAML',
    'cv2': 'opencv-python',
    'dotenv': 'python-dotenv',
    'PIL': 'Pillow',
    'bs4': 'beautifulsoup4',
    'sklearn': 'scikit-learn',
    'dateutil': 'python-dateutil',
    'psycopg2': 'psycopg2-binary',
    'MySQLdb': 'mysqlclient',
    'win32com': 'pywin32',
    'win32gui': 'pywin32',
    'win32api': 'pywin32',
}

def extract_imports_from_file(file_path):
    """Extract all import statements from a Python file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        tree = ast.parse(content)
        imports = set()
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    # Get the top-level package name
                    package = alias.name.split('.')[0]
                    imports.add(package)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    # Get the top-level package name
                    package = node.module.split('.')[0]
                    imports.add(package)
        
        return imports
    except Exception as e:
        print(f"⚠️  Error parsing {file_path}: {e}")
        return set()

def find_python_files(base_path):
    """Find all Python files in the project."""
    python_files = []
    base_path = Path(base_path)
    
    for py_file in base_path.rglob('*.py'):
        # Skip __pycache__ and virtual environment directories
        if '__pycache__' in str(py_file) or 'venv' in str(py_file) or '.venv' in str(py_file):
            continue
        python_files.append(py_file)
    
    return python_files

def is_third_party_package(package_name):
    """Check if a package is third-party (not in standard library)."""
    # Skip relative imports and local modules
    if package_name.startswith('.'):
        return False
    
    # Check if it's a standard library module
    if package_name in STANDARD_LIBRARY:
        return False
    
    # Check if it's a local module (exists as a file in the project)
    current_dir = Path.cwd()
    if (current_dir / f"{package_name}.py").exists():
        return False
    if (current_dir / package_name / "__init__.py").exists():
        return False
    
    return True

def get_pip_package_name(import_name):
    """Get the correct pip package name for an import."""
    return PACKAGE_MAPPINGS.get(import_name, import_name)

def read_current_requirements():
    """Read existing requirements.txt file."""
    requirements_file = Path('requirements.txt')
    current_packages = set()
    
    if requirements_file.exists():
        try:
            with open(requirements_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        # Extract package name (before any version specifiers)
                        package = line.split('==')[0].split('>=')[0].split('<=')[0].split('>')[0].split('<')[0].split('~')[0].strip()
                        current_packages.add(package.lower())
        except Exception as e:
            print(f"⚠️  Error reading requirements.txt: {e}")
    
    return current_packages

def update_requirements_file(new_packages):
    """Update requirements.txt with new packages."""
    requirements_file = Path('requirements.txt')
    
    # Read existing content
    existing_lines = []
    if requirements_file.exists():
        try:
            with open(requirements_file, 'r', encoding='utf-8') as f:
                existing_lines = f.readlines()
        except Exception as e:
            print(f"⚠️  Error reading requirements.txt: {e}")
    
    # Add new packages
    if new_packages:
        with open(requirements_file, 'a', encoding='utf-8') as f:
            if existing_lines and not existing_lines[-1].endswith('\n'):
                f.write('\n')
            
            f.write(f'\n# Added by requirements scanner on {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n')
            for package in sorted(new_packages):
                f.write(f'{package}\n')

def main():
    """Main function to scan and update requirements."""
    print("🔍 === PYTHON REQUIREMENTS SCANNER ===")
    print(f"📁 Scanning project: {Path.cwd()}")
    print()
    
    # Find all Python files
    python_files = find_python_files('.')
    print(f"📄 Found {len(python_files)} Python files")
    
    # Extract all imports
    all_imports = set()
    for py_file in python_files:
        imports = extract_imports_from_file(py_file)
        if imports:
            print(f"   📄 {py_file.name}: {', '.join(sorted(imports))}")
            all_imports.update(imports)
    
    print(f"\n🔍 Total unique imports found: {len(all_imports)}")
    
    # Filter to third-party packages only
    third_party_packages = set()
    for package in all_imports:
        if is_third_party_package(package):
            pip_package = get_pip_package_name(package)
            third_party_packages.add(pip_package)
    
    print(f"📦 Third-party packages detected: {len(third_party_packages)}")
    for package in sorted(third_party_packages):
        print(f"   📦 {package}")
    
    # Check existing requirements.txt
    current_packages = read_current_requirements()
    print(f"\n📋 Current requirements.txt has: {len(current_packages)} packages")
    
    # Find missing packages
    missing_packages = set()
    for package in third_party_packages:
        if package.lower() not in current_packages:
            missing_packages.add(package)
    
    if missing_packages:
        print(f"\n✅ Adding {len(missing_packages)} missing packages to requirements.txt:")
        for package in sorted(missing_packages):
            print(f"   ➕ {package}")
        
        update_requirements_file(missing_packages)
        print(f"\n🎯 Successfully updated requirements.txt!")
    else:
        print(f"\n✅ No missing packages - requirements.txt is up to date!")
    
    print(f"\n📄 Final requirements.txt contents:")
    requirements_file = Path('requirements.txt')
    if requirements_file.exists():
        with open(requirements_file, 'r') as f:
            for i, line in enumerate(f, 1):
                print(f"   {i:2d}: {line.rstrip()}")
    
    print("\n🎉 Requirements scan completed!")

if __name__ == "__main__":
    import datetime
    main()
