from sensai.util import logging

from serena.tools.tools_base import Tool

log = logging.getLogger(__name__)


class PreviewSymbolReplacementTool(Tool):
    """
    Preview a symbol replacement without actually applying the changes.
    Shows what the diff would look like if the replacement were applied.
    
    Requires an active project with Language Server support.
    """

    def apply(
        self,
        name_path: str,
        relative_path: str,
        new_body: str,
    ) -> str:
        """
        Preview what a symbol replacement would look like without applying the changes.

        :param name_path: for finding the symbol to preview replacement, same logic as in the `find_symbol` tool.
        :param relative_path: the relative path to the file containing the symbol
        :param new_body: the proposed new symbol body
        """
        try:
            # Get symbol information
            symbol_retriever = self.create_language_server_symbol_retriever()
            symbols = symbol_retriever.find_by_name(
                name_path, within_relative_path=relative_path, include_body=True
            )

            if not symbols:
                return f"Error: Symbol '{name_path}' not found in {relative_path}"

            symbol = symbols[0]
            old_content = symbol.body if symbol.body else ""

            # Generate preview diff
            diff_preview = self.agent.diff_manager.generate_diff_preview(
                old_content=old_content, new_content=new_body, file_path=relative_path, symbol_name=name_path
            )

            # Store as latest preview
            self.agent.diff_manager.set_latest(diff_preview)

            # Format the diff for display
            result = f"Preview of changes to '{name_path}' in {relative_path}:\n\n"
            result += f"Lines added: +{diff_preview.lines_added}\n"
            result += f"Lines removed: -{diff_preview.lines_removed}\n\n"
            result += "Unified diff:\n"
            result += diff_preview.unified_diff
            result += "\n\nThis is a preview only. Use replace_symbol_body to apply the changes."
            result += "\nPreview is now available in the web dashboard."

            return result

        except Exception as e:
            log.error(f"Error generating preview: {e}", exc_info=e)
            return f"Error generating preview: {str(e)}"


class PreviewFileDiffTool(Tool, ToolMarkerDoesNotRequireActiveProject):
    """
    Preview changes between arbitrary old and new content.
    Useful for showing what changes would be made before applying them.
    """

    def apply(
        self,
        old_content: str,
        new_content: str,
        file_path: str = "preview.txt",
        description: str = "Content changes",
    ) -> str:
        """
        Generate a preview diff between old and new content.

        :param old_content: the original content
        :param new_content: the proposed new content
        :param file_path: the file path to use in the diff header (for display purposes)
        :param description: a description of the changes being previewed
        """
        try:
            # Generate preview diff
            diff_preview = self.agent.diff_manager.generate_diff_preview(
                old_content=old_content,
                new_content=new_content,
                file_path=file_path,
                symbol_name=description,
            )

            # Store as latest preview
            self.agent.diff_manager.set_latest(diff_preview)

            # Format the diff for display
            result = f"Preview: {description}\n"
            result += f"File: {file_path}\n\n"
            result += f"Lines added: +{diff_preview.lines_added}\n"
            result += f"Lines removed: -{diff_preview.lines_removed}\n\n"
            result += "Unified diff:\n"
            result += diff_preview.unified_diff
            result += "\n\nThis is a preview only. No changes have been applied."
            result += "\nPreview is now available in the web dashboard."

            return result

        except Exception as e:
            log.error(f"Error generating preview: {e}", exc_info=e)
            return f"Error generating preview: {str(e)}"
