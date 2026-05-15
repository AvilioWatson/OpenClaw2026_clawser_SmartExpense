from abc import ABC, abstractmethod
from typing import Dict, Any

class BaseTool(ABC):
    """
    Abstract base class for all tools.
    Attributes:
        name: Unique identifier for the tool
        description: Description for LLM context
        version: Tool version
    """
    def __init__(self, name: str, description: str, version: str = "1.0"):
        self.name = name
        self.description = description
        self.version = version

    @abstractmethod
    def run(self, **kwargs) -> Dict[str, Any]:
        """
        Execute the tool with given parameters.
        Returns:
            Dictionary with execution results
        """
        pass

    @abstractmethod
    def validate_input(self, **kwargs) -> bool:
        """
        Validate input before execution.
        Returns:
            True if valid, False otherwise
        """
        pass

    def get_metadata(self) -> Dict[str, str]:
        """Return tool metadata for logging."""
        return {
            "tool_name": self.name,
            "tool_version": self.version,
            "tool_description": self.description
        }
