# Net-Pulse: UI Implementation Plan

This document breaks down the frontend development into 5 iterative milestones. Each milestone results in a verifiable, testable state.

## Milestone 1: The Static Shell & Layout

- **Goal:** Create the complete, responsive HTML and CSS structure of the application with a modern theme, but with no live data.
- **Tasks:**
    1. Choose and integrate a modern Bootstrap 5 theme.
    2. Create the main `index.html` file.
    3. Build the static layout including the Navbar, Content Area, a placeholder for the chart, and the structure for the Information Pane and Settings Modal.
    4. Ensure the static layout is responsive on desktop and mobile screen sizes.
- **Verification:** At the end of this milestone, we can open the `index.html` file in a browser and see the full application layout. Everything will be visually in place, but non-interactive.

## Milestone 2: The Live Chart

- **Goal:** Bring the main dashboard chart to life with real, auto-refreshing data from the backend.
- **Tasks:**
    1. Integrate Chart.js into the project.
    2. Write the JavaScript to call the `GET /api/traffic/history` endpoint.
    3. Render the data onto the Chart.js canvas.
    4. Implement the 30-second auto-refresh loop for the chart.
    5. Implement the initial loading spinner and the subtle background refresh indicator.
- **Verification:** The dashboard will now display a line chart of network traffic that updates automatically every 30 seconds.

## Milestone 3: Core User Interactivity

- **Goal:** Implement the most critical, interactive controls for the user.
- **Tasks:**
    1. Implement the "Start", "Stop", and "Collect Now" buttons and connect them to their respective API endpoints.
    2. Implement the "Time Window" and "Grouping" controls and make them update the chart view.
    3. Implement the "Live Speed" indicator and its 3-second refresh loop.
- **Verification:** The user can now control the data collector, manipulate the chart's view, and see the live network speed.

## Milestone 4: Application Configuration

- **Goal:** Build the settings modal to allow the user to configure the application's behavior.
- **Tasks:**
    1. Implement the Bootstrap Modal for the settings.
    2. Build the interface selection form, fetching and submitting data to the API.
    3. Build the input for the backend `collection-interval`.
    4. Build the inputs for the UI refresh rates, saving and loading the values from `localStorage`.
- **Verification:** The user can open the settings, change which interfaces are monitored, and customize all the timing intervals.

## Milestone 5: Detailed Information & Finalization

- **Goal:** Complete the dashboard by implementing the detailed information views and adding the final features.
- **Tasks:**
    1. Implement the three tabs in the Information Pane ("System", "Collector", "Interfaces"), including the on-click details for each interface.
    2. Implement the "Export Data" button.
    3. Conduct a final round of testing and UI polishing.
    4. Implement graceful error handling with toast notifications.
- **Verification:** All UI elements are fully functional, all 20 API endpoints are utilized, and the application is complete and robust.