# LogFiles Directory

This directory is designated for temporary files, test scripts, log files, and other development artifacts.

## Purpose

- **Temporary test scripts**: Place test scripts, comparison tools, and verification scripts here
- **Log files**: Output logs from backtests, tests, and debugging sessions
- **Temporary data files**: CSV exports, temporary data dumps, etc.
- **Development artifacts**: Any other temporary files created during development

## Git Ignore

All files in this directory are ignored by git (see `.gitignore`). This keeps the repository clean while allowing developers to store temporary files locally.

## Usage

When creating temporary test scripts or generating log files, place them in this directory instead of the project root:

```
LogFiles/
  ├── test_comparison.py
  ├── backtest_output.log
  ├── temp_data.csv
  └── ...
```
