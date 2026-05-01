"""
Combine Route Family Registry

Universal route family registry for the internal multi-agent orchestrator.
This registry is route-agnostic and supports all route families equally.
No single route family is treated as a universal default.
"""

from typing import List, Dict, Optional
from .contracts import CombineRouteCandidate


class RouteFamilyRegistry:
    """Universal route family registry"""
    
    # All supported route families
    ROUTE_FAMILIES = [
        "portrait_character_identity",
        "product_visual",
        "ugc_testimonial",
        "platform_ad_creative",
        "social_short_vertical",
        "cinematic_scene",
        "educational_explainer",
        "image_to_video",
        "video_to_video",
        "batch_variations",
        "custom"
    ]
    
    # Route family policies (metadata about each route family)
    ROUTE_FAMILY_POLICIES: Dict[str, Dict] = {
        "portrait_character_identity": {
            "description": "Portrait and character identity generation",
            "requires_character_reference": True,
            "typical_assets": ["portrait", "character_sheet"],
            "supports_video": True
        },
        "product_visual": {
            "description": "Product image and product video generation",
            "requires_product_reference": True,
            "typical_assets": ["product_image", "product_video"],
            "supports_video": True
        },
        "ugc_testimonial": {
            "description": "UGC and testimonial content generation",
            "requires_testimonial_script": True,
            "typical_assets": ["ugc_frame", "testimonial_video"],
            "supports_video": True
        },
        "platform_ad_creative": {
            "description": "Platform ad creative generation (Meta, TikTok, etc.)",
            "requires_ad_specs": True,
            "typical_assets": ["ad_creative", "ad_video"],
            "supports_video": True
        },
        "social_short_vertical": {
            "description": "Social short form vertical video (reels, shorts)",
            "requires_vertical_format": True,
            "typical_assets": ["vertical_video", "social_post"],
            "supports_video": True
        },
        "cinematic_scene": {
            "description": "Cinematic scene generation",
            "requires_scene_description": True,
            "typical_assets": ["cinematic_frame", "scene_video"],
            "supports_video": True
        },
        "educational_explainer": {
            "description": "Educational and explainer content generation",
            "requires_educational_content": True,
            "typical_assets": ["explainer_frame", "educational_video"],
            "supports_video": True
        },
        "image_to_video": {
            "description": "Image to video conversion",
            "requires_source_image": True,
            "typical_assets": ["video_from_image"],
            "supports_video": True
        },
        "video_to_video": {
            "description": "Video to video conversion/style transfer",
            "requires_source_video": True,
            "typical_assets": ["styled_video"],
            "supports_video": True
        },
        "batch_variations": {
            "description": "Batch generation of variations",
            "requires_base_asset": True,
            "typical_assets": ["variation_batch"],
            "supports_video": True
        },
        "custom": {
            "description": "Custom route for user-defined workflows",
            "requires_custom_config": True,
            "typical_assets": ["custom_output"],
            "supports_video": True
        }
    }
    
    @classmethod
    def list_route_families(cls) -> List[str]:
        """List all supported route families"""
        return cls.ROUTE_FAMILIES.copy()
    
    @classmethod
    def is_supported_route_family(cls, route_family: str) -> bool:
        """Check if a route family is supported"""
        return route_family in cls.ROUTE_FAMILIES
    
    @classmethod
    def get_route_family_policy(cls, route_family: str) -> Dict:
        """Get policy for a route family"""
        if not cls.is_supported_route_family(route_family):
            raise ValueError(f"Unsupported route family: {route_family}")
        return cls.ROUTE_FAMILY_POLICIES[route_family].copy()
    
    @classmethod
    def classify_route_stub(cls, brief: Dict) -> List[CombineRouteCandidate]:
        """
        Stub classifier for route classification.
        
        This is a simple deterministic keyword-based classifier for now.
        It returns candidates, not a final hardcoded universal default.
        
        Args:
            brief: Brief dictionary with route information
            
        Returns:
            List of route candidates with confidence scores
        """
        candidates = []
        brief_text = str(brief).lower()
        
        # Simple keyword-based classification
        if "portrait" in brief_text or "character" in brief_text:
            candidates.append(CombineRouteCandidate(
                route_family="portrait_character_identity",
                confidence=0.8,
                reason="Brief contains portrait/character keywords"
            ))
        
        if "product" in brief_text:
            candidates.append(CombineRouteCandidate(
                route_family="product_visual",
                confidence=0.8,
                reason="Brief contains product keywords"
            ))
        
        if "ugc" in brief_text or "testimonial" in brief_text:
            candidates.append(CombineRouteCandidate(
                route_family="ugc_testimonial",
                confidence=0.8,
                reason="Brief contains UGC/testimonial keywords"
            ))
        
        if "ad" in brief_text or "meta" in brief_text or "tiktok" in brief_text:
            candidates.append(CombineRouteCandidate(
                route_family="platform_ad_creative",
                confidence=0.8,
                reason="Brief contains ad/platform keywords"
            ))
        
        if "cinematic" in brief_text or "scene" in brief_text:
            candidates.append(CombineRouteCandidate(
                route_family="cinematic_scene",
                confidence=0.8,
                reason="Brief contains cinematic/scene keywords"
            ))
        
        if "educational" in brief_text or "explainer" in brief_text:
            candidates.append(CombineRouteCandidate(
                route_family="educational_explainer",
                confidence=0.8,
                reason="Brief contains educational/explainer keywords"
            ))
        
        if "image_to_video" in brief_text or "img2vid" in brief_text:
            candidates.append(CombineRouteCandidate(
                route_family="image_to_video",
                confidence=0.9,
                reason="Brief contains image-to-video keywords"
            ))
        
        if "video_to_video" in brief_text or "vid2vid" in brief_text:
            candidates.append(CombineRouteCandidate(
                route_family="video_to_video",
                confidence=0.9,
                reason="Brief contains video-to-video keywords"
            ))
        
        if "batch" in brief_text or "variation" in brief_text:
            candidates.append(CombineRouteCandidate(
                route_family="batch_variations",
                confidence=0.8,
                reason="Brief contains batch/variation keywords"
            ))
        
        # Always include custom as a fallback
        candidates.append(CombineRouteCandidate(
            route_family="custom",
            confidence=0.5,
            reason="Custom route is always available as fallback"
        ))
        
        # If no candidates found, return only custom
        if not candidates:
            candidates.append(CombineRouteCandidate(
                route_family="custom",
                confidence=0.5,
                reason="No specific route detected, using custom"
            ))
        
        # Sort by confidence
        candidates.sort(key=lambda x: x.confidence, reverse=True)
        
        return candidates
