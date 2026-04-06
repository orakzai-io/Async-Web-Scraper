# Frontend - Web Scraper Dashboard

A modern, responsive dashboard interface for initiating, monitoring, and downloading data from your asynchronous web scraping jobs.
## Project Structure & Key Components

The frontend is a lightweight, high-performance application built using **Vite** and **TypeScript**, focused on real-time feedback and clear data visualization.

### Root Files

- **`index.html`**: The single-page application entry point. 
    - Contains the core layout structure: URL input field, progress tracking area, and the action buttons for starting jobs and downloading results.
- **`package.json`**: Project configuration.
    - Manages scripts for development (`npm run dev`) and production builds (`npm run build`).
    - Lists only the essential dependencies (**Vite**, **TypeScript**) for a fast, browser-native experience.

### Source Files (`src/`)

- **`main.ts`**: The core dashboard orchestrator.
    - Manages all **UI state** (pending/processing/completed/failed).
    - Implements the **Asynchronous Polling Loop** to keep the interface updated with real-time progress from the backend.
    - Handles dynamic DOM manipulation and event listeners for URL submission and result downloads.
- **`api.ts`**: The communication layer.
    - A dedicated API client that handles all `fetch` requests to the FastAPI backend.
    - Directs traffic for `/scrape`, `/results`, and `/download` endpoints.
- **`css/style.css`**: The design system.
    - Defines a **fully responsive, premium aesthetic** using Vanilla CSS.
    - Manages the visual feedback for various job states (animations, status colors, and layout transitions).
- **`vite-env.d.ts`**: TypeScript environment definitions for Vite-specific features and environment variables.
---
[Return to Root Project README](../README.md)
