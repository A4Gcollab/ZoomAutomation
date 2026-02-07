"use client";

import * as React from "react";
import {
  ChevronDown,
  ChevronUp,
  FolderKanban,
  MoreHorizontal,
  Youtube,
  ExternalLink,
  Loader2,
  Search,
  Clock,
  CheckCircle2,
  AlertCircle,
} from "lucide-react";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { cn } from "@/lib/utils";
import { api } from "@/lib/api";

type CompletedRecording = {
  id: string;
  topic: string;
  team: string;
  playlist: string;
  approvedBy: string;
  processedAt: string;
  status: string;
  duration?: string;
  youtubeUrl?: string;
  driveUrl?: string;
  youtubeId?: string;
  driveVideoId?: string;
  driveTranscriptId?: string;
};

type SortConfig = {
  key: keyof CompletedRecording | null;
  direction: "ascending" | "descending";
};

function getStatusInfo(status: string) {
  const s = status?.toUpperCase() || 'UNKNOWN';
  switch (s) {
    case 'COMPLETED':
      return { color: 'bg-green-500', icon: CheckCircle2, label: 'Completed', progress: 100 };
    case 'PROCESSING':
      return { color: 'bg-blue-500', icon: Loader2, label: 'Processing', progress: 60, animate: true };
    case 'APPROVED':
      return { color: 'bg-yellow-500', icon: Clock, label: 'Queued', progress: 20 };
    case 'ERROR':
      return { color: 'bg-red-500', icon: AlertCircle, label: 'Error', progress: 0 };
    default:
      return { color: 'bg-gray-500', icon: Clock, label: status, progress: 0 };
  }
}

