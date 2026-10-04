"""
utils.py
---------
Utility functions used across the Intelligent Resume Analyzer project.

This module contains only helper functions that deal with:
    - Reading text files safely
    - Cleaning and normalizing text
    - Splitting text into individual words (tokenization)
    - Validating uploaded files
    - Saving the generated analysis report
    - Producing formatted date / time strings

Only Python's Standard Library is used (string, os, re, datetime, pathlib).
"""

import os
import re
import string
import datetime
from pathlib import Path


# --------------------------------------------------------------------------
# FILE VALIDATION
# --------------------------------------------------------------------------

def is_txt_file(file_path: str) -> bool:
    """
    Check whether the given file path points to a plain text (.txt) file.

    Args:
        file_path (str): Path of the file selected by the user.

    Returns:
        bool: True if the file has a .txt extension, False otherwise.
    """
    if not file_path:
        return False
    return Path(file_path).suffix.lower() == ".txt"


def list_txt_files_in_folder(folder_path: str) -> list:
    """
    Scan a folder (non-recursive) and return the full paths of every
    plain text (.txt) file found inside it, sorted alphabetically by
    filename for a predictable, stable display order.

    Args:
        folder_path (str): Path of the folder to scan.

    Returns:
        list: Sorted list of full paths to .txt files found in the
              folder. Returns an empty list if the folder does not
              exist or contains no .txt files.
    """
    if not folder_path or not os.path.isdir(folder_path):
        return []

    txt_files = [
        os.path.join(folder_path, name)
        for name in os.listdir(folder_path)
        if name.lower().endswith(".txt") and os.path.isfile(os.path.join(folder_path, name))
    ]
    return sorted(txt_files, key=lambda p: os.path.basename(p).lower())


def file_exists(file_path: str) -> bool:
    """
    Check whether a file physically exists on disk.

    Args:
        file_path (str): Path of the file to check.

    Returns:
        bool: True if the file exists, False otherwise.
    """
    return bool(file_path) and os.path.isfile(file_path)


def list_txt_files_in_folder(folder_path: str) -> list:
    """
    Scan a folder (non-recursively) and return the full paths of every
    plain text (.txt) file found inside it, sorted alphabetically by
    filename.

    Args:
        folder_path (str): Path of the folder to scan.

    Returns:
        list: Sorted list of full file paths ending in .txt. Empty list
              if the folder does not exist or contains no .txt files.
    """
    if not folder_path or not os.path.isdir(folder_path):
        return []

    txt_files = [
        os.path.join(folder_path, name)
        for name in os.listdir(folder_path)
        if name.lower().endswith(".txt") and os.path.isfile(os.path.join(folder_path, name))
    ]
    return sorted(txt_files, key=lambda p: os.path.basename(p).lower())


# --------------------------------------------------------------------------
# FILE READING
# --------------------------------------------------------------------------

def read_text_file(file_path: str) -> str:
    """
    Read the full content of a plain text file.

    Args:
        file_path (str): Path of the .txt file to read.

    Returns:
        str: The raw text content of the file.

    Raises:
        OSError: If the file cannot be opened or read.
        UnicodeDecodeError: If the file cannot be decoded as text.
    """
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()
    return content


# --------------------------------------------------------------------------
# TEXT CLEANING AND TOKENIZATION
# --------------------------------------------------------------------------

def to_lowercase(text: str) -> str:
    """Convert all characters in the given text to lowercase."""
    return text.lower()


def remove_punctuation(text: str) -> str:
    """
    Remove all punctuation characters from the given text.

    Uses Python's built-in string.punctuation table and re for
    replacing punctuation with a single space so that words which
    were separated only by punctuation (e.g. "Python/Java") do not
    get merged into one token.
    """
    # Replace punctuation characters with a space instead of deleting them,
    # so words separated by punctuation don't accidentally join together.
    translator = str.maketrans(string.punctuation, " " * len(string.punctuation))
    return text.translate(translator)


def remove_extra_spaces(text: str) -> str:
    """Collapse multiple consecutive whitespace characters into a single space."""
    return re.sub(r"\s+", " ", text).strip()


def clean_text(text: str) -> str:
    """
    Full text cleaning pipeline:
        1. Convert to lowercase
        2. Remove punctuation
        3. Remove unnecessary/extra spaces

    Args:
        text (str): Raw text extracted from a file.

    Returns:
        str: Cleaned text ready for tokenization.
    """
    text = to_lowercase(text)
    text = remove_punctuation(text)
    text = remove_extra_spaces(text)
    return text


def tokenize(text: str) -> list:
    """
    Split cleaned text into individual words using Python's built-in
    string split() method (no external tokenizer libraries).

    Args:
        text (str): Cleaned text.

    Returns:
        list: List of individual word tokens.
    """
    if not text:
        return []
    return text.split(" ")


def unique_words(words: list) -> set:
    """
    Remove duplicate words from a list of words using a set.

    Args:
        words (list): List of word tokens (may contain duplicates).

    Returns:
        set: Set of unique words.
    """
    # Filter out empty strings that may appear after cleaning/splitting.
    return {word for word in words if word.strip() != ""}


def extract_unique_words_from_text(text: str) -> set:
    """
    Convenience function that runs the full pipeline:
    clean -> tokenize -> remove duplicates.

    Args:
        text (str): Raw text.

    Returns:
        set: Set of unique, cleaned words.
    """
    cleaned = clean_text(text)
    words = tokenize(cleaned)
    return unique_words(words)


# --------------------------------------------------------------------------
# DATE / TIME HELPERS
# --------------------------------------------------------------------------

def get_current_date() -> str:
    """Return the current date as a formatted string (DD-MM-YYYY)."""
    return datetime.datetime.now().strftime("%d-%m-%Y")


def get_current_time() -> str:
    """Return the current time as a formatted string (HH:MM:SS)."""
    return datetime.datetime.now().strftime("%H:%M:%S")


# --------------------------------------------------------------------------
# REPORT SAVING
# --------------------------------------------------------------------------

def save_report(report_text: str, save_path: str) -> None:
    """
    Save the given report text to a .txt file at the specified path.

    Args:
        report_text (str): The complete formatted report text.
        save_path (str): Destination file path (should end with .txt).

    Raises:
        OSError: If the file cannot be written.
    """
    with open(save_path, "w", encoding="utf-8") as f:
        f.write(report_text)


def ensure_directory_exists(directory_path: str) -> None:
    """
    Create a directory (and any missing parent directories) if it
    does not already exist.

    Args:
        directory_path (str): Path of the directory to ensure exists.
    """
    Path(directory_path).mkdir(parents=True, exist_ok=True)
