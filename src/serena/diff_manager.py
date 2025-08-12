import difflib
from typing import Optional

from pydantic import BaseModel


class DiffPreview(BaseModel):
    """Model for diff preview data"""

    file_path: str
    symbol_name: Optional[str]
    unified_diff: str
    lines_added: int
    lines_removed: int


class DiffManager:
    """Utility class for generating diff previews"""

    def __init__(self):
        self._latest_preview: Optional[DiffPreview] = None

    def set_latest(self, preview: DiffPreview) -> None:
        """Set the latest diff preview"""
        self._latest_preview = preview

    def get_latest(self) -> Optional[DiffPreview]:
        """Get the latest diff preview"""
        return self._latest_preview

    def clear_latest(self) -> None:
        """Clear the latest diff preview"""
        self._latest_preview = None

    @staticmethod
    def generate_diff_preview(
        old_content: str,
        new_content: str,
        file_path: str,
        symbol_name: Optional[str] = None,
    ) -> DiffPreview:
        """Generate a diff preview between old and new content"""
        # Generate unified diff
        unified_diff = "\n".join(
            difflib.unified_diff(
                old_content.splitlines(keepends=True),
                new_content.splitlines(keepends=True),
                fromfile=f"a/{file_path}",
                tofile=f"b/{file_path}",
                lineterm="",
            )
        )

        # Count changes (exclude header lines and hunk headers)
        diff_lines = unified_diff.split("\n")
        lines_added = len([line for line in diff_lines if line.startswith("+") and not line.startswith("+++")])
        lines_removed = len([line for line in diff_lines if line.startswith("-") and not line.startswith("---")])

        return DiffPreview(
            file_path=file_path,
            symbol_name=symbol_name,
            unified_diff=unified_diff,
            lines_added=lines_added,
            lines_removed=lines_removed,
        )
