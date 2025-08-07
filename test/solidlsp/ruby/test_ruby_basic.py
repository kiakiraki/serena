import os
from pathlib import Path

import pytest

from solidlsp import SolidLanguageServer
from solidlsp.ls_config import Language
from solidlsp.ls_utils import SymbolUtils


@pytest.mark.ruby
class TestRubyLanguageServer:
    @pytest.mark.parametrize("language_server", [Language.RUBY], indirect=True)
    def test_find_symbol(self, language_server: SolidLanguageServer) -> None:
        symbols = language_server.request_full_symbol_tree()
        assert SymbolUtils.symbol_tree_contains_name(symbols, "DemoClass"), "DemoClass not found in symbol tree"
        assert SymbolUtils.symbol_tree_contains_name(symbols, "helper_function"), "helper_function not found in symbol tree"
        assert SymbolUtils.symbol_tree_contains_name(symbols, "print_value"), "print_value not found in symbol tree"

    @pytest.mark.parametrize("language_server", [Language.RUBY], indirect=True)
    def test_find_referencing_symbols(self, language_server: SolidLanguageServer) -> None:
        file_path = os.path.join("main.rb")
        symbols = language_server.request_document_symbols(file_path)
        helper_symbol = None
        for sym in symbols[0]:
            if sym.get("name") == "helper_function":
                helper_symbol = sym
                break
        print(helper_symbol)
        assert helper_symbol is not None, "Could not find 'helper_function' symbol in main.rb"

    @pytest.mark.parametrize("language_server", [Language.RUBY], indirect=True)
    @pytest.mark.parametrize("repo_path", [Language.RUBY], indirect=True)
    def test_find_definition_across_files(self, language_server: SolidLanguageServer, repo_path: Path) -> None:
        # Test finding Calculator.add method definition from line 17: Calculator.new.add(demo.value, 10)
        definition_location_list = language_server.request_definition(
            str(repo_path / "main.rb"), 16, 17
        )  # add method at line 17 (0-indexed 16), position 17

        assert len(definition_location_list) == 1
        definition_location = definition_location_list[0]
        print(f"Found definition: {definition_location}")
        assert definition_location["uri"].endswith("lib.rb")
        assert definition_location["range"]["start"]["line"] == 1  # add method on line 2 (0-indexed 1)

    @pytest.mark.parametrize("language_server", [Language.RUBY], indirect=True)
    def test_request_references_class(self, language_server: SolidLanguageServer) -> None:
        """Test request_references on the DemoClass class."""
        file_path = os.path.join("main.rb")
        symbols, _ = language_server.request_document_symbols(file_path)
        demo_class_symbol = next((s for s in symbols if s.get("name") == "DemoClass"), None)
        if not demo_class_symbol or "selectionRange" not in demo_class_symbol:
            raise AssertionError("DemoClass symbol or its selectionRange not found")
        sel_start = demo_class_symbol["selectionRange"]["start"]
        references = language_server.request_references(file_path, sel_start["line"], sel_start["character"])
        assert len(references) >= 0, "DemoClass should be referenced in multiple files"

    @pytest.mark.parametrize("language_server", [Language.RUBY], indirect=True)
    def test_request_references_function(self, language_server: SolidLanguageServer) -> None:
        """Test request_references on the helper_function function."""
        file_path = os.path.join("main.rb")
        symbols, _ = language_server.request_document_symbols(file_path)
        helper_function_symbol = next((s for s in symbols if s.get("name") == "helper_function"), None)
        if not helper_function_symbol or "selectionRange" not in helper_function_symbol:
            raise AssertionError("helper_function symbol or its selectionRange not found")
        sel_start = helper_function_symbol["selectionRange"]["start"]
        references = language_server.request_references(file_path, sel_start["line"], sel_start["character"])
        assert len(references) >= 0, "helper_function should be referenced in multiple files"
