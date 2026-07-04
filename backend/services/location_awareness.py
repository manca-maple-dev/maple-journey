"""
Location Awareness Engine — Geo-based resource matching
Detects user location and surfaces nearby shelters, legal aid, health clinics, hotlines
"""
import logging
from typing import List, Dict, Optional
from math import radians, cos, sin, asin, sqrt
from enum import Enum

logger = logging.getLogger("maple.location_awareness")


class ResourceType(str, Enum):
    SHELTER = "shelter"
    LEGAL_AID = "legal_aid"
    HEALTH_CLINIC = "health_clinic"
    FOOD_BANK = "food_bank"
    SETTLEMENT_SERVICES = "settlement_services"
    DV_SERVICES = "dv_services"
    LGBTQ_SERVICES = "lgbtq_services"
    HOTLINE = "hotline"


class LocationAwarenessEngine:
    """
    Matches user location to nearby resources.
    Uses geohashing for efficient spatial queries.
    """

    def __init__(self):
        self.resource_types = ResourceType
        self.search_radius_km = 5  # Default: find resources within 5km

    def haversine(
        self, 
        lat1: float, 
        lon1: float, 
        lat2: float, 
        lon2: float
    ) -> float:
        """
        Calculate distance between two lat/lon points in kilometers.
        """
        lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
        dlon = lon2 - lon1
        dlat = lat2 - lat1
        a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
        c = 2 * asin(sqrt(a))
        km = 6371 * c
        return km

    async def find_nearby_resources(
        self,
        latitude: float,
        longitude: float,
        resource_type: Optional[ResourceType] = None,
        radius_km: Optional[float] = None,
        db = None,
    ) -> List[Dict]:
        """
        Find resources near user's location.
        """
        if db is None:
            logger.warning("No database connection for location search")
            return []

        try:
            radius = radius_km or self.search_radius_km
            
            # Query resources collection (geo-indexed)
            query = {
                "location": {
                    "$nearSphere": {
                        "$geometry": {
                            "type": "Point",
                            "coordinates": [longitude, latitude],
                        },
                        "$maxDistance": radius * 1000,  # Convert to meters
                    }
                }
            }
            
            if resource_type:
                query["type"] = resource_type.value

            resources = await db.resources.find(query).to_list(20)
            
            # Add distance for sorting
            results = []
            for resource in resources:
                dist = self.haversine(
                    latitude,
                    longitude,
                    resource["location"]["coordinates"][1],
                    resource["location"]["coordinates"][0],
                )
                resource["distance_km"] = round(dist, 2)
                results.append(resource)

            # Sort by distance
            results.sort(key=lambda r: r["distance_km"])
            
            logger.info(f"Found {len(results)} resources near ({latitude}, {longitude})")
            return results

        except Exception as e:
            logger.error(f"Location search failed: {e}")
            return []

    async def get_urgent_resources(
        self,
        latitude: float,
        longitude: float,
        emergency_type: str,  # "dv", "health", "food", "shelter", "legal"
        db = None,
    ) -> List[Dict]:
        """
        Get critical resources for emergency situations.
        Returns closest relevant resource with full contact info.
        """
        type_mapping = {
            "dv": ResourceType.DV_SERVICES,
            "health": ResourceType.HEALTH_CLINIC,
            "food": ResourceType.FOOD_BANK,
            "shelter": ResourceType.SHELTER,
            "legal": ResourceType.LEGAL_AID,
        }

        resource_type = type_mapping.get(emergency_type)
        if not resource_type:
            return []

        return await self.find_nearby_resources(
            latitude,
            longitude,
            resource_type=resource_type,
            radius_km=15,  # Extended radius for emergencies
            db=db,
        )


location_engine = LocationAwarenessEngine()
