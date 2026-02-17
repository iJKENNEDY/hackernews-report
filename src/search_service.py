"""Search service for coordinating search operations."""

from typing import List, Tuple
import difflib

from src.search_engine import SearchEngine
from src.tags import TagSystem
from src.models import SearchQuery, SearchResult


class SearchService:
    """
    Service layer for search operations.

    Coordinates SearchEngine and TagSystem to provide a complete search
    experience with validation, tag management, and result highlighting.
    """

    def __init__(self, search_engine: SearchEngine, tag_system: TagSystem):
        """
        Initialize the SearchService.

        Args:
            search_engine: SearchEngine instance for executing queries
            tag_system: TagSystem instance for tag validation and suggestions
        """
        self.search_engine = search_engine
        self.tag_system = tag_system

    def search_posts(self, query: SearchQuery) -> SearchResult:
        """
        Execute a search query with validation.

        Validates the query before execution and returns results.

        Args:
            query: SearchQuery object with search criteria

        Returns:
            SearchResult with matching posts and pagination metadata

        Raises:
            ValueError: If the query is invalid
        """
        # Validate query
        is_valid, errors = self.validate_query(query)
        if not is_valid:
            raise ValueError(f"Invalid search query: {', '.join(errors)}")

        # Execute search
        return self.search_engine.search(query)

    def validate_query(self, query: SearchQuery) -> Tuple[bool, List[str]]:
        """
        Validate a search query and return validation errors.

        Performs comprehensive validation including:
        - Query criteria validation (from SearchQuery.validate())
        - Tag validation against TagSystem

        Args:
            query: SearchQuery object to validate

        Returns:
            Tuple of (is_valid, error_list)
            - is_valid: True if query is valid, False otherwise
            - error_list: List of validation error messages
        """
        errors = query.validate()

        # Additional validation: check if tags are valid
        if query.tags:
            available_tags = self.tag_system.get_all_tags()
            for tag in query.tags:
                if tag not in available_tags:
                    # Suggest similar tags
                    suggestions = self.suggest_tags(tag)
                    if suggestions:
                        errors.append(
                            f"Invalid tag '{tag}'. Did you mean: {', '.join(suggestions[:3])}?"
                        )
                    else:
                        errors.append(f"Invalid tag '{tag}'")

        return (len(errors) == 0, errors)

    def get_available_tags(self) -> List[str]:
        """
        Get a list of all available tags from the TagSystem.

        Returns:
            Sorted list of all tag names
        """
        return self.tag_system.get_all_tags()

    def suggest_tags(self, partial: str) -> List[str]:
        """
        Suggest tags similar to the given partial tag name.

        Uses fuzzy string matching to find tags that are similar to the
        provided partial string. Useful for handling typos or incomplete
        tag names.

        Args:
            partial: Partial or misspelled tag name

        Returns:
            List of suggested tag names, sorted by similarity (most similar first)
        """
        available_tags = self.tag_system.get_all_tags()

        # Use difflib to find close matches
        # cutoff=0.6 means at least 60% similarity
        suggestions = difflib.get_close_matches(
            partial,
            available_tags,
            n=5,  # Return up to 5 suggestions
            cutoff=0.6
        )

        return suggestions

    def highlight_terms(self, text: str, search_terms: List[str]) -> str:
        """
        Highlight search terms in text using markdown-style markers.

        Wraps each occurrence of search terms with **term** markers for
        CLI display. Performs case-insensitive matching.

        Args:
            text: Text to highlight terms in (typically a post title)
            search_terms: List of terms to highlight

        Returns:
            Text with search terms wrapped in **markers**

        Example:
            >>> highlight_terms("Python 3.11 released", ["python"])
            "**Python** 3.11 released"
        """
        if not search_terms or not text:
            return text

        # Sort terms by length (longest first) to handle overlapping terms correctly
        # This ensures "testing" is highlighted before "test"
        sorted_terms = sorted([t for t in search_terms if t.strip()], key=len, reverse=True)
        
        result = text

        # Process each search term
        for term in sorted_terms:
            term_lower = term.lower()
            text_lower = result.lower()

            # Build new string with highlights
            new_result = []
            i = 0
            while i < len(result):
                # Skip if we're inside a highlight marker
                if i > 0 and result[i-2:i] == "**":
                    # We're at the start of a highlighted term, skip to the end
                    end_marker = result.find("**", i)
                    if end_marker != -1:
                        # Copy everything up to and including the end marker
                        new_result.append(result[i:end_marker+2])
                        i = end_marker + 2
                        continue
                
                # Check if we're at the start of a match
                if text_lower[i:i+len(term)] == term_lower:
                    # Check if this position is already inside highlighted text
                    # Count ** markers before this position
                    markers_before = result[:i].count("**")
                    if markers_before % 2 == 0:  # Even number means we're not inside markers
                        # Extract the original case version
                        original_term = result[i:i+len(term)]
                        # Add highlighted version
                        new_result.append(f"**{original_term}**")
                        i += len(term)
                    else:
                        # We're inside markers, don't highlight
                        new_result.append(result[i])
                        i += 1
                else:
                    new_result.append(result[i])
                    i += 1

            result = ''.join(new_result)

        return result
