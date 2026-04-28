"""
GORYNYCH Knowledge Loader
Loads and validates knowledge files for the GORYNYCH-COMFY protocol.
"""

import os
from pathlib import Path
from typing import Optional


def get_knowledge_dir() -> Path:
    """Get the knowledge directory path."""
    base_dir = Path(__file__).parent.parent.parent
    return base_dir / "docs" / "knowledge"


def load_head_1() -> str:
    """
    Load HEAD 1 knowledge: Story Contract Knowledge.
    
    Returns:
        str: Content of head_1.md
        
    Raises:
        FileNotFoundError: If head_1.md does not exist
    """
    knowledge_dir = get_knowledge_dir()
    file_path = knowledge_dir / "head_1.md"
    
    if not file_path.exists():
        raise FileNotFoundError(
            f"Knowledge file not found: {file_path}. "
            "Ensure docs/knowledge/head_1.md exists."
        )
    
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()


def load_head_2() -> str:
    """
    Load HEAD 2 knowledge: Character Canon Knowledge.
    
    Returns:
        str: Content of head_2.md
        
    Raises:
        FileNotFoundError: If head_2.md does not exist
    """
    knowledge_dir = get_knowledge_dir()
    file_path = knowledge_dir / "head_2.md"
    
    if not file_path.exists():
        raise FileNotFoundError(
            f"Knowledge file not found: {file_path}. "
            "Ensure docs/knowledge/head_2.md exists."
        )
    
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()


def load_head_3() -> str:
    """
    Load HEAD 3 knowledge: Shot and Prompt Knowledge.
    
    Returns:
        str: Content of head_3.md
        
    Raises:
        FileNotFoundError: If head_3.md does not exist
    """
    knowledge_dir = get_knowledge_dir()
    file_path = knowledge_dir / "head_3.md"
    
    if not file_path.exists():
        raise FileNotFoundError(
            f"Knowledge file not found: {file_path}. "
            "Ensure docs/knowledge/head_3.md exists."
        )
    
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()


def validate_knowledge_files() -> bool:
    """
    Validate that all required knowledge files exist.
    
    Returns:
        bool: True if all knowledge files exist, False otherwise
    """
    knowledge_dir = get_knowledge_dir()
    required_files = ["head_1.md", "head_2.md", "head_3.md"]
    
    for filename in required_files:
        file_path = knowledge_dir / filename
        if not file_path.exists():
            return False
    
    return True


def load_all_knowledge() -> dict[str, str]:
    """
    Load all three knowledge files at once.
    
    Returns:
        dict: Dictionary with keys 'head_1', 'head_2', 'head_3' containing file contents
        
    Raises:
        FileNotFoundError: If any knowledge file is missing
    """
    return {
        "head_1": load_head_1(),
        "head_2": load_head_2(),
        "head_3": load_head_3(),
    }
