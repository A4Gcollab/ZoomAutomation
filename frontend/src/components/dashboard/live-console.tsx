"use client";

import * as React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Terminal,
  Minimize2,
  Maximize2,
  X,
  RefreshCw,
  Pause,
  Play,
  ChevronDown,
  ChevronUp
} from "lucide-react";
import { api } from "@/lib/api";
import { cn } from "@/lib/utils";

type LogEntry = {
  timestamp: string;
  level: string;
  logger?: string;
  message: string;
};

export function LiveConsole() {
  const [logs, setLogs] = React.useState<LogEntry[]>([]);
  const [isMinimized, setIsMinimized] = React.useState(false);
  const [isVisible, setIsVisible] = React.useState(true);
  const [isPaused, setIsPaused] = React.useState(false);
  const [autoScroll, setAutoScroll] = React.useState(true);
  const [serviceStatus, setServiceStatus] = React.useState<'running' | 'stopped' | 'unknown'>('unknown');
  const consoleRef = React.useRef<HTMLDivElement>(null);
  const intervalRef = React.useRef<NodeJS.Timeout | null>(null);

  const fetchLogs = React.useCallback(async () => {
    if (isPaused) return;

    const token = localStorage.getItem('auth_token');
    if (!token) return;

    try {
      const response = await api.getLogs(50);
      setLogs(response.logs || []);

      // Auto-scroll to bottom
      if (autoScroll && consoleRef.current) {
        setTimeout(() => {
          if (consoleRef.current) {
            consoleRef.current.scrollTop = consoleRef.current.scrollHeight;
          }
        }, 50);
      }
    } catch (error) {
      console.error('Failed to fetch logs:', error);
    }
  }, [isPaused, autoScroll]);

  const fetchServiceStatus = React.useCallback(async () => {
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000'}/service/status`);
      if (response.ok) {
        const data = await response.json();
        setServiceStatus(data.running ? 'running' : 'stopped');
      }
    } catch (error) {
      setServiceStatus('unknown');
    }
  }, []);

  React.useEffect(() => {
    fetchLogs();
    fetchServiceStatus();

    // Poll every 3 seconds for live updates
    intervalRef.current = setInterval(() => {
      fetchLogs();
      fetchServiceStatus();
    }, 3000);

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [fetchLogs, fetchServiceStatus]);

  const getLogColor = (level: string, logger?: string) => {
    // Color based on log content
    if (level === 'ERROR') return 'text-red-400';
    if (level === 'WARNING') return 'text-yellow-400';
    if (logger === 'BackgroundService') return 'text-green-400';
    if (logger === 'ZoomClient-Zoom Account 1' || logger === 'ZoomClient-Zoom Account 2') return 'text-blue-400';
    if (logger === 'YouTubeClient') return 'text-red-300';
    if (logger === 'DriveClient') return 'text-yellow-300';
    if (logger === 'SheetManager') return 'text-purple-400';
    return 'text-gray-300';
  };

  const formatLogLine = (log: LogEntry, index: number) => {
    const time = log.timestamp ? log.timestamp.split(' ')[1]?.split(',')[0] || '' : '';
    const logger = log.logger ? `[${log.logger}]` : '';

    // Highlight special messages
    const message = log.message;
    let icon = '';

    if (message.includes('Service Cycle #')) icon = '📊';
    else if (message.includes('Phase 1')) icon = '🔍';
    else if (message.includes('Phase 2')) icon = '⚙️';
    else if (message.includes('Phase 3')) icon = '🗑️';
    else if (message.includes('Sleeping')) icon = '😴';
    else if (message.includes('✅')) icon = '';
    else if (message.includes('❌')) icon = '';
    else if (message.includes('⚠️')) icon = '';

    return (
      <div
        key={index}
        className={cn(
          "font-mono text-xs leading-relaxed hover:bg-gray-800/50 px-2 py-0.5",
          getLogColor(log.level, log.logger)
        )}
      >
        <span className="text-gray-500">{time}</span>
        {' '}
        <span className="text-gray-400">{logger}</span>
        {' '}
        {icon && <span>{icon} </span>}
        <span>{message}</span>
      </div>
    );
  };

  if (!isVisible) {
    return (
      <Button
        onClick={() => setIsVisible(true)}
        className="fixed bottom-4 right-4 z-50 shadow-lg"
        size="sm"
      >
        <Terminal className="h-4 w-4 mr-2" />
        Show Console
      </Button>
    );
  }

  return (
    <Card className={cn(
      "fixed bottom-4 right-4 z-50 shadow-2xl border-gray-700 bg-gray-900 text-white transition-all duration-300",
      isMinimized ? "w-80 h-12" : "w-[600px] h-[400px]"
    )}>
      <CardHeader className="p-2 border-b border-gray-700 flex flex-row items-center justify-between space-y-0">
        <div className="flex items-center gap-2">
          <Terminal className="h-4 w-4 text-green-400" />
          <CardTitle className="text-sm font-medium">Live Service Console</CardTitle>
          <Badge
            variant="outline"
            className={cn(
              "text-xs",
              serviceStatus === 'running' ? "border-green-500 text-green-400" :
              serviceStatus === 'stopped' ? "border-red-500 text-red-400" :
              "border-gray-500 text-gray-400"
            )}
          >
            {serviceStatus === 'running' ? '● Running' :
             serviceStatus === 'stopped' ? '○ Stopped' :
             '? Unknown'}
          </Badge>
        </div>
        <div className="flex items-center gap-1">
          <Button
            variant="ghost"
            size="icon"
            className="h-6 w-6 text-gray-400 hover:text-white hover:bg-gray-700"
            onClick={() => setIsPaused(!isPaused)}
            title={isPaused ? "Resume" : "Pause"}
          >
            {isPaused ? <Play className="h-3 w-3" /> : <Pause className="h-3 w-3" />}
          </Button>
          <Button
            variant="ghost"
            size="icon"
            className="h-6 w-6 text-gray-400 hover:text-white hover:bg-gray-700"
            onClick={fetchLogs}
            title="Refresh"
          >
            <RefreshCw className="h-3 w-3" />
          </Button>
          <Button
            variant="ghost"
            size="icon"
            className="h-6 w-6 text-gray-400 hover:text-white hover:bg-gray-700"
            onClick={() => setIsMinimized(!isMinimized)}
            title={isMinimized ? "Expand" : "Minimize"}
          >
            {isMinimized ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />}
          </Button>
          <Button
            variant="ghost"
            size="icon"
            className="h-6 w-6 text-gray-400 hover:text-red-400 hover:bg-gray-700"
            onClick={() => setIsVisible(false)}
            title="Close"
          >
            <X className="h-3 w-3" />
          </Button>
        </div>
      </CardHeader>

      {!isMinimized && (
        <CardContent className="p-0 h-[calc(100%-48px)] overflow-hidden">
          <div
            ref={consoleRef}
            className="h-full overflow-y-auto bg-gray-950 p-2 scrollbar-thin scrollbar-thumb-gray-700 scrollbar-track-transparent"
          >
            {logs.length > 0 ? (
              logs.map((log, idx) => formatLogLine(log, idx))
            ) : (
              <div className="text-gray-500 text-xs text-center py-4">
                {isPaused ? "Console paused..." : "Waiting for logs..."}
              </div>
            )}
          </div>

          {/* Status bar */}
          <div className="absolute bottom-0 left-0 right-0 h-6 bg-gray-800 border-t border-gray-700 flex items-center justify-between px-2 text-xs text-gray-400">
            <div className="flex items-center gap-2">
              <span>{logs.length} lines</span>
              {isPaused && <Badge variant="outline" className="text-xs py-0 text-yellow-400 border-yellow-400">PAUSED</Badge>}
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={() => setAutoScroll(!autoScroll)}
                className={cn(
                  "text-xs hover:text-white",
                  autoScroll ? "text-green-400" : "text-gray-500"
                )}
              >
                Auto-scroll: {autoScroll ? 'ON' : 'OFF'}
              </button>
            </div>
          </div>
        </CardContent>
      )}
    </Card>
  );
}
