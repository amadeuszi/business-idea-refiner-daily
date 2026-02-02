#!/usr/bin/env python3
"""Verify that the project setup is complete and working."""

import sys
from pathlib import Path


def check_mark(condition: bool) -> str:
    """Return a checkmark or X based on condition."""
    return "✓" if condition else "✗"


def main():
    """Run setup verification checks."""
    print("🔍 Verifying Project Setup\n")
    print("=" * 50)
    
    all_passed = True
    
    # Check Python version
    print("\n📌 Python Version")
    print(f"   {check_mark(sys.version_info >= (3, 12))} Python {sys.version.split()[0]}")
    if sys.version_info < (3, 12):
        print("   ⚠️  Python 3.12+ recommended")
        all_passed = False
    
    # Check virtual environment
    print("\n📌 Virtual Environment")
    in_venv = hasattr(sys, 'real_prefix') or (
        hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix
    )
    print(f"   {check_mark(in_venv)} Virtual environment active")
    if not in_venv:
        print("   ⚠️  Activate with: source .venv/bin/activate")
        all_passed = False
    
    # Check required packages
    print("\n📌 Required Packages")
    packages = {
        'openai': 'OpenAI API client',
        'jupyter': 'Jupyter notebook',
        'dotenv': 'Environment variables',
        'pytest': 'Testing framework',
        'black': 'Code formatter',
        'ruff': 'Linter',
    }
    
    for package, description in packages.items():
        try:
            __import__(package)
            print(f"   {check_mark(True)} {package:20} - {description}")
        except ImportError:
            print(f"   {check_mark(False)} {package:20} - {description}")
            all_passed = False
    
    # Check project structure
    print("\n📌 Project Structure")
    required_paths = [
        'src/agents/__init__.py',
        'src/agents/example.py',
        'notebooks/00_getting_started.ipynb',
        'tests/test_example.py',
        'pyproject.toml',
        'README.md',
    ]
    
    for path in required_paths:
        exists = Path(path).exists()
        print(f"   {check_mark(exists)} {path}")
        if not exists:
            all_passed = False
    
    # Check environment file
    print("\n📌 Environment Configuration")
    env_exists = Path('.env').exists()
    env_example_exists = Path('.env.example').exists()
    print(f"   {check_mark(env_example_exists)} .env.example (template)")
    print(f"   {check_mark(env_exists)} .env (your configuration)")
    
    if not env_exists:
        print("   💡 Create .env file with: cp .env.example .env")
        print("   💡 Then add your OpenAI API key to .env")
    
    # Try importing the agents package
    print("\n📌 Package Import")
    try:
        import agents
        print(f"   {check_mark(True)} agents package can be imported")
        print(f"   📦 Version: {agents.__version__}")
    except ImportError as e:
        print(f"   {check_mark(False)} agents package import failed")
        print(f"   ⚠️  Error: {e}")
        all_passed = False
    
    # Summary
    print("\n" + "=" * 50)
    if all_passed:
        print("✅ All checks passed! Your setup is complete.")
        print("\n🚀 Next steps:")
        print("   1. Add your OpenAI API key to .env")
        print("   2. Run: jupyter lab")
        print("   3. Open notebooks/00_getting_started.ipynb")
    else:
        print("⚠️  Some checks failed. Please review the issues above.")
        print("\n📖 See SETUP.md for detailed setup instructions.")
        sys.exit(1)


if __name__ == "__main__":
    main()
