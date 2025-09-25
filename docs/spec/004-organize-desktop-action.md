# 004 - Organize Desktop Action

## Overview
This specification defines a new action that organizes files and directories on the desktop into a structured directory hierarchy based on creation dates, with special handling for image compression and file extension conversion.

## Status
- [x] Draft
- [x] Under Review
- [x] Approved
- [x] In Progress
- [x] Implemented
- [ ] Deprecated

## Motivation
Desktop organization provides:
- Automatic file management to prevent desktop clutter
- Chronological organization for easy retrieval of files
- Consistent directory structure across time periods
- Special handling for common file types (images, text files)
- Automated cleanup to maintain a clean workspace

## Requirements

### Functional Requirements
1. **Directory Structure**: Create year/month/day directory hierarchy in `~/Desktop`
2. **File Organization**: Move all desktop files into appropriate date-based directories
3. **Directory Organization**: Move all desktop directories into appropriate date-based directories  
4. **Date Detection**: Use file/directory creation time to determine target location
5. **Directory Timestamp Adjustment**: Set creation and modification dates of directories to match their purpose:
   - Year directories: Set to first day of the year (January 1st)
   - Month directories: Set to first day of the month
   - Day directories: Set to the actual date being organized
6. **Image Compression**: Compress CleanShot images larger than 1MB to approximately 1MB
7. **Text File Conversion**: Rename `.txt` files to `.md` extension during move
8. **Clean Desktop**: Ensure no files or directories remain directly on desktop after organization

### Non-Functional Requirements
1. **Performance**: Organization should complete within 30 seconds for typical desktop contents
2. **Safety**: Preserve all files and directories during organization
3. **Reliability**: Handle file system errors gracefully
4. **Logging**: Provide clear feedback on actions taken
5. **Idempotency**: Running multiple times should not cause issues

## Design

### Action Script Structure
Following the established action pattern from spec 002:

```python
#!/usr/bin/env python3
"""
organize_desktop.py - Organize desktop files into date-based directory structure

Moves all files and directories from ~/Desktop into a year/month/day hierarchy
based on creation time, with special handling for images and text files.
"""

import argparse
import sys
from typing import Optional

def main(args: Optional[list[str]] = None) -> None:
    """Organize desktop files into structured directories."""
    # Implementation details below
```

### Directory Structure
The target directory structure on the desktop:

```
~/Desktop/
├── 2024/
│   ├── 01/
│   │   ├── 15/
│   │   │   ├── document.md (was document.txt)
│   │   │   └── photo.jpg
│   │   └── 16/
│   │       └── presentation.pptx
│   ├── 02/
│   │   └── 28/
│   │       └── CleanShot_compressed.png (was >1MB)
│   └── 03/
│       └── 15/
│           └── example.md (was example.txt)
├── 2023/
│   └── 12/
│       └── 31/
│           └── old_file.pdf
```

### File Processing Rules

#### Standard Files and Directories
- Use creation time (`st_birthtime` on macOS, fallback to `st_ctime`)
- Move to `YYYY/MM/DD/` directory structure
- Preserve original filename unless special processing applies
- Create intermediate directories as needed

#### CleanShot Image Processing
- **Detection**: Files starting with "CleanShot" with image extensions (.png, .jpg, .jpeg, .gif, .bmp, .tiff)
- **Size Check**: Only compress if file size > 1MB
- **Compression**: Reduce to approximately 1MB while maintaining aspect ratio
- **Quality**: Use JPEG compression with progressive quality reduction until target size achieved

#### Text File Processing  
- **Detection**: Files with `.txt` extension
- **Conversion**: Change extension from `.txt` to `.md`
- **Content**: Preserve file content unchanged
- **Example**: `notes.txt` becomes `notes.md`

### Implementation Details

#### Directory Creation and Timestamp Setting
```python
def set_directory_timestamps(directory: Path, target_date: datetime) -> None:
    """Set creation and modification times for a directory."""
    timestamp = target_date.timestamp()
    # Set modification time
    os.utime(directory, (timestamp, timestamp))
    
    # On macOS, also try to set birth time if possible
    if hasattr(os, "stat_result") and hasattr(os.stat_result, "st_birthtime"):
        try:
            # Use touch command to set birth time on macOS
            import subprocess
            date_str = target_date.strftime("%Y%m%d%H%M.%S")
            subprocess.run(["touch", "-t", date_str, str(directory)], 
                          check=False, capture_output=True)
        except (subprocess.SubprocessError, FileNotFoundError):
            pass

def ensure_date_directory(base_path: Path, date_obj: datetime) -> Path:
    """Create year/month/day directory structure if it doesn't exist."""
    year_dir = base_path / str(date_obj.year)
    month_dir = year_dir / f"{date_obj.month:02d}"
    day_dir = month_dir / f"{date_obj.day:02d}"
    
    # Track which directories we create to set timestamps
    created_dirs = []
    
    if not year_dir.exists():
        year_dir.mkdir(exist_ok=True)
        created_dirs.append(("year", year_dir))
    
    if not month_dir.exists():
        month_dir.mkdir(exist_ok=True)
        created_dirs.append(("month", month_dir))
    
    if not day_dir.exists():
        day_dir.mkdir(exist_ok=True)
        created_dirs.append(("day", day_dir))
    
    # Set appropriate timestamps for newly created directories
    for dir_type, directory in created_dirs:
        if dir_type == "year":
            target_date = datetime(date_obj.year, 1, 1)
        elif dir_type == "month":
            target_date = datetime(date_obj.year, date_obj.month, 1)
        else:  # day
            target_date = date_obj
        
        set_directory_timestamps(directory, target_date)
    
    return day_dir
```

