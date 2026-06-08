"""Tests for ticker watchlist input parsing and normalization."""

import os
import sys
from pathlib import Path
from tempfile import NamedTemporaryFile

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.ticker_watchlist import normalize_tickers, load_tickers_from_file


def test_normalize_tickers_uppercase():
    """Test that tickers are converted to uppercase."""
    tickers = normalize_tickers(["maia", "abcd", "XYZ"])
    assert tickers == ["MAIA", "ABCD", "XYZ"]


def test_normalize_tickers_strip_whitespace():
    """Test that whitespace is stripped from tickers."""
    tickers = normalize_tickers([" MAIA ", "  ABCD", "XYZ  "])
    assert tickers == ["MAIA", "ABCD", "XYZ"]


def test_normalize_tickers_remove_duplicates():
    """Test that duplicate tickers are removed while preserving order."""
    tickers = normalize_tickers(["MAIA", "ABCD", "MAIA", "XYZ", "abcd"])
    assert tickers == ["MAIA", "ABCD", "XYZ"]


def test_normalize_tickers_skip_empty():
    """Test that empty strings are skipped."""
    tickers = normalize_tickers(["MAIA", "", "  ", "ABCD"])
    assert tickers == ["MAIA", "ABCD"]


def test_normalize_tickers_skip_invalid():
    """Test that invalid ticker symbols are skipped with warning."""
    tickers = normalize_tickers(["MAIA", "AB@CD", "XYZ", "!!!"])
    # Should only keep valid tickers
    assert tickers == ["MAIA", "XYZ"]


def test_load_tickers_from_file():
    """Test loading tickers from a file."""
    # Create temporary file with ticker list
    with NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8") as f:
        f.write("# Comment line\n")
        f.write("MAIA\n")
        f.write("  ABCD  \n")  # With whitespace
        f.write("# Another comment\n")
        f.write("XYZ\n")
        f.write("\n")  # Empty line
        temp_path = Path(f.name)

    try:
        tickers = load_tickers_from_file(temp_path)
        assert tickers == ["MAIA", "ABCD", "XYZ"]
    finally:
        temp_path.unlink()


def test_load_tickers_from_file_nonexistent():
    """Test that loading from nonexistent file raises FileNotFoundError."""
    try:
        load_tickers_from_file(Path("/nonexistent/file.txt"))
        assert False, "Should have raised FileNotFoundError"
    except FileNotFoundError:
        pass


def test_normalize_tickers_allows_hyphens_and_dots():
    """Test that tickers with hyphens and dots are allowed."""
    tickers = normalize_tickers(["BRK.B", "BRK-A", "MAIA"])
    assert tickers == ["BRK.B", "BRK-A", "MAIA"]
