from typing import List, Dict, Any, Union
from collections import Counter
from Backend.classes.Skill_Database_Handler import ESCODatabase

class VisualizationProcessor:
    def __init__(self):
        self.esco_db = ESCODatabase()

    def _get_attr(self, obj: Any, key: str, default: Any = None) -> Any:
        """Helper to get attribute from dict or object."""
        if isinstance(obj, dict):
            return obj.get(key, default)
        return getattr(obj, key, default)

    def process_custom_skills(self, skills: List[Any]) -> Dict[str, Any]:
        """
        Process skills for Donut (type distribution) and Density (confidence) charts.
        """
        # Donut Chart: Count by type
        types = [self._get_attr(s, "type", "Unknown") for s in skills]
        type_counts = Counter(types)
        
        donut_data = {
            "labels": list(type_counts.keys()),
            "datasets": [{
                "data": list(type_counts.values()),
                "backgroundColor": [
                    "#FF6384", "#36A2EB", "#FFCE56", "#4BC0C0", "#9966FF", "#FF9F40"
                ]
            }]
        }

        # Density Chart: Bins for confidence
        bins = [0] * 10
        for skill in skills:
            confidence = self._get_attr(skill, "confidence", 0)
            # Normalize if needed (assuming 0-1)
            if confidence > 1.0:
                confidence /= 100.0
            
            idx = min(int(confidence * 10), 9)
            bins[idx] += 1
            
        density_data = {
            "labels": [f"{i/10:.1f}-{(i+1)/10:.1f}" for i in range(10)],
            "datasets": [{
                "label": "Confidence",
                "data": bins,
                "backgroundColor": "rgba(54, 162, 235, 0.5)",
                "borderColor": "rgba(54, 162, 235, 1)",
                "borderWidth": 1
            }]
        }

        return {
            "donut": donut_data,
            "density": density_data
        }

    def process_esco_hierarchy(self, skills: List[Any]) -> Dict[str, Any]:
        """
        Build nested dictionary for Sunburst Chart.
        """
        root = {"name": "Skills", "children": []}
        
        for skill in skills:
            uri = self._get_attr(skill, "uri")
            name = self._get_attr(skill, "title") or self._get_attr(skill, "name", "Unknown")
            links = self._get_attr(skill, "links")
            
            if not uri:
                # Treat as "Other" or "Custom"
                parent_name = "Custom/Other"
            else:
                parent_name = "Uncategorized"
                # Use provided links if available to avoid API call
                if links and isinstance(links, dict):
                     if "broaderHierarchyConcept" in links:
                        parents = links["broaderHierarchyConcept"]
                        if isinstance(parents, list) and parents:
                            parent_name = parents[0].get("title", "Unknown")
                        elif isinstance(parents, dict):
                            parent_name = parents.get("title", "Unknown")
                     elif "broaderSkill" in links:
                        parents = links["broaderSkill"]
                        if isinstance(parents, list) and parents:
                             parent_name = parents[0].get("title", "Unknown")
                        elif isinstance(parents, dict):
                             parent_name = parents.get("title", "Unknown")
                
                # Fallback to API only if absolutely necessary and no links provided
                elif uri: 
                    # Fetch details for hierarchy
                    try:
                        details = self.esco_db.get_skill_details(uri)
                        if details and "_links" in details:
                            links = details["_links"]
                            # Check broaderHierarchyConcept (top level) or broaderSkill
                            if "broaderHierarchyConcept" in links:
                                parents = links["broaderHierarchyConcept"]
                                if isinstance(parents, list) and parents:
                                    parent_name = parents[0].get("title", "Unknown")
                                elif isinstance(parents, dict):
                                    parent_name = parents.get("title", "Unknown")
                            elif "broaderSkill" in links:
                                parents = links["broaderSkill"]
                                if isinstance(parents, list) and parents:
                                     parent_name = parents[0].get("title", "Unknown")
                                elif isinstance(parents, dict):
                                     parent_name = parents.get("title", "Unknown")
                    except Exception as e:
                         print(f"Error fetching details for {uri}: {e}")

            # Add to tree
            # Find parent node
            parent_node = next((c for c in root["children"] if c["name"] == parent_name), None)
            if not parent_node:
                parent_node = {"name": parent_name, "children": []}
                root["children"].append(parent_node)
            
            # Add skill
            parent_node["children"].append({"name": name, "value": 1})

        return root

    def match_occupations(self, skills: List[Any]) -> List[Dict[str, Any]]:
        """
        Extract related occupations and return Top 5.
        """
        occupations = {}
        
        # 1. Try to use links from skills first
        for skill in skills:
            uri = self._get_attr(skill, "uri")
            links = self._get_attr(skill, "links")
            
            if uri and links and isinstance(links, dict):
                 for rel_type in ["isEssentialForOccupation", "isOptionalForOccupation"]:
                    if rel_type in links:
                        items = links[rel_type]
                        if isinstance(items, dict):
                            items = [items]
                        
                        for item in items:
                            occ_uri = item.get("uri")
                            title = item.get("title", "Unknown")
                            if occ_uri:
                                if occ_uri not in occupations:
                                    occupations[occ_uri] = {
                                        "title": title,
                                        "uri": occ_uri,
                                        "count": 0,
                                        "relations": []
                                    }
                                occupations[occ_uri]["count"] += 1
        
        # 2. If no occupations found from local links, try API for URIs (limited batch to avoid timeout)
        if not occupations:
            uris = [self._get_attr(s, "uri") for s in skills if self._get_attr(s, "uri")]
            if uris:
                 # Limit to first 10 skills to prevent massive delays
                 occupations_map = self.esco_db.get_related_occupations(uris[:10])
                 occupations.update(occupations_map)
        
        # Sort by count
        sorted_occs = sorted(
            occupations.values(),
            key=lambda x: x["count"],
            reverse=True
        )
        
        # Return top 5
        return sorted_occs[:5]

    def process_radar_data(self, skills: List[Any]) -> Dict[str, Any]:
        """
        Categorize skills into 4 pillars.
        """
        categories = {
            "Knowledge": 0,
            "Skills": 0,
            "Attitudes": 0,
            "Language": 0
        }
        
        for skill in skills:
            # Check type or infer
            s_type = str(self._get_attr(skill, "type", "")).lower()
            
            if "knowledge" in s_type:
                categories["Knowledge"] += 1
            elif "language" in s_type:
                categories["Language"] += 1
            elif "attitude" in s_type or "social" in s_type:
                categories["Attitudes"] += 1
            else:
                # default
                categories["Skills"] += 1
        
        return {
            "labels": list(categories.keys()),
            "datasets": [{
                "label": "Skill Pillars",
                "data": list(categories.values()),
                "fill": True,
                "backgroundColor": "rgba(255, 99, 132, 0.2)",
                "borderColor": "rgb(255, 99, 132)",
                "pointBackgroundColor": "rgb(255, 99, 132)",
                "pointBorderColor": "#fff",
                "pointHoverBackgroundColor": "#fff",
                "pointHoverBorderColor": "rgb(255, 99, 132)"
            }]
        }