#### File Date Detection
```python
def get_creation_date(file_path: Path) -> datetime:
    """Get file creation date, with fallback handling."""
    import stat
    
    file_stat = file_path.stat()
    
    # macOS: use birth time if available
    if hasattr(file_stat, 'st_birthtime'):
        timestamp = file_stat.st_birthtime
    else:
        # Fallback to change time
        timestamp = file_stat.st_ctime
    
    return datetime.fromtimestamp(timestamp)
```

#### Image Compression
```python
def compress_cleanshot_image(image_path: Path, target_dir: Path) -> Path:
    """Compress CleanShot image to approximately 1MB."""
    from PIL import Image
    import io
    
    target_size = 1024 * 1024  # 1MB in bytes
    
    with Image.open(image_path) as img:
        # Convert to RGB if necessary (for JPEG compression)
        if img.mode in ('RGBA', 'LA'):
            background = Image.new('RGB', img.size, (255, 255, 255))
            background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
            img = background
        
        # Start with high quality and reduce until target size reached
        for quality in range(95, 10, -5):
            buffer = io.BytesIO()
            img.save(buffer, format='JPEG', quality=quality, optimize=True)
            
            if buffer.tell() <= target_size:
                break
        
        # Save compressed image
        output_path = target_dir / f"{image_path.stem}_compressed.jpg"
        with open(output_path, 'wb') as f:
            f.write(buffer.getvalue())
        
        return output_path
```

#### Text File Conversion
```python
def convert_txt_to_md(txt_path: Path, target_dir: Path) -> Path:
    """Convert .txt file to .md extension."""
    md_filename = txt_path.stem + '.md'
    output_path = target_dir / md_filename
    
    # Copy content with new extension
    import shutil
    shutil.copy2(txt_path, output_path)
    
    return output_path
```

#### Main Organization Logic
```python
def organize_desktop_items() -> None:
    """Organize all items on desktop into date-based directories."""
    desktop_path = Path.home() / 'Desktop'
    
    # Get all items directly on desktop (exclude existing year directories)
    items_to_organize = []
    
    for item in desktop_path.iterdir():
        # Skip hidden files and existing year directories
        if item.name.startswith('.'):
            continue
        if item.is_dir() and item.name.isdigit() and len(item.name) == 4:
            continue  # Skip existing year directories
            
        items_to_organize.append(item)
    
    print(f"Found {len(items_to_organize)} items to organize")
    
    for item in items_to_organize:
        try:
            organize_single_item(item, desktop_path)
        except Exception as e:
            print(f"Error organizing {item.name}: {e}")
            continue

def organize_single_item(item_path: Path, base_path: Path) -> None:
    """Organize a single file or directory."""
    creation_date = get_creation_date(item_path)
    target_dir = ensure_date_directory(base_path, creation_date)
    
    if item_path.is_file():
        organize_file(item_path, target_dir)
    else:
        organize_directory(item_path, target_dir)

def organize_file(file_path: Path, target_dir: Path) -> None:
    """Organize a single file with special processing."""
    filename = file_path.name
    
    # Check for CleanShot image compression
    if (filename.startswith('CleanShot') and 
        file_path.suffix.lower() in {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff'} and
        file_path.stat().st_size > 1024 * 1024):  # > 1MB
        
        new_path = compress_cleanshot_image(file_path, target_dir)
        print(f"Compressed and moved: {filename} -> {new_path.name}")
        file_path.unlink()  # Remove original
        
    # Check for text file conversion
    elif file_path.suffix.lower() == '.txt':
        new_path = convert_txt_to_md(file_path, target_dir)
        print(f"Converted and moved: {filename} -> {new_path.name}")
        file_path.unlink()  # Remove original
        
    # Standard file move
    else:
        new_path = target_dir / filename
        file_path.rename(new_path)
        print(f"Moved: {filename} -> {new_path.relative_to(Path.home() / 'Desktop')}")

def organize_directory(dir_path: Path, target_dir: Path) -> None:
    """Move directory to target location."""
    new_path = target_dir / dir_path.name
    dir_path.rename(new_path)
    print(f"Moved directory: {dir_path.name} -> {new_path.relative_to(Path.home() / 'Desktop')}")
```

