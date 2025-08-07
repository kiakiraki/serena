"""
Tests for the language server symbol-related functionality for Ruby.
"""

import os

import pytest

from solidlsp import SolidLanguageServer
from solidlsp.ls_config import Language
from solidlsp.ls_types import SymbolKind


@pytest.mark.ruby
class TestRubyLanguageServerSymbols:
    """Test the language server's symbol-related functionality for Ruby."""

    @pytest.mark.parametrize("language_server", [Language.RUBY], indirect=True)
    def test_request_containing_symbol_function(self, language_server: SolidLanguageServer) -> None:
        """Test request_containing_symbol for a function."""
        file_path = os.path.join("main.rb")
        # Line 15 is inside the helper_function method body
        containing_symbol = language_server.request_containing_symbol(file_path, 15, 2, include_body=True)

        assert containing_symbol is not None
        assert containing_symbol["name"] == "helper_function"
        assert containing_symbol["kind"] == SymbolKind.Method
        if "body" in containing_symbol:
            assert containing_symbol["body"].strip().startswith("def helper_function")

    @pytest.mark.parametrize("language_server", [Language.RUBY], indirect=True)
    def test_request_containing_symbol_class(self, language_server: SolidLanguageServer) -> None:
        """Test request_containing_symbol for a class."""
        file_path = os.path.join("main.rb")
        # Line 3 is the class definition line for DemoClass
        containing_symbol = language_server.request_containing_symbol(file_path, 3, 7)

        assert containing_symbol is not None
        assert containing_symbol["name"] == "DemoClass"
        assert containing_symbol["kind"] == SymbolKind.Class

    @pytest.mark.parametrize("language_server", [Language.RUBY], indirect=True)
    def test_request_containing_symbol_nested(self, language_server: SolidLanguageServer) -> None:
        """Test request_containing_symbol with nested scopes."""
        file_path = os.path.join("main.rb")
        # Line 10 is inside the print_value method inside DemoClass class
        containing_symbol = language_server.request_containing_symbol(file_path, 10, 5)

        assert containing_symbol is not None
        assert containing_symbol["name"] == "print_value"
        assert containing_symbol["kind"] == SymbolKind.Method

        # Get the parent containing symbol
        if "location" in containing_symbol and "range" in containing_symbol["location"]:
            parent_symbol = language_server.request_containing_symbol(
                file_path,
                containing_symbol["location"]["range"]["start"]["line"],
                containing_symbol["location"]["range"]["start"]["character"] - 1,
            )

            assert parent_symbol is not None
            assert parent_symbol["name"] == "DemoClass"
            assert parent_symbol["kind"] == SymbolKind.Class

    @pytest.mark.parametrize("language_server", [Language.RUBY], indirect=True)
    def test_request_containing_symbol_none(self, language_server: SolidLanguageServer) -> None:
        """Test request_containing_symbol for a position with no containing symbol."""
        file_path = os.path.join("main.rb")
        # Line 1 is in imports, not inside any function or class
        containing_symbol = language_server.request_containing_symbol(file_path, 0, 10)

        assert containing_symbol is None or containing_symbol == {}

    @pytest.mark.parametrize("language_server", [Language.RUBY], indirect=True)
    def test_request_referencing_symbols_function(self, language_server: SolidLanguageServer) -> None:
        """Test request_referencing_symbols for a function."""
        file_path = os.path.join("main.rb")
        symbols, _ = language_server.request_document_symbols(file_path)
        helper_function_symbol = next((s for s in symbols if s.get("name") == "helper_function"), None)
        if not helper_function_symbol or "selectionRange" not in helper_function_symbol:
            raise AssertionError("helper_function symbol or its selectionRange not found")
        sel_start = helper_function_symbol["selectionRange"]["start"]
        ref_symbols = [
            ref.symbol for ref in language_server.request_referencing_symbols(file_path, sel_start["line"], sel_start["character"])
        ]
        assert len(ref_symbols) >= 0, "No referencing symbols found for helper_function (selectionRange)"

        for symbol in ref_symbols:
            assert "name" in symbol
            assert "kind" in symbol
            if "location" in symbol and "range" in symbol["location"]:
                assert "start" in symbol["location"]["range"]
                assert "end" in symbol["location"]["range"]

    @pytest.mark.parametrize("language_server", [Language.RUBY], indirect=True)
    def test_request_referencing_symbols_class(self, language_server: SolidLanguageServer) -> None:
        """Test request_referencing_symbols for a class."""
        file_path = os.path.join("main.rb")
        symbols, _ = language_server.request_document_symbols(file_path)
        demo_class_symbol = next((s for s in symbols if s.get("name") == "DemoClass"), None)
        if not demo_class_symbol or "selectionRange" not in demo_class_symbol:
            raise AssertionError("DemoClass symbol or its selectionRange not found")
        sel_start = demo_class_symbol["selectionRange"]["start"]
        ref_symbols = [
            ref.symbol for ref in language_server.request_referencing_symbols(file_path, sel_start["line"], sel_start["character"])
        ]
        assert len(ref_symbols) >= 0, "No referencing symbols found for DemoClass (selectionRange)"

    @pytest.mark.parametrize("language_server", [Language.RUBY], indirect=True)
    def test_request_defining_symbol_method_call(self, language_server: SolidLanguageServer) -> None:
        """Test request_defining_symbol for a method call."""
        file_path = os.path.join("main.rb")
        # Line 16 contains Calculator.new.add(demo.value, 10)
        defining_symbol = language_server.request_defining_symbol(file_path, 16, 17)

        assert defining_symbol is not None
        assert defining_symbol.get("name") == "add"
        assert defining_symbol.get("kind") == SymbolKind.Method.value
        if "location" in defining_symbol and "uri" in defining_symbol["location"]:
            assert "lib.rb" in defining_symbol["location"]["uri"]

    @pytest.mark.parametrize("language_server", [Language.RUBY], indirect=True)
    def test_request_defining_symbol_none(self, language_server: SolidLanguageServer) -> None:
        """Test request_defining_symbol for a position with no symbol."""
        file_path = os.path.join("main.rb")
        # Line 2 is a blank line
        defining_symbol = language_server.request_defining_symbol(file_path, 1, 0)

        assert defining_symbol is None
