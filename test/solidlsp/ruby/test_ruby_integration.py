import os

import pytest

from serena.project import Project
from serena.text_utils import LineType
from solidlsp.ls_config import Language


@pytest.mark.ruby
class TestRubyProjectBasics:
    @pytest.mark.parametrize("project", [Language.RUBY], indirect=True)
    def test_retrieve_content_around_line(self, project: Project) -> None:
        """Test retrieve_content_around_line functionality with various scenarios."""
        file_path = os.path.join("main.rb")

        # Scenario 1: Just a single line (DemoClass class definition)
        line_2 = project.retrieve_content_around_line(file_path, 2)
        assert len(line_2.lines) == 1
        assert "class DemoClass" in line_2.lines[0].line_content
        assert line_2.lines[0].line_number == 2
        assert line_2.lines[0].match_type == LineType.MATCH

        # Scenario 2: Context above and below
        with_context_around_class = project.retrieve_content_around_line(file_path, 2, 2, 2)
        assert len(with_context_around_class.lines) == 5
        assert "class DemoClass" in with_context_around_class.matched_lines[0].line_content
        assert with_context_around_class.num_matched_lines == 1
        assert "attr_accessor :value" in with_context_around_class.lines[3].line_content
        assert with_context_around_class.lines[0].line_number == 0
        assert with_context_around_class.lines[1].line_number == 1
        assert with_context_around_class.lines[2].line_number == 2
        assert with_context_around_class.lines[3].line_number == 3
        assert with_context_around_class.lines[4].line_number == 4
        assert with_context_around_class.lines[0].match_type == LineType.BEFORE_MATCH
        assert with_context_around_class.lines[1].match_type == LineType.BEFORE_MATCH
        assert with_context_around_class.lines[2].match_type == LineType.MATCH
        assert with_context_around_class.lines[3].match_type == LineType.AFTER_MATCH
        assert with_context_around_class.lines[4].match_type == LineType.AFTER_MATCH

    @pytest.mark.parametrize("project", [Language.RUBY], indirect=True)
    def test_search_files_for_pattern(self, project: Project) -> None:
        """Test search_files_for_pattern with various patterns and glob filters."""
        # Test 1: Search for class definitions across all files
        class_pattern = r"class\s+\w+"
        matches = project.search_source_files_for_pattern(class_pattern)
        assert len(matches) > 0
        assert len(matches) >= 2  # DemoClass and Calculator

        # Test 2: Search for specific class with include glob
        demo_class_pattern = r"class\s+DemoClass"
        matches = project.search_source_files_for_pattern(demo_class_pattern, paths_include_glob="**/main.rb")
        assert len(matches) == 1
        assert "main.rb" in matches[0].source_file_path

        # Test 3: Search for method definitions with exclude glob
        method_pattern = r"def\s+\w+"
        matches = project.search_source_files_for_pattern(method_pattern, paths_exclude_glob="**/lib.rb")
        assert len(matches) > 0
        assert all("lib.rb" not in match.source_file_path for match in matches)

        # Test 4: Search with a pattern that should have no matches
        no_match_pattern = r"def\s+this_method_does_not_exist"
        matches = project.search_source_files_for_pattern(no_match_pattern)
        assert len(matches) == 0