export function CompletedHistory() {
  const [data, setData] = React.useState<CompletedRecording[]>([]);
  const [loading, setLoading] = React.useState(true);
  const [filter, setFilter] = React.useState("");
  const [sortConfig, setSortConfig] = React.useState<SortConfig>({
    key: "processedAt",
    direction: "descending",
  });
  const [currentPage, setCurrentPage] = React.useState(1);
  const [expandedRow, setExpandedRow] = React.useState<string | null>(null);
  const rowsPerPage = 10;

  // Fetch history from backend
  React.useEffect(() => {
    const fetchHistory = async () => {
      // Check for token first
      const token = localStorage.getItem('auth_token');
      if (!token) return;

      try {
        setLoading(true);
        const history = await api.getHistory(100);

        // Map backend fields to frontend expected format
        const mappedHistory = Array.isArray(history) ? history.map((item: any) => ({
          ...item,
          id: item.zoom_id || item.id, // Handle backend using zoom_id
          processedAt: item.processed_at || item.created_at || item.date_str || new Date().toISOString(),
          approvedBy: item.approved_by || item.approvedBy || 'System',
          youtubeUrl: item.youtube_url || item.youtubeUrl,
          driveUrl: item.drive_url || item.driveUrl
        })) : [];

        setData(mappedHistory);
      } catch (error) {
        console.error('Failed to fetch history:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchHistory();
    // Refresh every 15 seconds for real-time progress updates
    const interval = setInterval(fetchHistory, 15000);
    return () => clearInterval(interval);
  }, []);

  const sortedData = React.useMemo(() => {
    let sortableItems = [...data];
    if (sortConfig.key !== null) {
      sortableItems.sort((a, b) => {
        const valA = a[sortConfig.key!] ?? '';
        const valB = b[sortConfig.key!] ?? '';

        if (valA < valB) {
          return sortConfig.direction === "ascending" ? -1 : 1;
        }
        if (valA > valB) {
          return sortConfig.direction === "ascending" ? 1 : -1;
        }
        return 0;
      });
    }
    return sortableItems;
  }, [data, sortConfig]);

  const filteredData = sortedData.filter((item) =>
    item.topic?.toLowerCase().includes(filter.toLowerCase()) ||
    item.team?.toLowerCase().includes(filter.toLowerCase()) ||
    item.playlist?.toLowerCase().includes(filter.toLowerCase())
  );

  const paginatedData = filteredData.slice(
    (currentPage - 1) * rowsPerPage,
    currentPage * rowsPerPage
  );

  const totalPages = Math.max(1, Math.ceil(filteredData.length / rowsPerPage));

  const requestSort = (key: keyof CompletedRecording) => {
    let direction: "ascending" | "descending" = "ascending";
    if (sortConfig.key === key && sortConfig.direction === "ascending") {
      direction = "descending";
    }
    setSortConfig({ key, direction });
  };

  const getSortIcon = (key: keyof CompletedRecording) => {
    if (sortConfig.key !== key) {
      return null;
    }
    return sortConfig.direction === "ascending" ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />;
  };

  const toggleRow = (id: string) => {
    setExpandedRow(expandedRow === id ? null : id);
  };

  const getApproverName = (email: string) => {
    if (!email) return 'System';
    return email.split('@')[0];
  }

  // Stats
  const stats = React.useMemo(() => {
    const completed = data.filter(r => r.status?.toUpperCase() === 'COMPLETED').length;
    const processing = data.filter(r => r.status?.toUpperCase() === 'PROCESSING').length;
    const queued = data.filter(r => r.status?.toUpperCase() === 'APPROVED').length;
    const errors = data.filter(r => r.status?.toUpperCase() === 'ERROR').length;
    return { completed, processing, queued, errors };
  }, [data]);

  return (
    <Card>
      <CardHeader>
        <div className="flex flex-col gap-4">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
            <div>
              <CardTitle>Recording History</CardTitle>
              <CardDescription>
                {filteredData.length} recording{filteredData.length !== 1 ? 's' : ''} in history
              </CardDescription>
            </div>
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search..."
                value={filter}
                onChange={(e) => setFilter(e.target.value)}
                className="pl-10 w-full sm:w-[250px]"
              />
            </div>
          </div>

          {/* Status summary badges */}
          <div className="flex flex-wrap gap-2">
            <Badge variant="outline" className="flex items-center gap-1">
              <CheckCircle2 className="h-3 w-3 text-green-500" />
              {stats.completed} Completed
            </Badge>
            {stats.processing > 0 && (
              <Badge variant="outline" className="flex items-center gap-1">
                <Loader2 className="h-3 w-3 text-blue-500 animate-spin" />
                {stats.processing} Processing
              </Badge>
            )}
            {stats.queued > 0 && (
              <Badge variant="outline" className="flex items-center gap-1">
                <Clock className="h-3 w-3 text-yellow-500" />
                {stats.queued} Queued
              </Badge>
            )}
            {stats.errors > 0 && (
              <Badge variant="destructive" className="flex items-center gap-1">
                <AlertCircle className="h-3 w-3" />
                {stats.errors} Error{stats.errors > 1 ? 's' : ''}
              </Badge>
            )}
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="rounded-md border overflow-x-auto">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="w-[40px]" />
                <TableHead
                  className="cursor-pointer min-w-[200px]"
                  onClick={() => requestSort("topic")}
                >
                  <div className="flex items-center gap-2">Topic {getSortIcon("topic")}</div>
                </TableHead>
                <TableHead
                  className="cursor-pointer hidden md:table-cell"
                  onClick={() => requestSort("team")}
                >
                  <div className="flex items-center gap-2">Team {getSortIcon("team")}</div>
                </TableHead>
                <TableHead
                  className="cursor-pointer hidden lg:table-cell"
                  onClick={() => requestSort("playlist")}
                >
                  <div className="flex items-center gap-2">Playlist {getSortIcon("playlist")}</div>
                </TableHead>
                <TableHead className="w-[120px]">Status</TableHead>
                <TableHead
                  className="cursor-pointer text-right hidden sm:table-cell"
                  onClick={() => requestSort("processedAt")}
                >
                  <div className="flex items-center justify-end gap-2">Date {getSortIcon("processedAt")}</div>
                </TableHead>
                <TableHead className="text-center w-[80px]">Links</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {loading ? (
                <TableRow>
                  <TableCell colSpan={7} className="h-24 text-center">
                    <div className="flex items-center justify-center gap-2">
                      <Loader2 className="h-5 w-5 animate-spin" />
                      <span>Loading history...</span>
                    </div>
                  </TableCell>
                </TableRow>
              ) : paginatedData.length > 0 ? (
                paginatedData.map((recording) => {
                  const statusInfo = getStatusInfo(recording.status);
                  const StatusIcon = statusInfo.icon;

                  return (
                    <React.Fragment key={recording.id}>
                      <TableRow className={cn(
                        statusInfo.animate && "bg-blue-50 dark:bg-blue-950/20"
                      )}>
                        <TableCell>
                          <Button
                            variant="ghost"
                            size="icon"
                            className="h-8 w-8"
                            onClick={() => toggleRow(recording.id)}
                          >
                            {expandedRow === recording.id ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
                          </Button>
                        </TableCell>
                        <TableCell className="font-medium">
                          <div className="flex flex-col">
                            <span className="line-clamp-1">{recording.topic}</span>
                            {/* Mobile: Show team and date inline */}
                            <div className="flex gap-2 mt-1 md:hidden text-xs text-muted-foreground">
                              <span>{recording.team}</span>
                              <span>|</span>
                              <span>{new Date(recording.processedAt).toLocaleDateString()}</span>
                            </div>
                          </div>
                        </TableCell>
                        <TableCell className="hidden md:table-cell">{recording.team}</TableCell>
                        <TableCell className="hidden lg:table-cell">{recording.playlist}</TableCell>
                        <TableCell>
                          <div className="flex flex-col gap-1">
                            <div className="flex items-center gap-2">
                              <StatusIcon className={cn(
                                "h-4 w-4",
                                statusInfo.animate && "animate-spin",
                                recording.status?.toUpperCase() === 'COMPLETED' && "text-green-500",
                                recording.status?.toUpperCase() === 'PROCESSING' && "text-blue-500",
                                recording.status?.toUpperCase() === 'ERROR' && "text-red-500",
                                recording.status?.toUpperCase() === 'APPROVED' && "text-yellow-500"
                              )} />
                              <span className="text-sm">{statusInfo.label}</span>
                            </div>
                            {recording.status?.toUpperCase() === 'PROCESSING' && (
                              <Progress value={statusInfo.progress} className="h-1 w-16" />
                            )}
                          </div>
                        </TableCell>
                        <TableCell className="text-right hidden sm:table-cell">
                          {new Date(recording.processedAt).toLocaleDateString()}
                        </TableCell>
                        <TableCell>
                          <div className="flex items-center justify-center gap-1">
                            {(recording.youtubeId || recording.youtubeUrl) && (
                              <a
                                href={recording.youtubeUrl || `https://www.youtube.com/watch?v=${recording.youtubeId}`}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="p-1.5 rounded hover:bg-muted text-red-600"
                                title="View on YouTube"
                              >
                                <Youtube className="h-4 w-4" />
                              </a>
                            )}
                            {(recording.driveVideoId || recording.driveUrl) && (
                              <a
                                href={recording.driveUrl || `https://drive.google.com/drive/folders/${recording.driveVideoId}`}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="p-1.5 rounded hover:bg-muted text-blue-600"
                                title="View on Drive"
                              >
                                <FolderKanban className="h-4 w-4" />
                              </a>
                            )}
                            {!recording.youtubeUrl && !recording.driveUrl && !recording.youtubeId && !recording.driveVideoId && (
                              <span className="text-muted-foreground text-xs">-</span>
                            )}
                          </div>
                        </TableCell>
                      </TableRow>
                      {expandedRow === recording.id && (
                        <TableRow>
                          <TableCell colSpan={7}>
                            <div className="p-4 bg-muted/50 rounded-md">
                              <h4 className="font-semibold mb-3">Recording Details</h4>
                              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 text-sm">
                                <div>
                                  <span className="font-medium text-muted-foreground block">Recording ID</span>
                                  <span className="font-mono text-xs break-all">{recording.id}</span>
                                </div>
                                <div>
                                  <span className="font-medium text-muted-foreground block">Duration</span>
                                  <span>{recording.duration || 'N/A'}</span>
                                </div>
                                <div>
                                  <span className="font-medium text-muted-foreground block">Approved By</span>
                                  <span>{getApproverName(recording.approvedBy)}</span>
                                </div>
                                <div>
                                  <span className="font-medium text-muted-foreground block">Processed</span>
                                  <span>{new Date(recording.processedAt).toLocaleString()}</span>
                                </div>
                              </div>

                              {/* Links section */}
                              <div className="mt-4 pt-4 border-t flex flex-wrap gap-2">
                                {(recording.youtubeUrl || recording.youtubeId) && (
                                  <Button variant="outline" size="sm" asChild>
                                    <a
                                      href={recording.youtubeUrl || `https://www.youtube.com/watch?v=${recording.youtubeId}`}
                                      target="_blank"
                                      rel="noopener noreferrer"
                                    >
                                      <Youtube className="mr-2 h-4 w-4 text-red-600" />
                                      YouTube
                                      <ExternalLink className="ml-2 h-3 w-3" />
                                    </a>
                                  </Button>
                                )}
                                {(recording.driveUrl || recording.driveVideoId) && (
                                  <Button variant="outline" size="sm" asChild>
                                    <a
                                      href={recording.driveUrl || `https://drive.google.com/drive/folders/${recording.driveVideoId}`}
                                      target="_blank"
                                      rel="noopener noreferrer"
                                    >
                                      <FolderKanban className="mr-2 h-4 w-4 text-blue-600" />
                                      Drive
                                      <ExternalLink className="ml-2 h-3 w-3" />
                                    </a>
                                  </Button>
                                )}
                              </div>
                            </div>
                          </TableCell>
                        </TableRow>
                      )}
                    </React.Fragment>
                  );
                })
              ) : (
                <TableRow>
                  <TableCell colSpan={7} className="h-24 text-center">
                    No recordings found.
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </div>

        {/* Pagination */}
        <div className="flex flex-col sm:flex-row items-center justify-between gap-4 py-4">
          <span className="text-sm text-muted-foreground order-2 sm:order-1">
            Showing {((currentPage - 1) * rowsPerPage) + 1} - {Math.min(currentPage * rowsPerPage, filteredData.length)} of {filteredData.length}
          </span>
          <div className="flex items-center gap-2 order-1 sm:order-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setCurrentPage((prev) => Math.max(prev - 1, 1))}
              disabled={currentPage === 1}
            >
              Previous
            </Button>
            <span className="text-sm text-muted-foreground px-2">
              {currentPage} / {totalPages}
            </span>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setCurrentPage((prev) => Math.min(prev + 1, totalPages))}
              disabled={currentPage === totalPages}
            >
              Next
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
