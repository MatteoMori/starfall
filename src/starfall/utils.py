from pathlib import Path
import re

def slugify(text: str) -> str:
    """Sanitize text for filenames: replace non-alphanumerics with hyphens."""
    return re.sub(r'[^A-Za-z0-9]+', '-', text.strip()).strip('-').lower()

def assign_task_output_file_name(crew, subfolder: str, scope: str, task_name: str, tool_name: str, tool_version: str):
    """
    Find a task by name in the crew and assign a dynamic output_file name.

    Args:
        crew: The Crew object containing tasks.
        subfolder (str): The subfolder where the output file will be saved.
        scope (str): The scope to include in the filename.
        task_name (str): The name of the task to update.
        tool_name (str): The tool's name (used in filename).
        tool_version (str): The tool's version (used in filename).

    Returns:
        None

    Raises:
        RuntimeError: If no task with the given name is found.
    """
    task = next((t for t in crew.tasks if t.name == task_name), None)
    if not task:
        raise RuntimeError(f"Task named '{task_name}' not found in crew.tasks")

    Path("outputs").mkdir(exist_ok=True)
    filename = f"outputs/{subfolder}/{slugify(tool_name)}-{tool_version}-{scope}-report.md"
    task.output_file = filename
    return
