from typing import Dict, Type
from tools.base_tool import BaseTool

class ToolRegistry:
    """
    Registry for storing and accessing tools.
    The Assistant uses this registry to find tools.
    """
    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}

    def register(self, tool: BaseTool) -> None:
        """Register a tool to the registry."""
        self._tools[tool.name] = tool

    def get(self, name: str) -> BaseTool:
        """Get a tool by name."""
        if name not in self._tools:
            raise ValueError(f"Tool '{name}' not found in registry.")
        return self._tools[name]

    def list_tools(self) -> Dict[str, str]:
        """List all available tools."""
        return {name: tool.description for name, tool in self._tools.items()}

    def get_all_tools(self) -> Dict[str, BaseTool]:
        """Get all registered tools."""
        return self._tools.copy()

# Singleton instance
_registry = None

def get_registry() -> ToolRegistry:
    """Get or create singleton registry instance."""
    global _registry
    if _registry is None:
        _registry = ToolRegistry()
    return _registry
