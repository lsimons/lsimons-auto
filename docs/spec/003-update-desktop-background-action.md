# 003 - Update Desktop Background Action

## Overview
This specification defines a new action that generates and sets a custom desktop background image featuring the "lsimons-auto" text with current UTC date/time in a geeky monospace font, optimized for high-resolution macOS displays.

## Status
- [x] Draft
- [x] Under Review
- [x] Approved
- [x] In Progress
- [x] Implemented
- [ ] Deprecated

## Motivation
Having a dynamic desktop background that displays the current date/time provides:
- Quick visual reference to current UTC time without additional clock widgets
- Personal branding with "lsimons-auto" text
- Automated way to refresh desktop appearance
- Demonstration of image generation capabilities in the automation framework

## Requirements

### Functional Requirements
1. **Image Generation**: Create a desktop background image with specified text content
2. **Text Content**: Display "lsimons-auto" prominently with current UTC date/time below
3. **Font Selection**: Use a monospace font with "geeky" aesthetic (e.g., Source Code Pro, JetBrains Mono, or similar)
4. **High Resolution**: Generate images suitable for high-DPI macOS displays (at least 2880x1800 for MacBook Pro)
5. **Desktop Setting**: Automatically set the generated image as the desktop background
6. **File Management**: Clean up old background images to prevent disk space accumulation

### Non-Functional Requirements
1. **Performance**: Image generation should complete within 2-3 seconds
2. **Reliability**: Handle missing fonts gracefully with fallback options
3. **Cross-Resolution**: Support multiple common macOS resolutions
4. **File Size**: Generated images should be reasonably sized (< 2MB)
5. **Aesthetics**: Professional appearance suitable for work environments

## Design

### Action Script Structure
Following the established action pattern from spec 002:

```python
#!/usr/bin/env python3
"""
update_desktop_background.py - Generate and set custom desktop background

Creates a desktop background with "lsimons-auto" branding and current UTC time
using a monospace font optimized for high-resolution macOS displays.
"""

import argparse
import sys
from typing import Optional

def main(args: Optional[list[str]] = None) -> None:
    """Generate and set desktop background image."""
    # Implementation details below
```

