"use client";

import * as React from "react";
import { PlayCircle, RefreshCw, StopCircle, Wifi, WifiOff } from "lucide-react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import { api } from "@/lib/api";
import { useToast } from "@/hooks/use-toast";

type ServiceStatus = "running" | "stopped" | "restarting";
type ConnectionStatus = "connected" | "disconnected";

export function ServiceControl() {
  const [serviceStatus, setServiceStatus] = React.useState<ServiceStatus>("stopped");
  const [connectionStatus, setConnectionStatus] = React.useState<ConnectionStatus>("disconnected");
  const [loading, setLoading] = React.useState(false);
  const { toast } = useToast();

  // Fetch service status on mount and periodically
  React.useEffect(() => {
    const fetchStatus = async () => {
      // Check for token first
      const token = localStorage.getItem('auth_token');
      if (!token) return;

      try {
        const status = await api.getServiceStatus();
        setServiceStatus(status.running ? "running" : "stopped");
        setConnectionStatus("connected");
      } catch (error) {
        console.error('Failed to fetch service status:', error);
        setConnectionStatus("disconnected");
      }
    };

    fetchStatus();
    const interval = setInterval(fetchStatus, 10000); // Poll every 10 seconds
    return () => clearInterval(interval);
  }, []);

  const handleAction = async (action: "start" | "stop" | "restart") => {
    setLoading(true);
    try {
      let result;
      switch (action) {
        case "start":
          result = await api.startService();
          setServiceStatus("running");
          toast({ title: "Service Started", description: result.message });
          break;
        case "stop":
          result = await api.stopService();
          setServiceStatus("stopped");
          toast({ title: "Service Stopped", description: result.message });
          break;
        case "restart":
          setServiceStatus("restarting");
          result = await api.restartService();
          toast({ title: "Service Restarting", description: result.message });
          setTimeout(() => setServiceStatus("running"), 3000);
          break;
      }
    } catch (error: any) {
      toast({
        variant: "destructive",
        title: "Action Failed",
        description: error.message || "Failed to perform service action"
      });
      // Refresh status after error
      try {
        const status = await api.getServiceStatus();
        setServiceStatus(status.running ? "running" : "stopped");
      } catch { }
    } finally {
      setLoading(false);
    }
  };

  const getStatusBadge = () => {
    switch (serviceStatus) {
      case "running":
        return <Badge className="bg-chart-2 text-white shadow">Running</Badge>;
      case "stopped":
        return <Badge variant="destructive" className="shadow">Stopped</Badge>;
      case "restarting":
        return <Badge className="bg-chart-3 text-white shadow">Restarting</Badge>;
    }
  };

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <div>
          <CardTitle className="text-sm font-medium">Service Control</CardTitle>
          <CardDescription>Manage the background automation service.</CardDescription>
        </div>
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          {connectionStatus === 'connected' ? (
            <>
              <Wifi className="h-4 w-4 text-chart-2" />
              <span>Connected</span>
            </>
          ) : (
            <>
              <WifiOff className="h-4 w-4 text-destructive" />
              <span>Disconnected</span>
            </>
          )}
        </div>
      </CardHeader>
      <CardContent>
        <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <span className="text-sm font-medium">Status:</span>
            {getStatusBadge()}
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => handleAction("start")}
              disabled={loading || serviceStatus === "running" || serviceStatus === "restarting"}
            >
              <PlayCircle className="mr-2 h-4 w-4" /> Start
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => handleAction("stop")}
              disabled={loading || serviceStatus === "stopped" || serviceStatus === "restarting"}
            >
              <StopCircle className="mr-2 h-4 w-4" /> Stop
            </Button>
            <Button
              size="sm"
              onClick={() => handleAction("restart")}
              disabled={loading || serviceStatus === "restarting"}
            >
              <RefreshCw className={cn("mr-2 h-4 w-4", (serviceStatus === "restarting" || loading) && "animate-spin")} /> Restart
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
