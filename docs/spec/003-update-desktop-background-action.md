# 003 - Update Desktop Background Action

**Purpose:** Generate dynamic desktop backgrounds with "lsimons-auto" branding and current UTC timestamp

**Requirements:**
- Generate 2880x1800 PNG with monospace font (JetBrains Mono preferred)
- Display "lsimons-auto" title with current UTC time below
- Set as macOS desktop background via AppleScript
- Clean up old backgrounds (keep 5 most recent)
- Support --dry-run mode for testing

**Design Approach:**
- Follow action script architecture from DESIGN.md (template in 000-shared-patterns.md)
- Use Pillow for image generation with dark theme (#1A1A1A bg, #E8E8E8 text)
- Font fallback: JetBrains Mono → Source Code Pro → SF Mono → Monaco → Courier New
- Store in `~/.local/share/lsimons-auto/backgrounds/`
- Execute via `osascript` to set desktop background on all displays

**Implementation Notes:**
- Dependency: Pillow >=10.0.0
- macOS-only (AppleScript desktop setting)
- 72pt title, 36pt timestamp, centered layout
- File naming: `background_YYYYMMDD_HHMMSS.png`
- File permissions: 600 (user-readable only)
- Cleanup policy: Remove files beyond 5 most recent by modification time

**Status:** Implemented