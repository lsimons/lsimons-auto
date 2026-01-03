# 010 - Google Drive Sync Action

**Purpose:** Synchronize Google Drive to a local volume using `rclone`, but only on specific hardware and when the target volume is available.

**Requirements:**
- Action name: `gdrive-sync`
- Execute `rclone sync gdrive: "/Volumes/LSData/Google Drive"`
- Run ONLY if hostname is "paddo"
- Run ONLY if `/Volumes/LSData` is mounted (directory exists)
- Launchd agent `com.leosimons.gdrive-sync` that triggers the action automatically when `/Volumes/LSData` is mounted
- Installation script must install this new launchd agent

**Design Approach:**
- **Action Script**: Standard Python action `lsimons_auto/actions/gdrive_sync.py`.
    - Use `socket.gethostname()` to check for "paddo".
    - Use `os.path.ismount()` or `os.path.exists()` to check for volume availability.
    - Use `subprocess.run()` to execute `rclone`.
- **Launchd Agent**:
    - Use `StartOnMount` key (if available/reliable) or `WatchPaths` looking for the volume.
    - Actually, for mounting events, `StartOnMount` is deprecated/not standard. A better approach for detecting volume mounts in launchd is `StartOnMount` (which *is* supported but might be tricky) or watching `/Volumes`. However, the prompt specifically asks to be "triggered to run ... when /Volumes/LSData is mounted".
    - The standard way to watch for a mount is often `StartOnMount` set to true in the plist.
    - Alternatively, watching `/Volumes/LSData` with `WatchPaths`. If the path exists/appears, it triggers.
    - We will use `WatchPaths` pointing to `/Volumes/LSData`. When it mounts, the path changes (or appears).
- **Installation**:
    - Update `install.py` to generate and install `com.leosimons.gdrive-sync.plist`.
    - Ensure the plist points to the `auto gdrive-sync` command (wrapper script).

**Implementation Notes:**
- Needs `rclone` installed (assumed pre-requisite, check `shutil.which("rclone")`).
- `WatchPaths` on `/Volumes/LSData` might trigger multiple times or on unmount. The script's idempotency and checks (is mounted?) handle this. if it runs on unmount, the "is mounted" check will fail and it will exit gracefully.
- Hostname check should be case-insensitive just in case.

**Status:** Draft