### Image Specifications
- **Resolution**: Default 2880x1800 (MacBook Pro 15"), with support for 1920x1080, 2560x1600
- **Format**: PNG for lossless quality and transparency support
- **Color Scheme**: Dark background with light text for reduced eye strain
- **Layout**: Centered text with "lsimons-auto" larger than date/time

### Text Layout Design
```
                    lsimons-auto
                 2024-01-15 14:30:42 UTC
```

**Typography Hierarchy:**
- Main title: 72pt monospace font
- Date/time: 36pt monospace font  
- Colors: Light gray (#E8E8E8) on dark background (#1A1A1A)

### Font Selection Priority
1. **JetBrains Mono** - Modern, highly readable programming font
2. **Source Code Pro** - Adobe's open-source monospace font
3. **SF Mono** - Apple's system monospace font (macOS default)
4. **Monaco** - Classic macOS monospace fallback
5. **Courier New** - Universal fallback

### File Management
- **Storage Location**: `~/.local/share/lsimons-auto/backgrounds/`
- **Naming Convention**: `background_YYYYMMDD_HHMMSS.png`
- **Cleanup Policy**: Keep only the 5 most recent background files
- **Permissions**: User-readable only (600)

## Implementation

### Phase 1: Core Image Generation
1. Create `lsimons_auto/actions/update_desktop_background.py`
2. Implement image generation using Pillow (PIL)
3. Add font detection and fallback logic
4. Implement text rendering with proper positioning

### Phase 2: Desktop Integration
1. Add macOS desktop background setting via `osascript`
2. Implement file cleanup mechanism
3. Add error handling for permission issues

### Phase 3: Additional Options
1. Add dry-run mode for testing
2. Add command-line options for custom resolutions

### Key Implementation Details

#### Font Detection
```python
def find_available_font() -> str:
    """Find the best available monospace font on the system."""
    preferred_fonts = [
        "/System/Library/Fonts/JetBrainsMono-Regular.ttf",
        "/System/Library/Fonts/SourceCodePro-Regular.ttf", 
        "/System/Library/Fonts/SFMono-Regular.ttf",
        "/System/Library/Fonts/Monaco.ttf",
        "/System/Library/Fonts/CourierNewPSMT.ttf"
    ]
    
    for font_path in preferred_fonts:
        if Path(font_path).exists():
            return font_path
    
    # System fallback
    return "Monaco"
```

#### Image Generation
```python
def generate_background(width: int = 2880, height: int = 1800) -> Path:
    """Generate desktop background image with current timestamp."""
    from PIL import Image, ImageDraw, ImageFont
    from datetime import datetime
    
    # Create image with dark background
    img = Image.new('RGB', (width, height), color='#1A1A1A')
    draw = ImageDraw.Draw(img)
    
    # Load fonts
    title_font = ImageFont.truetype(find_available_font(), 72)
    time_font = ImageFont.truetype(find_available_font(), 36)
    
    # Generate timestamp
    now_utc = datetime.utcnow()
    timestamp = now_utc.strftime('%Y-%m-%d %H:%M:%S UTC')
    
    # Calculate text positioning
    title_text = "lsimons-auto"
    title_bbox = draw.textbbox((0, 0), title_text, font=title_font)
    time_bbox = draw.textbbox((0, 0), timestamp, font=time_font)
    
    # Center text on image
    title_x = (width - title_bbox[2]) // 2
    title_y = height // 2 - 50
    
    time_x = (width - time_bbox[2]) // 2  
    time_y = title_y + 100
    
    # Draw text
    draw.text((title_x, title_y), title_text, font=title_font, fill='#E8E8E8')
    draw.text((time_x, time_y), timestamp, font=time_font, fill='#E8E8E8')
    
    # Save image
    bg_dir = Path.home() / ".local" / "share" / "lsimons-auto" / "backgrounds"
    bg_dir.mkdir(parents=True, exist_ok=True)
    
    filename = f"background_{now_utc.strftime('%Y%m%d_%H%M%S')}.png"
    filepath = bg_dir / filename
    
    img.save(filepath, 'PNG')
    filepath.chmod(0o600)
    
    return filepath
```

#### Desktop Background Setting
```python
def set_desktop_background(image_path: Path) -> None:
    """Set the desktop background using macOS APIs."""
    import subprocess
    
    script = f'''
    tell application "System Events"
        tell every desktop
            set picture to "{image_path}"
        end tell
    end tell
    '''
    
    try:
        subprocess.run(['osascript', '-e', script], check=True)
        print(f"Desktop background updated: {image_path}")
    except subprocess.CalledProcessError as e:
        print(f"Failed to set desktop background: {e}")
        sys.exit(1)
```

#### File Cleanup
```python
def cleanup_old_backgrounds(keep_count: int = 5) -> None:
    """Remove old background files, keeping only the most recent."""
    bg_dir = Path.home() / ".local" / "share" / "lsimons-auto" / "backgrounds"
    
    if not bg_dir.exists():
        return
    
    background_files = sorted(
        bg_dir.glob("background_*.png"),
        key=lambda x: x.stat().st_mtime,
        reverse=True
    )
    
    for old_file in background_files[keep_count:]:
        old_file.unlink()
        print(f"Cleaned up old background: {old_file.name}")
```

### Command Line Interface
```python
def main(args: Optional[list[str]] = None) -> None:
    """Main function to generate and set desktop background."""
    parser = argparse.ArgumentParser(
        description="Generate and set desktop background with current UTC time"
    )
    
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Generate image but don't set as background"
    )
    
    parsed_args = parser.parse_args(args)
    
    try:
        # Generate new background (hardcoded to 2880x1800)
        image_path = generate_background(2880, 1800)
        print(f"Generated background: {image_path}")
        
        # Set as desktop background (unless dry-run)
        if not parsed_args.dry_run:
            set_desktop_background(image_path)
        
        # Cleanup old files (keep 5 most recent)
        cleanup_old_backgrounds(5)
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
```

## Dependencies

### Required Python Packages
- **Pillow (PIL)**: Image generation and manipulation
  - Add to `pyproject.toml`: `pillow>=10.0.0`
- **Standard Library**: `datetime`, `subprocess`, `pathlib`, `argparse`

### System Requirements  
- **macOS**: Required for desktop background setting via AppleScript
- **Font Files**: System fonts or user-installed monospace fonts
- **Disk Space**: ~10MB for background image storage (with cleanup)

## Testing

### Unit Tests
```python
def test_font_detection():
    """Test that font detection finds a valid monospace font."""
    font_path = find_available_font()
    assert font_path is not None
    # Test that font_path points to accessible file or is valid system font name

def test_image_generation():
    """Test image generation creates valid PNG file."""
    with tempfile.TemporaryDirectory() as temp_dir:
        image_path = generate_background(1920, 1080)
        assert image_path.exists()
        assert image_path.suffix == '.png'
        
        # Verify image can be opened
        from PIL import Image
        with Image.open(image_path) as img:
            assert img.size == (1920, 1080)
            assert img.mode == 'RGB'

def test_cleanup_functionality():
    """Test that old background cleanup works correctly."""
    # Create test background files
    # Run cleanup with keep_count=2
    # Verify correct files are kept/removed
```

### Integration Tests
```python
def test_full_workflow():
    """Test complete background generation and setting workflow."""
    # Test dry-run mode doesn't set background
    # Test actual background setting (if on macOS)
    # Verify cleanup runs without errors

def test_command_line_interface():
    """Test CLI argument parsing and execution."""
    # Test --dry-run flag
    # Test help output
```

### Manual Testing Checklist
- [ ] Verify image appears correctly on different screen resolutions
- [ ] Confirm text is readable on various desktop setups
- [ ] Test font fallback when preferred fonts unavailable
- [ ] Verify desktop background actually changes
- [ ] Confirm file cleanup works as expected
- [ ] Test error handling when permissions denied

## Security Considerations

### File Permissions
- Background images stored with user-only permissions (600)
- Directory creation respects user umask settings
- No elevation of privileges required

### AppleScript Execution
- Uses standard macOS APIs through `osascript`
- No arbitrary code execution risks
- Limited to desktop background modification only

## Future Enhancements

### Potential Features
1. **Custom Text**: Allow user-specified text instead of "lsimons-auto"
2. **Color Themes**: Support multiple color schemes (dark, light, colorful)
3. **Time Zones**: Display multiple time zones simultaneously
4. **Configuration File**: Support YAML config for customization options

## References
- [Pillow Documentation](https://pillow.readthedocs.io/) - Image processing library
- [macOS Desktop Picture APIs](https://developer.apple.com/documentation/appkit/nsworkspace) - Background setting
- [AppleScript Desktop Commands](https://developer.apple.com/library/archive/documentation/AppleScript/Conceptual/AppleScriptLangGuide/) - System automation
- Typography best practices for programming fonts
- macOS HIG for desktop wallpaper design considerations