from typing import List, Dict, Any, Union
from collections import Counter
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from Backend.classes.Skill_Database_Handler import ESCODatabase

class VisualizationProcessor:
    def __init__(self):
        self.esco_db = ESCODatabase()
        # Simple cache for skill details to avoid redundant API calls
        self._skill_details_cache = {}
        # Define the specific S-categories requested by user
        self.S_CATEGORIES = {
            "S1": "communication, collaboration and creativity",
            "S2": "information skills",
            "S3": "assisting and caring",
            "S4": "management skills",
            "S5": "working with computers",
            "S6": "handling and moving",
            "S7": "constructing",
            "S8": "working with machinery and specialised equipment"
        }
    
    def _get_skill_details_cached(self, uri: str) -> Dict[str, Any]:
        """Get skill details with caching."""
        if uri not in self._skill_details_cache:
            self._skill_details_cache[uri] = self.esco_db.get_skill_details(uri)
        return self._skill_details_cache[uri]

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

    def match_occupations(self, skills: List[Any]) -> List[Dict[str, Any]]:
        """
        Extract related occupations, calculate match ratio, and return Top 5.
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
        
        # 2. If no occupations found from local links, try API for URIs (limited batch)
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
        
        top_5 = sorted_occs[:5]

        # 3. Enrich with total skills count for match ratio (parallelized)
        def fetch_occupation_total(occ):
            try:
                details = self.esco_db.get_occupation_details(occ["uri"])
                total_skills = 0
                if details and "_links" in details:
                    links = details["_links"]
                    # Count essential and optional skills
                    if "hasEssentialSkill" in links:
                        skills_list = links["hasEssentialSkill"]
                        total_skills += len(skills_list) if isinstance(skills_list, list) else 1
                    if "hasOptionalSkill" in links:
                        skills_list = links["hasOptionalSkill"]
                        total_skills += len(skills_list) if isinstance(skills_list, list) else 1
                return occ, total_skills
            except Exception as e:
                print(f"Error fetching details for occupation {occ.get('title')}: {e}")
                return occ, 0
        
        # Fetch all occupation totals in parallel
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {executor.submit(fetch_occupation_total, occ): occ for occ in top_5}
            for future in as_completed(futures):
                occ, total_skills = future.result()
                occ["total"] = total_skills
        
        return top_5

    def process_radar_data(self, skills: List[Any]) -> Dict[str, Any]:
        """
        Categorize skills into specific S-subgroups based on hierarchy.
        Maps to S1-S8 categories.
        """
        # Initialize with 0 for all target categories to ensure they appear on chart
        # Use dictionary first, then convert to Counter logic
        categories_map = {name: 0 for name in self.S_CATEGORIES.values()}
        
        # Regex to match S<digit> in URI
        # Matches .../skill/S1 or .../skill/S1.2.3
        s_pattern = re.compile(r'/skill/S(\d)')
        
        # Helper to check list of parents
        def check_parents(parents_list):
            if not parents_list:
                return None
            if isinstance(parents_list, dict):
                parents_list = [parents_list]
            
            for parent in parents_list:
                # Parent can be string URI or dict with 'uri'
                p_uri = parent if isinstance(parent, str) else parent.get("uri", "")
                if p_uri:
                    match = s_pattern.search(p_uri)
                    if match:
                        s_num = "S" + match.group(1)
                        if s_num in self.S_CATEGORIES:
                            return self.S_CATEGORIES[s_num]
            return None

        # First pass: check existing links and URI patterns (no API calls)
        skills_needing_fetch = []
        for skill in skills:
            links = self._get_attr(skill, "links")
            uri = self._get_attr(skill, "uri")
            matched_category = None

            # 0. Quick check: extract S-category directly from URI if it matches pattern
            # Some skills have URIs like .../skill/S4.8.1 which we can parse directly
            if uri:
                uri_match = s_pattern.search(uri)
                if uri_match:
                    s_num = "S" + uri_match.group(1)
                    if s_num in self.S_CATEGORIES:
                        matched_category = self.S_CATEGORIES[s_num]

            # 1. Try to find hierarchy from existing links
            if not matched_category and links and isinstance(links, dict):
                # Check broaderHierarchyConcept first (most relevant)
                if "broaderHierarchyConcept" in links:
                    matched_category = check_parents(links["broaderHierarchyConcept"])
                
                # Fallback to broaderSkill
                if not matched_category and "broaderSkill" in links:
                    matched_category = check_parents(links["broaderSkill"])
            
            # 2. Assign category if found, otherwise mark for fetching
            if matched_category:
                categories_map[matched_category] += 1
            elif uri:
                skills_needing_fetch.append((skill, uri))
        
        # Second pass: fetch details in parallel for skills that need it
        def fetch_skill_category(skill_uri):
            try:
                details = self._get_skill_details_cached(skill_uri)
                if details and "_links" in details:
                    fetched_links = details["_links"]
                    if "broaderHierarchyConcept" in fetched_links:
                        matched = check_parents(fetched_links["broaderHierarchyConcept"])
                        if matched:
                            return matched
                    if "broaderSkill" in fetched_links:
                        matched = check_parents(fetched_links["broaderSkill"])
                        if matched:
                            return matched
            except Exception:
                pass
            return None
        
        # Fetch all missing categories in parallel (increased workers for faster processing)
        if skills_needing_fetch:
            with ThreadPoolExecutor(max_workers=20) as executor:
                futures = {executor.submit(fetch_skill_category, uri): uri for _, uri in skills_needing_fetch}
                for future in as_completed(futures):
                    matched_category = future.result()
                    if matched_category:
                        categories_map[matched_category] += 1
        
        # Keep only the requested S-categories
        final_data = {k: v for k, v in categories_map.items()}

        return {
            "labels": list(final_data.keys()),
            "datasets": [{
                "label": "Skill Groups",
                "data": list(final_data.values()),
                "fill": True,
                "backgroundColor": "rgba(255, 99, 132, 0.2)",
                "borderColor": "rgb(255, 99, 132)",
                "pointBackgroundColor": "rgb(255, 99, 132)",
                "pointBorderColor": "#fff",
                "pointHoverBackgroundColor": "#fff",
                "pointHoverBorderColor": "rgb(255, 99, 132)"
            }]
        }
