export type PendingRecording = {
  id: string;
  topic: string;
  date: string;
  duration: string;
  team: string | null;
  playlist: string | null;
  zoomAccount: string;
};

export type CompletedRecording = {
  id: string;
  topic: string;
  team: string;
  playlist: string;
  processedAt: string;
  duration: string;
  status: "Completed" | "Uploaded";
  approvedBy: string;
  youtubeUrl: string;
  driveUrl: string;
};

export type LogEntry = {
  timestamp: string;
  level: "INFO" | "WARN" | "ERROR";
  message: string;
};

export const teams: string[] = ["Engineering", "Marketing", "Product", "Sales"];

export const playlists: string[] = [
  "Weekly Standups",
  "Product Demos",
  "All-Hands Meetings",
  "Technical Deep Dives",
];

export const pendingRecordings: PendingRecording[] = [
  {
    id: "rec-001",
    topic: "Q2 Engineering Sprint Planning",
    date: "2024-07-20T10:00:00Z",
    duration: "01:03:45",
    team: null,
    playlist: null,
    zoomAccount: "dev-team@example.com",
  },
  {
    id: "rec-002",
    topic: "Weekly Marketing Sync",
    date: "2024-07-19T14:30:00Z",
    duration: "00:45:12",
    team: null,
    playlist: null,
    zoomAccount: "marketing@example.com",
  },
  {
    id: "rec-003",
    topic: "Project Phoenix: Kick-off",
    date: "2024-07-19T09:00:00Z",
    duration: "00:55:30",
    team: null,
    playlist: null,
    zoomAccount: "product@example.com",
  },
];

export const completedRecordings: CompletedRecording[] = [
  {
    id: "rec-comp-001",
    topic: "Q1 All-Hands Meeting",
    team: "Sales",
    playlist: "All-Hands Meetings",
    processedAt: "2024-04-05T12:00:00Z",
    duration: "01:30:00",
    status: "Completed",
    approvedBy: "admin@example.com",
    youtubeUrl: "#",
    driveUrl: "#",
  },
  {
    id: "rec-comp-002",
    topic: "New Feature Demo: AI Insights",
    team: "Product",
    playlist: "Product Demos",
    processedAt: "2024-07-18T16:20:00Z",
    duration: "00:25:40",
    status: "Completed",
    approvedBy: "admin@example.com",
    youtubeUrl: "#",
    driveUrl: "#",
  },
    {
    id: "rec-comp-003",
    topic: "API Authentication Deep Dive",
    team: "Engineering",
    playlist: "Technical Deep Dives",
    processedAt: "2024-07-15T11:00:00Z",
    duration: "01:15:10",
    status: "Completed",
    approvedBy: "admin@example.com",
    youtubeUrl: "#",
    driveUrl: "#",
  },
];

export const errorLogs: LogEntry[] = [
  {
    timestamp: new Date(Date.now() - 2 * 60 * 1000).toISOString(),
    level: "ERROR",
    message: "Failed to upload to YouTube API: Quota Exceeded. Retrying in 10 minutes.",
  },
  {
    timestamp: new Date(Date.now() - 5 * 60 * 1000).toISOString(),
    level: "WARN",
    message: "Google Drive API latency high: 2500ms for file creation.",
  },
  {
    timestamp: new Date(Date.now() - 10 * 60 * 1000).toISOString(),
    level: "INFO",
    message: "Processing job for 'rec-comp-002' completed successfully.",
  },
    {
    timestamp: new Date(Date.now() - 12 * 60 * 1000).toISOString(),
    level: "INFO",
    message: "New recording 'rec-003' detected and added to queue.",
  },
];
