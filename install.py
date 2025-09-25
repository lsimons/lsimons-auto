#!/usr/bin/env python3
"""
install.py - Installation script for lsimons-auto

This script:
1. Creates ~/.local/bin directory if it doesn't exist
2. Creates a symlink ~/.local/bin/start-the-day pointing to start_the_day.py
3. Creates a symlink ~/.local/bin/auto pointing to lsimons_auto.py
4. Creates ~/.local/log directory for LaunchAgent logs
5. Installs macOS LaunchAgent plist for daily 7am execution
"""

import os
import sys
from pathlib import Path


def install_symlinks() -> None:
    """Install the start-the-day and lsimons_auto symlinks."""
    # Get the absolute path to scripts in the lsimons_auto directory
    script_dir = Path(__file__).parent.absolute()
    start_the_day_path = script_dir / "lsimons_auto" / "start_the_day.py"
    lsimons_auto_path = script_dir / "lsimons_auto" / "lsimons_auto.py"

    if not start_the_day_path.exists():
        print(f"Error: {start_the_day_path} not found")
        sys.exit(1)

    if not lsimons_auto_path.exists():
        print(f"Error: {lsimons_auto_path} not found")
        sys.exit(1)

    # Create ~/.local/bin directory if it doesn't exist
    local_bin_dir = Path.home() / ".local" / "bin"
    if not local_bin_dir.exists():
        print(f"Creating directory: {local_bin_dir}")
        local_bin_dir.mkdir(parents=True, exist_ok=True)
    else:
        print(f"Directory already exists: {local_bin_dir}")

    # Install start-the-day symlink
    install_single_symlink(start_the_day_path, local_bin_dir / "start-the-day")

    # Install auto symlink
    install_single_symlink(lsimons_auto_path, local_bin_dir / "auto")


def install_single_symlink(source_path: Path, symlink_path: Path) -> None:
    """Install a single symlink, handling existing files gracefully."""
    if symlink_path.exists():
        if symlink_path.is_symlink():
            existing_target = symlink_path.readlink()
            if existing_target == source_path:
                print(
                    f"Symlink already exists and points to correct target: {symlink_path}"
                )
                return
            else:
                print(
                    f"Symlink exists but points to different target: {existing_target}"
                )
                print("Removing existing symlink and creating new one...")
                symlink_path.unlink()
        else:
            print(f"Error: {symlink_path} exists but is not a symlink")
            sys.exit(1)

    print(f"Creating symlink: {symlink_path} -> {source_path}")
    symlink_path.symlink_to(source_path)


def install_launch_agent() -> None:
    """Install macOS LaunchAgent for daily execution."""
    # Create ~/.local/log directory for LaunchAgent logs
    local_log_dir = Path.home() / ".local" / "log"
    if not local_log_dir.exists():
        print(f"Creating directory: {local_log_dir}")
        local_log_dir.mkdir(parents=True, exist_ok=True)
    else:
        print(f"Directory already exists: {local_log_dir}")

    # Get current user's username for plist template
    username = os.environ.get("USER", "unknown")

    # Get the absolute path to the plist template
    script_dir = Path(__file__).parent.absolute()
    plist_template_path = script_dir / "etc" / "com.leosimons.start-the-day.plist"

    if not plist_template_path.exists():
        print(f"Error: {plist_template_path} not found")
        sys.exit(1)

    # Read plist template and replace username
    plist_content = plist_template_path.read_text()
    plist_content = plist_content.replace("/Users/lsimons/", f"/Users/{username}/")

    # Install to ~/Library/LaunchAgents/
    launch_agents_dir = Path.home() / "Library" / "LaunchAgents"
    if not launch_agents_dir.exists():
        print(f"Creating directory: {launch_agents_dir}")
        launch_agents_dir.mkdir(parents=True, exist_ok=True)

    plist_dest_path = launch_agents_dir / "com.leosimons.start-the-day.plist"

    # Write the customized plist
    print(f"Installing LaunchAgent: {plist_dest_path}")
    plist_dest_path.write_text(plist_content)

    # Load the LaunchAgent
    print("Loading LaunchAgent...")
    result = os.system(f"launchctl load {plist_dest_path}")
    if result == 0:
        print("LaunchAgent loaded successfully!")
        print("The script will now run daily at 7:00 AM")
    else:
        print("Warning: Failed to load LaunchAgent. You may need to load it manually:")
        print(f"  launchctl load {plist_dest_path}")


def main() -> None:
    """Main installation function."""
    print("Installing lsimons-auto...")

    install_symlinks()
    install_launch_agent()

    print("\nInstallation completed successfully!")
    print(
        "- You can now run 'start-the-day' from anywhere (if ~/.local/bin is in your PATH)"
    )
    print("- You can now run 'auto' from anywhere (if ~/.local/bin is in your PATH)")
    print(
        "- The start-the-day script will automatically run daily at 7:00 AM via LaunchAgent"
    )
    print("- Logs will be written to ~/.local/log/start-the-day.log")
    print("- Use 'auto --help' to see available actions")


if __name__ == "__main__":
    main()
