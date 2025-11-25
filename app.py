from Backend.api import app
import uvicorn


def main():
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8000,
        log_config=None,  # Disable uvicorn's logging config
        access_log=True   # Keep access logs but use your format
    )


if __name__ == "__main__":
    main()


# ### 1. Goal
# Visualize the skills extracted by your AI chatbot to provide insights into the user's competency profile. The visualizations will handle two distinct data types: **Custom Skills** (extracted by LLM) and **ESCO Skills** (standardized European taxonomy).

# ### 2. Selected Visualizations

# #### Custom Skills (Local Data)
# *   **Donut Chart:** Displays the distribution of skill types (Technical, Soft, Domain-specific, Other).
# *   **Density/Histogram Chart:** Visualizes the distribution of **Confidence Scores** (0.0 - 1.0) to show how certain the model is about the extracted skills.

# #### ESCO Skills (API Data)
# *   **Hierarchical Sunburst:** A multi-level chart showing skills nested within their official ESCO categories (e.g., *Transversal skills > Digital skills > Programming*).
# *   **Occupation Match (Bar/List):** Shows the **Top 5 Occupations** the user is best suited for based on their current skill set, including a "Completeness" score (e.g., "80% match for Software Developer").
# *   **Top-Level Radar Chart:** A standardized profile showing the balance of skills across the 4 top-level ESCO pillars (Knowledge, Skills, Attitudes/Values, Language).

# ### 3. Technical Architecture Plan

# #### Backend (`Backend/visualization/`)
# You requested a dedicated module for processing this data to keep the logic clean.
# *   **New Folder:** `Backend/visualization/`
# *   **New File:** `Backend/visualization/processor.py`
#     *   *Function:* `process_custom_skills(skills: List[CustomSkillModel]) -> Dict`
#         *   Aggregates counts for the Donut Chart.
#         *   Bins confidence scores for the Density Chart.
#     *   *Function:* `process_esco_hierarchy(skills: List[ESCOSkillModel]) -> Dict`
#         *   Calls ESCO API to find parent categories for the Sunburst/Radar charts.
#     *   *Function:* `match_occupations(skills: List[ESCOSkillModel]) -> List[Dict]`
#         *   Queries ESCO API to find occupations linked to the user's skills and calculates match percentages for the Top 5.
# *   **New Router:** `Backend/routers/visualization.py`
#     *   Endpoints like `GET /api/visualizations/session/{session_id}/custom` and `GET /api/visualizations/session/{session_id}/esco`.

# #### Frontend
# *   **Library:** Chart.js (via CDN).
# *   **Implementation:** Fetch data from the new visualization endpoints and render the configured charts in `skills.html`.
