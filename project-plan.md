Excellent. Here is the updated project plan for Net-Pulse, incorporating the psutil-based architecture.

### Project Plan: Net-Pulse

---

### **Milestone 1: Backend Core - The Data Collector**

**Goal:** Create a functional, Python-native data collector that can autonomously track and store network traffic using psutil.

* **1.1: Project Scaffolding:**
    * Initialize a standard Python project structure (`pyproject.toml`, `src/`).
    * Add initial dependencies: `psutil`, `apscheduler`.

* **1.2: psutil Network Module:**
    * Create a robust network monitoring module using `psutil.net_io_counters(pernic=True)`.
    * Implement interface discovery using `psutil.net_if_addrs()`.
    * Handle per-interface traffic statistics collection.

* **1.3: Database Schema:**
    * Implement a module to initialize the SQLite database (`netpulse.db`) with two tables:
        * `traffic_data` (timestamp, interface_name, rx_bytes, tx_bytes, rx_packets, tx_packets)
        * `configuration` (key, value) for storing monitored interfaces.

* **1.4: Core Polling Engine:**
    * Implement the main collection logic:
        * Use psutil to collect traffic statistics at regular intervals.
        * Calculate traffic deltas between polling cycles.
        * Handle counter resets automatically (psutil handles this internally).
        * Write the calculated deltas to the `traffic_data` table.

* **1.5: Auto-Detection Logic:**
    * Using psutil, implement the startup logic to discover available network interfaces.
    * Identify the primary interface by finding interfaces with active traffic.
    * On first launch, if the `configuration` table is empty, populate it with discovered interfaces.

* **✅ Outcome:** A Python script that, when executed, automatically discovers network interfaces using psutil and begins logging traffic data into a `netpulse.db` file. The backend is now verifiable at a data level.

---

### **Milestone 2: API Layer - Exposing the Data**

**Goal:** Build a complete API server to expose data and configuration endpoints.

* **2.1: API Scaffolding:**
    * Integrate FastAPI into the project.
    * Combine the psutil-based collector logic from M1 to run as a background task using `apscheduler` when the FastAPI app starts.

* **2.2: Informational Endpoints:**
    * `GET /api/health`: A simple endpoint for health checks.
    * `GET /api/interfaces`: Returns a JSON list of all available network interfaces discovered by psutil.

* **2.3: Configuration Endpoints:**
    * `GET /api/config/monitored_interfaces`: Reads and returns the list of interfaces from the `configuration` table.
    * `POST /api/config/monitored_interfaces`: Accepts a JSON array of interface names and updates the database.

* **2.4: Core Data Endpoint:**
    * Implement `GET /api/traffic` with required query parameters (`time_window_hours`, `group_minutes`). This will contain the SQL logic to filter by time and aggregate the results.

* **✅ Outcome:** A fully functional FastAPI server. All backend logic is now complete and can be tested via `curl` or any API client, validating the entire data pipeline.

---

### **Milestone 3: Frontend - Visualization Dashboard**

**Goal:** Create the primary user-facing dashboard for viewing network traffic.

* **3.1: Frontend Scaffolding:**
    * Initialize a Svelte project inside a `frontend/` subdirectory.
    * Install `chart.js`.

* **3.2: UI Layout:**
    * Build the main dashboard page layout with a placeholder for the chart and the two control sliders ("Time Window" and "Grouping").

* **3.3: API Integration & Charting:**
    * Implement the JavaScript logic to call the `/api/traffic` endpoint.
    * Render the response data onto a Chart.js line chart with distinct series for RX and TX traffic.
    * Hook the sliders up to trigger new API calls and redraw the chart on value changes.

* **✅ Outcome:** A functional web interface where a user can view the traffic graph for the default interface and dynamically adjust the time window and data granularity.

---

### **Milestone 4: Frontend - Configuration UI**

**Goal:** Empower the user to configure the application directly from the web interface.

* **4.1: Settings UI Component:**
    * Create a "Settings" page or modal.
    * On load, this component will fetch data from both `/api/interfaces` and `/api/config/monitored_interfaces`.

* **4.2: Interactive Selection:**
    * Display the full list of interfaces discovered by psutil with checkboxes, ensuring the currently monitored ones are pre-selected.
    * Implement a "Save" button that sends the new selection to the `POST /api/config/monitored_interfaces` endpoint.

* **4.3: Dashboard Enhancement:**
    * Update the main dashboard to gracefully handle multiple monitored interfaces (e.g., add a dropdown to switch the view between interfaces).

* **✅ Outcome:** A fully interactive web app. Users can now both view traffic and configure which interfaces to monitor without any manual intervention.

---

### **Milestone 5: Packaging & Finalization**

**Goal:** Package the entire application for simple, one-command deployment.

* **5.1: Dockerization:**
    * Write a multi-stage `Dockerfile` that first builds the Svelte frontend and then builds the Python application, copying the compiled assets to be served by FastAPI.

* **5.2: Compose for Deployment:**
    * Create a `docker-compose.yml` that defines the Net-Pulse service, maps the port, and mounts a volume for `netpulse.db` to ensure data persistence across container restarts.

* **5.3: Documentation:**
    * Create a `README.md` with clear, concise instructions on configuration (overriding defaults via environment variables) and deployment (`docker-compose up -d`).

* **✅ Outcome:** A complete, portable, and well-documented application ready for deployment in any home lab environment.