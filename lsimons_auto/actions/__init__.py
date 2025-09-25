"""
lsimons_auto.actions - Action scripts submodule

This submodule contains individual Python scripts that can be executed
both standalone and as subcommands through the lsimons_auto dispatcher.

Each action script follows a standard pattern:
- Has a main() function that performs the core work
- Can be run standalone with `python -m lsimons_auto.actions.{action_name}`
- Can be imported as a module
- Accepts optional args parameter for argument injection
"""
