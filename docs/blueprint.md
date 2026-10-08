# **App Name**: Zoom Automation Dashboard

## Core Features:

- Google OAuth Integration: Secure user authentication via Google OAuth 2.0 with Firebase Authentication, including automatic redirection and token management.
- Real-time Dashboard Updates: Utilize WebSockets for live updates on service status, queue changes, and processing events. Includes connection status indicators and auto-reconnect functionality.
- Service Control Panel: Control background service with start, stop, and restart buttons (admin only).  Reflects real-time status updates via WebSocket.
- Pending Recordings Queue: Manage and approve pending Zoom recordings with team and playlist assignments.  Implements dropdowns for team/playlist selection, validation, and saving new options.
- Completed Recordings History: View the history of processed recordings with links to YouTube and Google Drive. Includes pagination, filtering, search, sorting, and expandable row details.
- Error Logging and Monitoring: Monitor system logs and dedicated error logs for troubleshooting. Includes real-time log streaming, filtering, and error details.
- User Identity Tracking: Tracks exactly WHO performs an action and persist it to the database. Store User Avatar and Name in top navigation bar. Display the Approve User's email or name.
- Playlist Mapping: Allow users to map specific Zoom accounts or meeting topics to predefined YouTube playlists. This mapping will be stored and used to automatically suggest playlists during the approval process. The AI tool will use these mappings to determine the most appropriate playlist for a new recording based on the Zoom account or meeting topic. If no mapping is found, the tool will suggest the most frequently used playlist or a default playlist.

## Style Guidelines:

- Primary color: Indigo (#4F46E5) for a modern, professional feel.
- Background color: Light gray (#F9FAFB) for a zen light theme.
- Accent color: Emerald (#10B981) for success and positive feedback.
- Font: 'Inter' (sans-serif) for a clean and readable dashboard experience. Note: currently only Google Fonts are supported.
- Use a clean, minimal interface with generous whitespace and rounded corners.
- Apply smooth transitions (200-300ms) for a fluid user experience.
- Color-coded status badges to provide immediate visual feedback.