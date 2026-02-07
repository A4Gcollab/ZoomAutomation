"use client";

import * as React from "react";
import {
  ChevronDown,
  ChevronUp,
  FolderKanban,
  MoreHorizontal,
  Youtube,
  ExternalLink,
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
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
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
  const rowsPerPage = 5;

  // Fetch history from backend
  React.useEffect(() => {
    let isMounted = true;

    const fetchHistory = async () => {
      const token = localStorage.getItem('auth_token');
      if (!token) return;

      try {
        if (isMounted) setLoading(true);
        const history = await api.getHistory(100);

        if (!isMounted) return;

        const mappedHistory = Array.isArray(history) ? history.map((item: any) => ({
          ...item,
          id: item.zoom_id || item.id,
          processedAt: item.processed_at || item.created_at || item.date_str || new Date().toISOString(),
          approvedBy: item.approved_by || item.approvedBy || 'System',
          youtubeUrl: item.youtube_url || item.youtubeUrl,
          driveUrl: item.drive_url || item.driveUrl,
        })) : [];

        setData(mappedHistory);
      } catch (error) {
        if (!isMounted) return;
        console.error('Failed to fetch history:', error);
      } finally {
        if (isMounted) setLoading(false);
      }
    };

    fetchHistory();
    const interval = setInterval(fetchHistory, 30000);
    return () => {
      isMounted = false;
      clearInterval(interval);
    };
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
    item.topic.toLowerCase().includes(filter.toLowerCase())
  );

  const paginatedData = filteredData.slice(
    (currentPage - 1) * rowsPerPage,
    currentPage * rowsPerPage
  );

  const totalPages = Math.ceil(filteredData.length / rowsPerPage);

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
    return email.split('@')[0];
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <CardTitle>Completed Recordings</CardTitle>
          <Input
            placeholder="Search by topic..."
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            className="max-w-sm"
          />
        </div>
      </CardHeader>
      <CardContent>
        <div className="rounded-md border">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead />
                <TableHead
                  className="cursor-pointer"
                  onClick={() => requestSort("topic")}
                >
                  <div className="flex items-center gap-2">Topic {getSortIcon("topic")}</div>
                </TableHead>
                <TableHead
                  className="cursor-pointer"
                  onClick={() => requestSort("team")}
                >
                  <div className="flex items-center gap-2">Team {getSortIcon("team")}</div>
                </TableHead>
                <TableHead
                  className="cursor-pointer"
                  onClick={() => requestSort("playlist")}
                >
                  <div className="flex items-center gap-2">Playlist {getSortIcon("playlist")}</div>
                </TableHead>
                <TableHead
                  className="cursor-pointer"
                  onClick={() => requestSort("approvedBy")}
                >
                  <div className="flex items-center gap-2">Approved By {getSortIcon("approvedBy")}</div>
                </TableHead>
                <TableHead
                  className="cursor-pointer text-right"
                  onClick={() => requestSort("processedAt")}
                >
                  <div className="flex items-center justify-end gap-2">Processed {getSortIcon("processedAt")}</div>
                </TableHead>
                <TableHead className="text-center">YouTube</TableHead>
                <TableHead className="text-center">Drive</TableHead>
                <TableHead>
                  <span className="sr-only">Actions</span>
                </TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {paginatedData.length > 0 ? (
                paginatedData.map((recording) => (
                  <React.Fragment key={recording.id}>
                    <TableRow>
                      <TableCell>
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => toggleRow(recording.id)}
                        >
                          {expandedRow === recording.id ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
                        </Button>
                      </TableCell>
                      <TableCell className="font-medium">{recording.topic}</TableCell>
                      <TableCell>{recording.team}</TableCell>
                      <TableCell>{recording.playlist}</TableCell>
                      <TableCell>{getApproverName(recording.approvedBy)}</TableCell>
                      <TableCell className="text-right">
                        {new Date(recording.processedAt).toLocaleDateString()}
                      </TableCell>
                      <TableCell className="text-center">
                        {recording.youtubeId || recording.youtubeUrl ? (
                          <a
                            href={recording.youtubeUrl || `https://www.youtube.com/watch?v=${recording.youtubeId}`}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="inline-flex items-center gap-1 text-red-600 hover:text-red-700 hover:underline"
                          >
                            <Youtube className="h-4 w-4" />
                            <ExternalLink className="h-3 w-3" />
                          </a>
                        ) : (
                          <span className="text-muted-foreground text-xs">-</span>
                        )}
                      </TableCell>
                      <TableCell className="text-center">
                        {recording.driveVideoId || recording.driveUrl ? (
                          <a
                            href={recording.driveUrl || `https://drive.google.com/drive/folders/${recording.driveVideoId}`}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="inline-flex items-center gap-1 text-blue-600 hover:text-blue-700 hover:underline"
                          >
                            <FolderKanban className="h-4 w-4" />
                            <ExternalLink className="h-3 w-3" />
                          </a>
                        ) : (
                          <span className="text-muted-foreground text-xs">-</span>
                        )}
                      </TableCell>
                      <TableCell className="text-right">
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <Button variant="ghost" className="h-8 w-8 p-0">
                              <span className="sr-only">Open menu</span>
                              <MoreHorizontal className="h-4 w-4" />
                            </Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align="end">
                            <DropdownMenuItem asChild>
                              <a href={recording.youtubeUrl} target="_blank" rel="noopener noreferrer">
                                <Youtube className="mr-2 h-4 w-4" /> View on YouTube
                              </a>
                            </DropdownMenuItem>
                            <DropdownMenuItem asChild>
                              <a href={recording.driveUrl} target="_blank" rel="noopener noreferrer">
                                <FolderKanban className="mr-2 h-4 w-4" /> View on Drive
                              </a>
                            </DropdownMenuItem>
                          </DropdownMenuContent>
                        </DropdownMenu>
                      </TableCell>
                    </TableRow>
                    {expandedRow === recording.id && (
                      <TableRow>
                        <TableCell colSpan={9}>
                          <div className="p-4 bg-muted rounded-md">
                            <h4 className="font-semibold mb-2">Recording Details</h4>
                            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
                              <div><span className="font-medium text-muted-foreground">Recording ID:</span> {recording.id}</div>
                              <div><span className="font-medium text-muted-foreground">Duration:</span> {recording.duration}</div>
                              <div><span className="font-medium text-muted-foreground">Processed:</span> {new Date(recording.processedAt).toLocaleString()}</div>
                              <div className="col-span-1 md:col-span-3">
                                <Badge className={cn("text-white", recording.status === "Completed" ? "bg-chart-2" : "bg-primary")}>
                                  Status: {recording.status}
                                </Badge>
                              </div>
                            </div>
                          </div>
                        </TableCell>
                      </TableRow>
                    )}
                  </React.Fragment>
                ))
              ) : (
                <TableRow>
                  <TableCell colSpan={9} className="h-24 text-center">
                    {loading ? "Loading..." : "No results found."}
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </div>
        <div className="flex items-center justify-end space-x-2 py-4">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setCurrentPage((prev) => Math.max(prev - 1, 1))}
            disabled={currentPage === 1}
          >
            Previous
          </Button>
          <span className="text-sm text-muted-foreground">
            Page {currentPage} of {totalPages}
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
      </CardContent>
    </Card>
  );
}
