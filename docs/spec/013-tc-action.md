# 013 - Technology Council Meeting Action

**Purpose:** Manage Technology Council meeting preparation, including directory creation, template copying, and PDF generation

**Requirements:**
- Subcommand `tc prep-meeting`: Prepare for next Monday's meeting by creating directory, copying template, opening current and previous meeting docs in Word
- Subcommand `tc gen-pdf`: Convert .docx files to PDF for all meeting directories missing PDFs in current year
- Subcommand `tc create-dirs`: Create directories for all Mondays of next year
- Configurable base directory (default: `~/Schuberg Philis/Engineering - Documents/Meetings/Technology Council`)
- Support `--dry-run` for all subcommands

**Design Approach:**
- Implement as single action with subcommands using argparse subparsers
- Use Monday-based date calculation (next Monday, or today if Monday)
- Directory structure: `{base_dir}/{YYYY}/{YYYYMMDD}/`
- Template file: `{base_dir}/YYYYMMDD Minutes Technology Council.docx`
- Meeting doc naming: `{YYYYMMDD} Minutes Technology Council.docx`
- Use AppleScript via osascript for Word automation (open docs, PDF conversion)

**Implementation Notes:**
- Migration from standalone `tc` command in `~/.local/bin/tc`
- No external dependencies (standard library only)
- PDF generation updates Word fields before saving
- Previous meeting search goes back through current year until finding existing doc
- Base directory configurable via `--base-dir` argument or environment variable `TC_BASE_DIR`

**Status:** Draft
