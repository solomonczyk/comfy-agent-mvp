"""Dangerous Tool Registry

Defines categories of dangerous tools that require special authorization.
"""

from typing import List, Dict, Set


class DangerousToolRegistry:
    """Registry of dangerous tools and their categories"""

    # Dangerous tool categories as specified in requirements
    DANGEROUS_CATEGORIES = {
        "comfyui.submit": ["generation", "comfyui", "execution"],
        "generation.run": ["generation", "execution"],
        "retry.run": ["retry", "execution"],
        "preview.render": ["render", "preview", "execution"],
        "voice.generate": ["voice", "generation", "execution"],
        "assembly.run": ["assembly", "execution"],
        "final_render.run": ["render", "execution", "production"],
        "asset.download": ["asset", "download", "external"],
        "asset.install": ["asset", "install", "external"],
        "external_api.call": ["api", "external", "network"],
        "git.force_push": ["git", "destructive"],
        "production.accept": ["production", "acceptance", "destructive"],
    }

    # Additional dangerous tools that should be blocked
    ADDITIONAL_DANGEROUS = {
        "image.edit": ["image", "edit", "execution"],
        "image.upscale": ["image", "upscale", "execution"],
        "visual_qa.accept": ["visual", "qa", "acceptance"],
        "operator.visual.accept": ["visual", "operator", "acceptance"],
        "state.mutate": ["state", "mutation", "destructive"],
    }

    def __init__(self):
        self.registry: Dict[str, List[str]] = {}
        self.registry.update(self.DANGEROUS_CATEGORIES)
        self.registry.update(self.ADDITIONAL_DANGEROUS)

    def get_dangerous_categories(self, tool: str) -> List[str]:
        """Get dangerous categories for a tool"""
        return self.registry.get(tool, [])

    def is_dangerous(self, tool: str) -> bool:
        """Check if a tool is dangerous"""
        return tool in self.registry

    def get_all_dangerous_tools(self) -> List[str]:
        """Get all dangerous tools"""
        return list(self.registry.keys())

    def get_tools_by_category(self, category: str) -> List[str]:
        """Get all tools in a specific category"""
        return [tool for tool, cats in self.registry.items() if category in cats]

    def to_dict(self) -> Dict:
        """Export registry as dictionary"""
        return {
            "dangerous_tools": self.registry,
            "total_count": len(self.registry),
        }
