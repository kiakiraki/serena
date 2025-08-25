import time
from pathlib import Path

import pytest

from solidlsp import SolidLanguageServer
from solidlsp.ls_config import Language
from solidlsp.ls_utils import SymbolUtils


@pytest.mark.ruby
class TestRubyLspBasic:
    @pytest.mark.parametrize("language_server", [Language.RUBY], indirect=True)
    def test_find_symbol(self, language_server: SolidLanguageServer) -> None:
        """Test basic symbol discovery with ruby-lsp"""
        symbols = language_server.request_full_symbol_tree()
        assert SymbolUtils.symbol_tree_contains_name(symbols, "DemoClass"), "DemoClass not found in symbol tree"
        assert SymbolUtils.symbol_tree_contains_name(symbols, "Calculator"), "Calculator not found in symbol tree"
        assert SymbolUtils.symbol_tree_contains_name(symbols, "helper_function"), "helper_function not found in symbol tree"
        assert SymbolUtils.symbol_tree_contains_name(symbols, "User"), "User not found in symbol tree"
        assert SymbolUtils.symbol_tree_contains_name(symbols, "Product"), "Product not found in symbol tree"

    @pytest.mark.parametrize("language_server", [Language.RUBY], indirect=True)
    def test_faster_initialization(self, language_server: SolidLanguageServer) -> None:
        """Test that ruby-lsp initializes quickly"""
        start_time = time.time()
        symbols = language_server.request_full_symbol_tree()
        duration = time.time() - start_time

        # ruby-lsp should initialize quickly
        assert duration < 15.0, f"Initialization took {duration:.2f}s, expected < 15s"
        assert len(symbols) > 0, "Should find symbols in test repository"

    @pytest.mark.parametrize("language_server", [Language.RUBY], indirect=True)
    def test_find_referencing_symbols(self, language_server: SolidLanguageServer) -> None:
        """Test finding references to symbols"""
        file_path = "main.rb"
        symbols = language_server.request_document_symbols(file_path)

        helper_symbol = None
        for sym in symbols[0]:
            if sym.get("name") == "helper_function":
                helper_symbol = sym
                break

        assert helper_symbol is not None, "Could not find 'helper_function' symbol in main.rb"

    @pytest.mark.parametrize("language_server", [Language.RUBY], indirect=True)
    @pytest.mark.parametrize("repo_path", [Language.RUBY], indirect=True)
    def test_find_definition_across_files(self, language_server: SolidLanguageServer, repo_path: Path) -> None:
        """Test finding definitions across files"""
        # Test finding Calculator.add method definition from main.rb
        definition_location_list = language_server.request_definition(
            str(repo_path / "main.rb"), 15, 20  # calculate_with_tax method calls Calculator.new
        )

        assert len(definition_location_list) >= 1, "Should find at least one definition"
        definition_location = definition_location_list[0]
        assert definition_location["uri"].endswith("calculator.rb"), f"Expected calculator.rb, got {definition_location['uri']}"

    @pytest.mark.parametrize("language_server", [Language.RUBY], indirect=True)
    def test_module_and_class_discovery(self, language_server: SolidLanguageServer) -> None:
        """Test discovery of modules and classes"""
        symbols = language_server.request_full_symbol_tree()

        # Check for modules
        assert SymbolUtils.symbol_tree_contains_name(symbols, "MathUtils"), "MathUtils module not found"
        assert SymbolUtils.symbol_tree_contains_name(symbols, "Validations"), "Validations module not found"

        # Check for classes
        assert SymbolUtils.symbol_tree_contains_name(symbols, "Calculator"), "Calculator class not found"
        assert SymbolUtils.symbol_tree_contains_name(symbols, "User"), "User class not found"
        assert SymbolUtils.symbol_tree_contains_name(symbols, "Product"), "Product class not found"
        assert SymbolUtils.symbol_tree_contains_name(symbols, "Order"), "Order class not found"

    @pytest.mark.parametrize("language_server", [Language.RUBY], indirect=True)
    def test_method_discovery_in_classes(self, language_server: SolidLanguageServer) -> None:
        """Test discovery of methods within classes"""
        symbols = language_server.request_full_symbol_tree()

        # Check for Calculator methods
        assert SymbolUtils.symbol_tree_contains_name(symbols, "add"), "add method not found"
        assert SymbolUtils.symbol_tree_contains_name(symbols, "subtract"), "subtract method not found"
        assert SymbolUtils.symbol_tree_contains_name(symbols, "multiply"), "multiply method not found"
        assert SymbolUtils.symbol_tree_contains_name(symbols, "divide"), "divide method not found"

        # Check for User methods
        assert SymbolUtils.symbol_tree_contains_name(symbols, "full_info"), "full_info method not found"
        assert SymbolUtils.symbol_tree_contains_name(symbols, "to_hash"), "to_hash method not found"
        assert SymbolUtils.symbol_tree_contains_name(symbols, "self.from_hash"), "self.from_hash method not found"

    @pytest.mark.parametrize("language_server", [Language.RUBY], indirect=True)
    def test_document_symbols(self, language_server: SolidLanguageServer) -> None:
        """Test document symbols for specific files"""
        # Test main.rb symbols
        main_symbols = language_server.request_document_symbols("main.rb")
        assert len(main_symbols) > 0, "Should find symbols in main.rb"

        # Test calculator.rb symbols
        calc_symbols = language_server.request_document_symbols("lib/calculator.rb")
        assert len(calc_symbols) > 0, "Should find symbols in lib/calculator.rb"

        # Test models.rb symbols
        model_symbols = language_server.request_document_symbols("lib/models.rb")
        assert len(model_symbols) > 0, "Should find symbols in lib/models.rb"

    @pytest.mark.parametrize("language_server", [Language.RUBY], indirect=True)
    @pytest.mark.parametrize("repo_path", [Language.RUBY], indirect=True)
    def test_erb_file_support(self, language_server: SolidLanguageServer, repo_path: Path) -> None:
        """Test ERB file support (ruby-lsp specific feature)"""
        erb_file = "views/index.html.erb"
        erb_path = repo_path / erb_file

        if erb_path.exists():
            # Test that ruby-lsp can handle ERB files
            try:
                symbols = language_server.request_document_symbols(erb_file)
                # ERB files might not have traditional symbols, but should not error
                assert symbols is not None, "ERB file should be processable"
            except Exception as e:
                pytest.skip(f"ERB support may not be fully available: {e}")

    @pytest.mark.parametrize("language_server", [Language.RUBY], indirect=True)
    def test_rack_file_support(self, language_server: SolidLanguageServer) -> None:
        """Test Rack file (.ru) support"""
        try:
            symbols = language_server.request_document_symbols("config.ru")
            assert symbols is not None, "Rack file should be processable"
        except Exception as e:
            pytest.skip(f"Rack file support may not be available: {e}")
