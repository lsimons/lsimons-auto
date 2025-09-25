# 004 - Organize Desktop Action

**Purpose:** Automatically organize desktop files into date-based directories with intelligent file processing and compression

**Requirements:**
- Move desktop files to `~/Desktop/{YYYY-MM-DD}/` directories based on creation date
- Compress CleanShot images (`.png` with CleanShot prefix) using ImageIO
- Convert `.txt` files to `.md` with proper metadata headers
- Support dry-run mode for testing organization logic
- Preserve file timestamps and handle duplicates gracefully
- Skip system files, directories, and special items (Trash, etc.)

**Design Approach:**
- Follow action script architecture from DESIGN.md (template in 000-shared-patterns.md)
- Create date directories with timestamps matching oldest contained file
- Use `os.stat().st_birthtime` for creation date detection on macOS
- Process files individually with specific handlers for different file types
- Fall back to modification time if creation time unavailable
- Apply 85% JPEG compression to CleanShot images for space savings

**Implementation Notes:**
- Dependencies: Standard library only (os, pathlib, datetime, shutil)
- File processing: PNG compression (~70% size reduction), TXT→MD conversion
- Directory timestamps: Set to match earliest file creation time in directory
- Error handling: Skip problematic files with warnings, continue processing
- Duplicate handling: Append incrementing numbers to filenames as needed
- Exclusions: Skip `.DS_Store`, Trash, system directories, hidden files

**Status:** Implemented