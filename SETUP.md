# Setup Guide

This guide will help you get started with the Amadeusz Agents project.

## ✅ Project Structure

Your project has been set up with the following structure:

```
amadeusz_agents/
├── .env.example          # Example environment variables
├── .gitignore           # Git ignore patterns
├── .python-version      # Python version specification (3.12)
├── pyproject.toml       # Project configuration and dependencies
├── README.md            # Main project documentation
├── SETUP.md            # This file
│
├── src/
│   └── agents/         # Main Python package
│       ├── __init__.py
│       └── example.py  # Example module with OpenAI integration
│
├── notebooks/          # Jupyter notebooks
│   ├── README.md
│   └── 00_getting_started.ipynb  # Getting started notebook
│
└── tests/              # Unit tests
    ├── __init__.py
    └── test_example.py
```

## 🚀 Quick Start

### 1. Activate the Virtual Environment

```bash
source .venv/bin/activate
```

You should see `(.venv)` in your terminal prompt.

### 2. Configure Environment Variables

Copy the example environment file and add your OpenAI API key:

```bash
cp .env.example .env
```

Then edit `.env` and add your actual OpenAI API key:

```
OPENAI_API_KEY=sk-your-actual-api-key-here
```

### 3. Verify Installation

Check that all packages are installed:

```bash
uv pip list
```

Test the Python package:

```bash
python -c "from agents import example; print('✓ Package imported successfully')"
```

### 4. Start Jupyter

Launch Jupyter to work with notebooks:

```bash
# Option 1: Classic Jupyter Notebook
jupyter notebook

# Option 2: JupyterLab (recommended)
jupyter lab
```

This will open in your browser. Navigate to the `notebooks/` folder and open `00_getting_started.ipynb`.

## 📦 Dependencies Installed

- **openai** - OpenAI API client
- **jupyter** - Jupyter notebook environment
- **ipykernel** - Python kernel for Jupyter
- **python-dotenv** - Environment variable management
- **pytest** - Testing framework (dev)
- **black** - Code formatter (dev)
- **ruff** - Fast Python linter (dev)

## 🔧 Common Commands

### Running Tests
```bash
pytest
```

### Code Formatting
```bash
black .
```

### Linting
```bash
ruff check .
```

### Adding New Dependencies

To add a new package:

```bash
# Add to dependencies
uv pip install package-name

# Update pyproject.toml manually to make it permanent
# Or use:
echo 'package-name>=version' >> requirements.txt  # if you prefer requirements.txt
```

### Running Python Scripts

```bash
python src/agents/example.py
```

### Starting an Interactive Python Session

```bash
python
>>> from agents.example import simple_completion
>>> result = simple_completion("Hello!")
>>> print(result)
```

## 📝 Next Steps

1. Open and run `notebooks/00_getting_started.ipynb`
2. Create your own notebooks in the `notebooks/` directory
3. Add your Python modules in `src/agents/`
4. Write tests in `tests/`
5. Explore the OpenAI API: https://platform.openai.com/docs

## 🆘 Troubleshooting

### Virtual Environment Not Activated
If commands aren't working, make sure the virtual environment is activated:
```bash
source .venv/bin/activate
```

### Missing API Key
If you get API key errors, make sure you've:
1. Created a `.env` file (not just `.env.example`)
2. Added your actual OpenAI API key to `.env`
3. The key starts with `sk-`

### Import Errors
If you can't import the `agents` package:
```bash
uv pip install -e .
```

### Jupyter Kernel Not Found
```bash
python -m ipykernel install --user --name=amadeusz-agents
```

## 📚 Resources

- [uv Documentation](https://github.com/astral-sh/uv)
- [OpenAI API Reference](https://platform.openai.com/docs/api-reference)
- [Jupyter Documentation](https://jupyter.org/documentation)
- [pytest Documentation](https://docs.pytest.org/)
