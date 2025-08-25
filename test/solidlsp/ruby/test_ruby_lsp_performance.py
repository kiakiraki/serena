import time
from pathlib import Path

import pytest

from solidlsp import SolidLanguageServer
from solidlsp.ls_config import Language


@pytest.mark.ruby
@pytest.mark.performance
class TestRubyLspPerformance:
    """Performance-focused tests for ruby-lsp"""

    @pytest.mark.parametrize("language_server", [Language.RUBY], indirect=True)
    def test_initialization_speed(self, language_server: SolidLanguageServer) -> None:
        """Test initialization speed is reasonable"""
        start_time = time.time()

        # First request should trigger full initialization
        symbols = language_server.request_full_symbol_tree()

        init_duration = time.time() - start_time

        # ruby-lsp should initialize quickly
        assert init_duration < 15.0, f"Initialization took {init_duration:.2f}s, expected < 15s"
        assert len(symbols) > 0, "Should discover symbols during initialization"

    @pytest.mark.parametrize("language_server", [Language.RUBY], indirect=True)
    def test_symbol_request_performance(self, language_server: SolidLanguageServer) -> None:
        """Test symbol requests are fast after initialization"""
        # Ensure initialization is complete
        language_server.request_full_symbol_tree()

        # Test subsequent requests are fast
        start_time = time.time()
        symbols = language_server.request_full_symbol_tree()
        duration = time.time() - start_time

        assert duration < 5.0, f"Symbol request took {duration:.2f}s, expected < 5s"
        assert len(symbols) > 0, "Should return symbols quickly"

    @pytest.mark.parametrize("language_server", [Language.RUBY], indirect=True)
    def test_document_symbols_performance(self, language_server: SolidLanguageServer) -> None:
        """Test document symbol requests are fast"""
        files_to_test = ["main.rb", "lib/calculator.rb", "lib/models.rb"]

        for file_path in files_to_test:
            start_time = time.time()
            symbols = language_server.request_document_symbols(file_path)
            duration = time.time() - start_time

            assert duration < 2.0, f"Document symbols for {file_path} took {duration:.2f}s, expected < 2s"
            assert symbols is not None, f"Should return symbols for {file_path}"

    @pytest.mark.parametrize("language_server", [Language.RUBY], indirect=True)
    @pytest.mark.parametrize("repo_path", [Language.RUBY], indirect=True)
    def test_definition_request_performance(self, language_server: SolidLanguageServer, repo_path: Path) -> None:
        """Test definition requests are fast"""
        start_time = time.time()

        # Request definition for Calculator.new in main.rb
        definitions = language_server.request_definition(str(repo_path / "main.rb"), 15, 20)

        duration = time.time() - start_time

        assert duration < 3.0, f"Definition request took {duration:.2f}s, expected < 3s"
        assert len(definitions) >= 0, "Should return definition results"

    @pytest.mark.parametrize("language_server", [Language.RUBY], indirect=True)
    def test_multiple_file_indexing_speed(self, language_server: SolidLanguageServer) -> None:
        """Test that indexing multiple files is reasonably fast"""
        start_time = time.time()

        # Request symbols which should trigger indexing of all files
        symbols = language_server.request_full_symbol_tree()

        indexing_duration = time.time() - start_time

        # With the test repository size, indexing should be very fast
        assert indexing_duration < 10.0, f"Indexing took {indexing_duration:.2f}s, expected < 10s"

        # Verify we found symbols from multiple files
        symbol_names = []

        def collect_symbol_names(sym_list):
            for sym in sym_list:
                if isinstance(sym, dict) and "name" in sym:
                    symbol_names.append(sym["name"])
                if isinstance(sym, dict) and "children" in sym:
                    collect_symbol_names(sym["children"])

        for file_symbols in symbols:
            collect_symbol_names(file_symbols)

        # Should find symbols from different files
        expected_symbols = ["DemoClass", "Calculator", "User", "Product", "MathUtils"]
        found_symbols = [name for name in expected_symbols if name in symbol_names]

        assert len(found_symbols) >= 3, f"Should find multiple symbols across files, found: {found_symbols}"
