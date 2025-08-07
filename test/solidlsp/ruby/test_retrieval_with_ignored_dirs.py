from collections.abc import Generator

import pytest

from solidlsp import SolidLanguageServer
from solidlsp.ls_config import Language
from test.conftest import create_ls

# This mark will be applied to all tests in this module
pytestmark = pytest.mark.ruby


@pytest.fixture(scope="module")
def ls_with_ignored_dirs() -> Generator[SolidLanguageServer, None, None]:
    """Fixture to set up an LS for the ruby test repo with the 'vendor' directory ignored."""
    ignored_paths = ["vendor"]
    ls = create_ls(ignored_paths=ignored_paths, language=Language.RUBY)
    ls.start()
    try:
        yield ls
    finally:
        ls.stop()


@pytest.mark.parametrize("ls_with_ignored_dirs", [Language.RUBY], indirect=True)
def test_symbol_tree_ignores_dir(ls_with_ignored_dirs: SolidLanguageServer):
    """Tests that request_full_symbol_tree ignores the configured directory."""
    root = ls_with_ignored_dirs.request_full_symbol_tree()[0]
    root_children = root["children"]
    children_names = {child["name"] for child in root_children}
    assert "vendor" not in children_names


@pytest.mark.parametrize("ls_with_ignored_dirs", [Language.RUBY], indirect=True)
def test_find_references_ignores_dir(ls_with_ignored_dirs: SolidLanguageServer):
    """Tests that find_references ignores the configured directory."""
    # Location of Calculator, which is referenced in vendor/dummy.rb
    definition_file = "lib.rb"
    definition_line = 0
    definition_col = 6

    references = ls_with_ignored_dirs.request_references(definition_file, definition_line, definition_col)

    # assert that vendor does not appear in the references
    assert not any("vendor" in ref["uri"] for ref in references)
