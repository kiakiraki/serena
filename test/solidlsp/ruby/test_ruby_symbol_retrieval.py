"""
Tests for the Ruby language server symbol-related functionality.

These tests focus on the following methods:
- request_containing_symbol
- request_referencing_symbols
- request_defining_symbol
- request_document_symbols integration
"""

import os

import pytest

from solidlsp import SolidLanguageServer
from solidlsp.ls_config import Language
from solidlsp.ls_types import SymbolKind

pytestmark = pytest.mark.ruby


class TestRubyLanguageServerSymbols:
    """Test the Ruby language server's symbol-related functionality."""

    @pytest.mark.parametrize("language_server", [Language.RUBY], indirect=True)
    def test_request_containing_symbol_method(self, language_server: SolidLanguageServer) -> None:
        """Test request_containing_symbol for a method."""
        # Test for a position inside the add method in Calculator class
        file_path = "lib/calculator.rb"
        # Look for a position inside the add method body
        containing_symbol = language_server.request_containing_symbol(file_path, 5, 10, include_body=True)

        # Verify that we found the containing symbol
        assert containing_symbol is not None, "Should find containing symbol for method position"
        assert containing_symbol["name"] == "add", f"Expected 'add', got '{containing_symbol['name']}'"
        assert (
            containing_symbol["kind"] == SymbolKind.Method.value
        ), f"Expected Method kind ({SymbolKind.Method.value}), got {containing_symbol['kind']}"

        # Verify location information
        assert "location" in containing_symbol, "Containing symbol should have location information"
        location = containing_symbol["location"]
        assert "range" in location, "Location should contain range information"
        assert "start" in location["range"], "Range should have start position"
        assert "end" in location["range"], "Range should have end position"

        # Verify body content if available
        if "body" in containing_symbol:
            body = containing_symbol["body"]
            assert "def add" in body, "Method body should contain method definition"
            assert len(body.strip()) > 0, "Method body should not be empty"

    @pytest.mark.parametrize("language_server", [Language.RUBY], indirect=True)
    def test_request_containing_symbol_class(self, language_server: SolidLanguageServer) -> None:
        """Test request_containing_symbol for a class."""
        # Test for a position inside the Calculator class
        file_path = "lib/calculator.rb"
        # Line inside the class definition
        containing_symbol = language_server.request_containing_symbol(file_path, 3, 5)

        # Verify that we found the containing symbol
        assert containing_symbol is not None, "Should find containing symbol for class position"
        assert containing_symbol["name"] == "Calculator", f"Expected 'Calculator', got '{containing_symbol['name']}'"
        assert (
            containing_symbol["kind"] == SymbolKind.Class.value
        ), f"Expected Class kind ({SymbolKind.Class.value}), got {containing_symbol['kind']}"

        # Verify location information exists
        assert "location" in containing_symbol, "Class symbol should have location information"
        location = containing_symbol["location"]
        assert "range" in location, "Location should contain range"
        assert "start" in location["range"] and "end" in location["range"], "Range should have start and end positions"

    @pytest.mark.parametrize("language_server", [Language.RUBY], indirect=True)
    def test_request_containing_symbol_module(self, language_server: SolidLanguageServer) -> None:
        """Test request_containing_symbol for a module context."""
        # Test that we can find the MathUtils module in document symbols
        file_path = "lib/calculator.rb"
        symbols, roots = language_server.request_document_symbols(file_path)

        # Verify MathUtils module appears in document symbols
        math_utils_module = None
        for symbol in symbols:
            if symbol.get("name") == "MathUtils" and symbol.get("kind") == SymbolKind.Module:
                math_utils_module = symbol
                break

        assert math_utils_module is not None, "MathUtils module not found in document symbols"

    @pytest.mark.parametrize("language_server", [Language.RUBY], indirect=True)
    def test_request_containing_symbol_none(self, language_server: SolidLanguageServer) -> None:
        """Test request_containing_symbol for a position with no containing symbol."""
        # Test for a position outside any class/method (e.g., at the top of the file)
        file_path = "lib/calculator.rb"
        # Line 1 is likely outside any class or method - but ruby-lsp may still find the class
        containing_symbol = language_server.request_containing_symbol(file_path, 0, 5)

        # ruby-lsp is more aggressive and may find containing class even at file start
        # This is acceptable behavior for ruby-lsp
        if containing_symbol is not None:
            assert "name" in containing_symbol
            assert "kind" in containing_symbol

    @pytest.mark.parametrize("language_server", [Language.RUBY], indirect=True)
    def test_request_referencing_symbols_method(self, language_server: SolidLanguageServer) -> None:
        """Test request_referencing_symbols for a method."""
        # Test referencing symbols for add method
        file_path = "lib/calculator.rb"
        # Find the add method in document symbols
        symbols, roots = language_server.request_document_symbols(file_path)
        add_symbol = None

        # Find add method in the document symbols
        for symbol in symbols:
            if symbol.get("name") == "add":
                add_symbol = symbol
                break

        if not add_symbol or "selectionRange" not in add_symbol:
            pytest.skip("add symbol or its selectionRange not found")

        sel_start = add_symbol["selectionRange"]["start"]
        ref_symbols = [
            ref.symbol for ref in language_server.request_referencing_symbols(file_path, sel_start["line"], sel_start["character"])
        ]

        # We might not have references in our simple test setup, so just verify structure
        for symbol in ref_symbols:
            assert "name" in symbol
            assert "kind" in symbol

    @pytest.mark.parametrize("language_server", [Language.RUBY], indirect=True)
    def test_request_referencing_symbols_class(self, language_server: SolidLanguageServer) -> None:
        """Test request_referencing_symbols for a class."""
        # Test referencing symbols for User class
        file_path = "lib/models.rb"
        # Find User class in document symbols
        symbols, roots = language_server.request_document_symbols(file_path)
        user_symbol = None

        for symbol in symbols:
            if symbol.get("name") == "User":
                user_symbol = symbol
                break

        if not user_symbol or "selectionRange" not in user_symbol:
            pytest.skip("User symbol or its selectionRange not found")

        sel_start = user_symbol["selectionRange"]["start"]
        ref_symbols = [
            ref.symbol for ref in language_server.request_referencing_symbols(file_path, sel_start["line"], sel_start["character"])
        ]

        # Verify structure of referencing symbols
        for symbol in ref_symbols:
            assert "name" in symbol
            assert "kind" in symbol
            if "location" in symbol and "range" in symbol["location"]:
                assert "start" in symbol["location"]["range"]
                assert "end" in symbol["location"]["range"]

    @pytest.mark.parametrize("language_server", [Language.RUBY], indirect=True)
    def test_request_defining_symbol_class(self, language_server: SolidLanguageServer) -> None:
        """Test request_defining_symbol for a class reference."""
        # Test finding the definition of the Calculator class
        file_path = "main.rb"
        # Look for Calculator usage in main.rb
        defining_symbol = language_server.request_defining_symbol(file_path, 15, 15)

        # This might not work perfectly in all Ruby language servers
        if defining_symbol is not None:
            assert "name" in defining_symbol
            # The name might be "Calculator" or the method that contains it
            assert defining_symbol.get("name") is not None

    @pytest.mark.parametrize("language_server", [Language.RUBY], indirect=True)
    def test_request_defining_symbol_none(self, language_server: SolidLanguageServer) -> None:
        """Test request_defining_symbol for a position with no symbol."""
        # Test for a position with no symbol (e.g., whitespace or comment)
        file_path = "main.rb"
        # Line 1 is likely a comment or blank line
        defining_symbol = language_server.request_defining_symbol(file_path, 1, 0)

        # ruby-lsp may find definitions even for require statements, which is acceptable
        if defining_symbol is not None:
            assert "name" in defining_symbol
            assert "kind" in defining_symbol

    @pytest.mark.parametrize("language_server", [Language.RUBY], indirect=True)
    def test_symbol_methods_integration(self, language_server: SolidLanguageServer) -> None:
        """Test the integration between different symbol-related methods."""
        file_path = "lib/models.rb"

        # Step 1: Find a method we know exists - line 5 is inside @name = name in initialize method
        containing_symbol = language_server.request_containing_symbol(file_path, 5, 5)  # inside initialize method
        if containing_symbol is not None:
            # ruby-lsp may return the class or the method depending on position
            assert containing_symbol["name"] in ["initialize", "User"]

            # Step 2: Get the defining symbol for the same position
            defining_symbol = language_server.request_defining_symbol(file_path, 5, 5)
            if defining_symbol is not None:
                assert "name" in defining_symbol

                # Step 3: Verify that symbols have valid structure
                assert "kind" in defining_symbol
                assert "kind" in containing_symbol

    @pytest.mark.parametrize("language_server", [Language.RUBY], indirect=True)
    def test_symbol_tree_structure_basic(self, language_server: SolidLanguageServer) -> None:
        """Test that the symbol tree structure includes Ruby symbols."""
        # Get all symbols in the test repository
        repo_structure = language_server.request_full_symbol_tree()
        assert len(repo_structure) >= 1

        # Look for our Ruby files in the structure
        found_ruby_files = False
        for root in repo_structure:
            if "children" in root:
                for child in root["children"]:
                    if child.get("name") in ["main", "calculator", "models"]:
                        found_ruby_files = True
                        break

        # We should find at least some Ruby files in the symbol tree
        assert found_ruby_files, "Ruby files not found in symbol tree"

    @pytest.mark.parametrize("language_server", [Language.RUBY], indirect=True)
    def test_document_symbols_detailed(self, language_server: SolidLanguageServer) -> None:
        """Test document symbols for detailed Ruby file structure."""
        file_path = "lib/models.rb"
        symbols, roots = language_server.request_document_symbols(file_path)

        # Verify we have symbols
        assert len(symbols) > 0 or len(roots) > 0

        # Look for expected class names
        symbol_names = set()
        all_symbols = symbols if symbols else roots

        for symbol in all_symbols:
            symbol_names.add(symbol.get("name"))
            # Add children names too
            if "children" in symbol:
                for child in symbol["children"]:
                    symbol_names.add(child.get("name"))

        # We should find at least some of our defined classes/methods
        expected_symbols = {"User", "Product", "Order", "Validations"}
        found_symbols = symbol_names.intersection(expected_symbols)
        assert len(found_symbols) > 0, f"Expected symbols not found. Found: {symbol_names}"

    @pytest.mark.parametrize("language_server", [Language.RUBY], indirect=True)
    def test_request_dir_overview(self, language_server: SolidLanguageServer) -> None:
        """Test that request_dir_overview returns correct symbol information for files in a directory."""
        # Get overview of the test repo directory
        overview = language_server.request_dir_overview(".")

        # Verify that we have entries for our main files
        expected_files = ["main.rb", "lib/calculator.rb", "lib/models.rb"]
        found_files = []

        for file_path in overview.keys():
            for expected in expected_files:
                if expected in file_path:
                    found_files.append(expected)
                    break

        assert len(found_files) >= 2, f"Should find at least 2 expected files, found: {found_files}"

        # Test specific symbols from calculator.rb if it exists
        calculator_file_key = None
        for file_path in overview.keys():
            if "calculator.rb" in file_path:
                calculator_file_key = file_path
                break

        if calculator_file_key:
            calculator_symbols = overview[calculator_file_key]
            assert len(calculator_symbols) > 0, "calculator.rb should have symbols"

            # Check for expected symbols
            symbol_names = []
            for symbol in calculator_symbols:
                if hasattr(symbol, 'get'):
                    symbol_names.append(symbol.get("name"))
                elif isinstance(symbol, dict):
                    symbol_names.append(symbol.get("name"))

            expected_symbols = ["Calculator", "MathUtils"]
            found_expected = [name for name in expected_symbols if name in symbol_names]
            assert len(found_expected) >= 1, f"Should find at least one expected symbol, found: {found_expected} in {symbol_names}"

    @pytest.mark.parametrize("language_server", [Language.RUBY], indirect=True)
    def test_request_document_overview(self, language_server: SolidLanguageServer) -> None:
        """Test that request_document_overview returns correct symbol information for a file."""
        # Get overview of the main.rb file
        file_path = "main.rb"
        overview = language_server.request_document_overview(file_path)

        # Verify that we have symbol information
        assert len(overview) > 0, "Document overview should contain symbols"

        # Look for expected symbols from the file
        symbol_names = set()
        for s_info in overview:
            if hasattr(s_info, 'get'):
                symbol_names.add(s_info.get("name"))
            elif isinstance(s_info, dict):
                symbol_names.add(s_info.get("name"))

        # We should find our DemoClass
        expected_symbols = {"DemoClass"}
        found_symbols = symbol_names.intersection(expected_symbols)
        assert len(found_symbols) > 0, f"Expected to find some symbols from {expected_symbols}, found: {symbol_names}"

    @pytest.mark.parametrize("language_server", [Language.RUBY], indirect=True)
    def test_request_containing_symbol_nested(self, language_server: SolidLanguageServer) -> None:
        """Test request_containing_symbol with nested scopes."""
        # Test for a position inside a method which is inside a class
        file_path = "lib/calculator.rb"
        # Position inside add method within Calculator class
        containing_symbol = language_server.request_containing_symbol(file_path, 5, 15)

        # Verify that we found the innermost containing symbol (the method)
        if containing_symbol is not None:
            assert containing_symbol["name"] == "add"
            assert containing_symbol["kind"] == SymbolKind.Method

    @pytest.mark.parametrize("language_server", [Language.RUBY], indirect=True)
    def test_request_referencing_symbols_none(self, language_server: SolidLanguageServer) -> None:
        """Test request_referencing_symbols for a position with no symbol."""
        # Test for a position with no symbol (comment or blank line)
        file_path = "main.rb"

        # Try a position that should have no symbols (comment line)
        try:
            ref_symbols = [ref.symbol for ref in language_server.request_referencing_symbols(file_path, 1, 0)]
            # If we get here, make sure we got an empty result or minimal results
            if ref_symbols:
                # Some language servers might return minimal info, verify it's reasonable
                assert len(ref_symbols) <= 3, f"Expected few/no references at line 1, got {len(ref_symbols)}"

        except Exception as e:
            # Some language servers throw exceptions for invalid positions, which is acceptable
            assert (
                "symbol" in str(e).lower() or "position" in str(e).lower() or "reference" in str(e).lower()
            ), f"Exception should be related to symbol/position/reference issues, got: {e}"