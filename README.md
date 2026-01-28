# JARS CLI

The official command-line interface for the JARS copy trading application.

## Installation

The recommended way to install JARS is via pipx:

```bash
pipx install jars-cli
```

Or via standard pip:

```bash
pip install jars-cli
```

## Quick Start

Once installed, just type:

```bash
jars
```

This will launch the interactive REPL.

## Commands

- `auth login`: Authenticate with your JARS account
- `wallet summary`: View your balance
- `traders list`: Find master traders to copy
- `subs follow <id>`: Start copy trading instantly

## Development

```bash
git clone https://github.com/astrovine/jars.git
cd jars
poetry install
poetry run jars
```
