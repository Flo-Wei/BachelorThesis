<!-- 9f357176-eedf-4419-881f-969a3730b403 553c3a7f-b9a8-4bb5-9ebb-9ff85c6963a1 -->
# Skill Visualization Implementation

## Backend Changes

### 1. Update Skill Database Handler

-   **File:** `Backend/classes/Skill_Database_Handler.py`
-   **Goal:** Add methods to support visualization data requirements.
-   **Changes:**
    -   Add `get_skill_details(uri)`: Fetch full skill details including `broader` concepts (parents) and `isEssentialFor`/`isOptionalFor` (occupations).
    -   Add `get_related_occupations(uris)`: Helper to aggregate occupations for a list of skills.

### 2. Create Visualization Processor

-   **New File:** `Backend/visualization/processor.py`
-   **Goal:** Centralize logic for aggregating chart data.
-   **Functions:**
    -   `process_custom_skills(skills)`:
        -   Count occurrences of each `type` (Technical, Soft, etc.) for Donut Chart.
        -   Create bins for `confidence` scores (e.g., 0.0-0.1, ..., 0.9-1.0) for Density/Histogram.
    -   `process_esco_hierarchy(skills)`:
        -   For each skill, use `ESCODatabase` to fetch parent hierarchy.
        -   Build a nested dictionary structure for the Sunburst Chart (e.g., Transversal > Digital > ...).
    -   `match_occupations(skills)`:
        -   Extract related occupations from skill details.
        -   Count frequency of each occupation across the user's skill set.
        -   Return Top 5 occupations with a "match score" (percentage based on coverage or simple frequency).
    -   `process_radar_data(skills)`:
        -   Categorize skills into 4 pillars (Knowledge, Skills, Attitudes, Language) based on ESCO hierarchy or URI patterns.

### 3. Create Visualization Router

-   **New File:** `Backend/routers/visualization.py`
-   **Endpoints:**
    -   `GET /api/visualizations/session/{session_id}/custom`: Returns data for Donut and Density charts.
    -   `GET /api/visualizations/session/{session_id}/esco`: Returns data for Sunburst, Occupation Match, and Radar charts.
    -   Uses `Backend/visualization/processor.py` functions.

### 4. Register Router

-   **File:** `Backend/api.py`
-   **Changes:** Import and include `visualization.router`.

## Frontend Changes

### 5. Update Skills Page

-   **File:** `Frontend/skills.html`
-   **Changes:**
    -   Add Chart.js library via CDN (`<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>`).
    -   Add layout containers for the charts (Donut, Density, Sunburst, Radar, Occupation List).
    -   Include new script `js/skills_viz.js`.

### 6. Create Visualization Script

-   **New File:** `Frontend/js/skills_viz.js`
-   **Goal:** Handle data fetching and chart rendering.
-   **Logic:**
    -   `loadVisualizations(sessionId)`: Fetch data from new API endpoints.
    -   `renderCustomCharts(data)`: Render Donut and Density charts.
    -   `renderEscoCharts(data)`: Render Sunburst, Radar, and Occupation List.
    -   Integrate with existing `skills.html` UI (e.g., trigger load when session is selected).

## Todo List

1.  Modify `Backend/classes/Skill_Database_Handler.py` to add ESCO detail fetching.
2.  Create `Backend/visualization/processor.py`.
3.  Create `Backend/routers/visualization.py`.
4.  Update `Backend/api.py`.
5.  Create `Frontend/js/skills_viz.js`.
6.  Update `Frontend/skills.html` to include charts and scripts.

### To-dos

- [ ] Update Skill_Database_Handler.py with new ESCO methods
- [ ] Create Backend/visualization/processor.py
- [ ] Create Backend/routers/visualization.py
- [ ] Update Backend/api.py to include visualization router
- [ ] Create Frontend/js/skills_viz.js for Chart.js logic
- [ ] Update Frontend/skills.html with chart containers and script refs