### Command Line Interface
```python
def main(args: Optional[list[str]] = None) -> None:
    """Main function to organize desktop."""
    parser = argparse.ArgumentParser(
        description="Organize desktop files into date-based directory structure"
    )
    
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Show what would be organized without making changes"
    )
    
    parser.add_argument(
        "--verbose", "-v", action="store_true",
        help="Show detailed information about each file processed"
    )
    
    parsed_args = parser.parse_args(args)
    
    try:
        if parsed_args.dry_run:
            print("DRY RUN MODE - No files will be moved")
            preview_organization()
        else:
            organize_desktop_items()
            print("Desktop organization completed")
            
    except Exception as e:
        print(f"Error organizing desktop: {e}")
        sys.exit(1)
```

## Dependencies

### Required Python Packages
- **Pillow (PIL)**: Image compression and format conversion
  - Add to `pyproject.toml`: `pillow>=10.0.0`
- **Standard Library**: `pathlib`, `datetime`, `shutil`, `argparse`, `stat`

### System Requirements
- **macOS/Linux/Windows**: Cross-platform file system operations
- **Disk Space**: Sufficient space for compressed images and directory structure
- **Permissions**: Read/write access to `~/Desktop` directory

## Testing

### Unit Tests
```python
def test_date_detection():
    """Test creation date detection from files."""
    # Create test file with known creation time
    # Verify get_creation_date returns correct datetime

def test_directory_creation():
    """Test year/month/day directory structure creation."""
    # Test ensure_date_directory creates proper hierarchy
    # Verify existing directories are not recreated

def test_directory_timestamp_setting():
    """Test that directory timestamps are set correctly."""
    # Create directory structure for specific date
    # Verify year directory timestamp is set to January 1st
    # Verify month directory timestamp is set to first day of month
    # Verify day directory timestamp matches the actual date

def test_directory_timestamp_existing_dirs():
    """Test that existing directory timestamps are not modified."""
    # Create directories with custom timestamps
    # Call ensure_date_directory
    # Verify existing directories keep their original timestamps

def test_image_compression():
    """Test CleanShot image compression logic."""
    # Create test image > 1MB
    # Verify compression reduces size to ~1MB
    # Check that aspect ratio is preserved

def test_txt_to_md_conversion():
    """Test text file extension conversion."""
    # Create test .txt file
    # Verify conversion to .md preserves content
    # Check that original extension is changed

def test_file_organization():
    """Test individual file organization logic."""
    # Test standard file moves
    # Test special processing (images, text files)
    # Verify error handling for problematic files
```

### Integration Tests
```python
def test_full_desktop_organization():
    """Test complete desktop organization workflow."""
    # Create mock desktop with various file types
    # Run organization
    # Verify all files moved to correct date directories
    # Check special processing applied correctly

def test_dry_run_mode():
    """Test dry-run functionality."""
    # Verify dry-run shows preview without moving files
    # Confirm no actual file system changes occur

def test_error_handling():
    """Test error scenarios."""
    # Test permission denied situations
    # Test corrupted image files
    # Test very large files
```

### Manual Testing Checklist
- [ ] Verify organization works with real desktop files
- [ ] Confirm CleanShot images are properly compressed
- [ ] Test .txt to .md conversion preserves content
- [ ] Check directory moves work correctly
- [ ] Verify existing year directories are not disturbed
- [ ] Test dry-run mode provides accurate preview
- [ ] Verify directory timestamps are set correctly:
  - [ ] Year directories show January 1st as creation/modification date
  - [ ] Month directories show first day of month as creation/modification date
  - [ ] Day directories show the actual organization date
- [ ] Confirm existing directories maintain their original timestamps

## Security Considerations

### File System Safety
- Preserve all file content during moves and conversions
- Handle file system permissions appropriately
- Use atomic operations where possible to prevent corruption
- Validate file paths to prevent directory traversal

### Data Protection
- Maintain original file timestamps where appropriate
- Ensure compressed images maintain reasonable quality
- Backup original files during compression (temporary)
- Handle symbolic links safely

## Error Handling

### Common Error Scenarios
1. **Permission Denied**: Log error and continue with other files
2. **Disk Full**: Stop processing and report error clearly
3. **Corrupted Images**: Skip compression and move file normally
4. **Invalid Dates**: Use current date as fallback
5. **Filename Conflicts**: Add numeric suffix to avoid overwrites

### Recovery Strategies
- Log all operations for potential rollback
- Preserve original files during conversion until success confirmed
- Provide detailed error messages with suggested solutions

## References
- [Python pathlib documentation](https://docs.python.org/3/library/pathlib.html) - File system operations
- [Pillow documentation](https://pillow.readthedocs.io/) - Image processing
- [macOS file system attributes](https://developer.apple.com/library/archive/documentation/System/Conceptual/ManPages_iPhoneOS/man2/stat.2.html) - Creation time detection
- Desktop organization best practices
- File naming conventions for chronological organization