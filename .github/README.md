

# Active-Apparel-Group / data-orchestration — .github Overview

This `.github` folder defines universal project conventions, Copilot/agent instructions, scoped language rules, and reusable prompts to support all development and operations in this repository.

## Structure

```markdown
github/
├── README.md # This file — index of Copilot/agent config
├── copilot-instructions.md # Global Copilot and style instructions
├── instructions/
│ ├── python.instructions.md # Python-specific coding instructions
│ ├── sql.instructions.md # SQL Server / T-SQL coding instructions
│ └── yaml.instructions.md # YAML and Kestra flow instructions
├── prompts/
│ ├── dev-task.prompt.md # Reusable prompt for development tasks
│ └── ops-checklist.prompt.md # Reusable prompt for ops & deployment tasks
```


## Purpose

- Standardize Copilot, AI agents, and human developer contributions
- Ensure consistent practices for Python, SQL Server, YAML/Kestra flows
- Provide reusable prompt templates for common tasks
- Keep project quality and maintainability high

## Notes

- Copilot and agents will reference `.github/copilot-instructions.md` globally.
- File-type rules in `.github/instructions/*.instructions.md` apply by extension.
- Prompts in `.github/prompts/*.prompt.md` can be selected in Copilot Chat or AI agents.
