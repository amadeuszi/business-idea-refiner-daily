# Amadeusz Agents

A Python project for experimenting with notebooks, AI agents, and OpenAI integration.

## Setup

This project uses [uv](https://github.com/astral-sh/uv) for fast Python package management.

### Prerequisites

- Python 3.12
- uv package manager

### Installation

1. Install uv (if not already installed):
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

2. Create a virtual environment and install dependencies:
```bash
uv venv
source .venv/bin/activate  # On Linux/Mac
uv pip install -e .
```

3. For development dependencies:
```bash
uv pip install -e ".[dev]"
```

### Project Structure

```
amadeusz_agents/
├── src/                  # Python source code
│   └── agents/          # Main package
├── notebooks/           # Jupyter notebooks
├── data/               # Data files (gitignored)
├── tests/              # Unit tests
├── pyproject.toml      # Project configuration
└── README.md           # This file
```

## Usage

### Running Notebooks

1. Activate the virtual environment
2. Launch Jupyter:
```bash
jupyter notebook
```
or
```bash
jupyter lab
```

### Environment Variables

Create a `.env` file in the project root for sensitive data like API keys:
```
OPENAI_API_KEY=your_api_key_here
```

## Development

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
