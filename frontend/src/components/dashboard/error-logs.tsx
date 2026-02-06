"use client";

import * as React from "react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { FileSpreadsheet, RefreshCw, AlertCircle, Info, AlertTriangle } from "lucide-react";
import { api } from "@/lib/api";
import { cn } from "@/lib/utils";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

type LogEntry = {
  timestamp: string;
  level: string;
  logger?: string;
  message: string;
};

export function ErrorLogs() {
  const [logs, setLogs] = React.useState<LogEntry[]>([]);
  const [loading, setLoading] = React.useState(false);
  const [sheetUrl, setSheetUrl] = React.useState<string | null>(null);
  const [levelFilter, setLevelFilter] = React.useState<string>("all");

  const fetchLogs = React.useCallback(async () => {
    const token = localStorage.getItem('auth_token');
    if (!token) return;

    setLoading(true);
    try {
      const response = await api.getLogs(100);
      setLogs(response.logs || []);
    } catch (error) {
      console.error('Failed to fetch logs:', error);
    } finally {
      setLoading(false);
    }
  }, []);

  // Fetch sheet URL on mount
  React.useEffect(() => {
    const fetchSheetUrl = async () => {
      const token = localStorage.getItem('auth_token');
      if (!token) return;

      try {
        const response = await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000'}/sheets-url`, {
          headers: { 'X-Token': token }
        });
        if (response.ok) {
          const data = await response.json();
          setSheetUrl(data.url);
        }
      } catch (error) {
        console.error('Failed to fetch sheet URL:', error);
      }
    };

    fetchSheetUrl();
    fetchLogs();
  }, [fetchLogs]);

  const filteredLogs = React.useMemo(() => {
    if (levelFilter === "all") return logs;
    return logs.filter(log => log.level === levelFilter);
  }, [logs, levelFilter]);

  const getLevelIcon = (level: string) => {
    switch (level) {
      case 'ERROR':
        return <AlertCircle className="h-4 w-4 text-destructive" />;
      case 'WARNING':
        return <AlertTriangle className="h-4 w-4 text-yellow-500" />;
      default:
        return <Info className="h-4 w-4 text-blue-500" />;
    }
  };

  const getLevelBadge = (level: string) => {
    switch (level) {
      case 'ERROR':
        return <Badge variant="destructive">{level}</Badge>;
      case 'WARNING':
        return <Badge className="bg-yellow-500 text-white">{level}</Badge>;
      default:
        return <Badge variant="secondary">{level}</Badge>;
    }
  };

  return (
    <Card>
      <CardHeader>
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div>
            <CardTitle>System Logs</CardTitle>
            <CardDescription>
              View recent system events and errors. Full logs are also available in Google Sheets.
            </CardDescription>
          </div>
          <div className="flex items-center gap-2">
            <Select value={levelFilter} onValueChange={setLevelFilter}>
              <SelectTrigger className="w-[130px]">
                <SelectValue placeholder="Filter level" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Levels</SelectItem>
                <SelectItem value="INFO">Info</SelectItem>
                <SelectItem value="WARNING">Warning</SelectItem>
                <SelectItem value="ERROR">Error</SelectItem>
              </SelectContent>
            </Select>
            <Button variant="outline" size="sm" onClick={fetchLogs} disabled={loading}>
              <RefreshCw className={cn("h-4 w-4", loading && "animate-spin")} />
            </Button>
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {sheetUrl && (
          <a
            href={sheetUrl}
            target="_blank"
            rel="noopener noreferrer"
          >
            <Button variant="outline" className="w-full md:w-auto">
              <FileSpreadsheet className="mr-2 h-4 w-4" />
              View Full Logs in Google Sheets
            </Button>
          </a>
        )}

        <div className="rounded-md border max-h-[400px] overflow-y-auto">
          {filteredLogs.length > 0 ? (
            <div className="divide-y">
              {filteredLogs.map((log, idx) => (
                <div key={idx} className="p-3 text-sm hover:bg-muted/50">
                  <div className="flex items-start gap-3">
                    {getLevelIcon(log.level)}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        {getLevelBadge(log.level)}
                        {log.logger && (
                          <span className="text-xs text-muted-foreground">[{log.logger}]</span>
                        )}
                        {log.timestamp && (
                          <span className="text-xs text-muted-foreground ml-auto">
                            {log.timestamp}
                          </span>
                        )}
                      </div>
                      <p className="text-sm break-words">{log.message}</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="p-8 text-center text-muted-foreground">
              {loading ? "Loading logs..." : "No logs found."}
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
