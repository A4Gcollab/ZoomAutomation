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

type ServiceStatus = "running" | "stopped" | "restarting";
type ConnectionStatus = "connected" | "disconnected";

export function ServiceControl() {
  const [serviceStatus, setServiceStatus] = React.useState<ServiceStatus>("running");
  const [connectionStatus, setConnectionStatus] = React.useState<ConnectionStatus>("disconnected");

  React.useEffect(() => {
    const timer = setTimeout(() => setConnectionStatus("connected"), 1500);
    return () => clearTimeout(timer);
  }, []);

  const handleAction = (action: "start" | "stop" | "restart") => {
    switch (action) {
      case "start":
        setServiceStatus("running");
        break;
      case "stop":
        setServiceStatus("stopped");
        break;
      case "restart":
        setServiceStatus("restarting");
        setTimeout(() => setServiceStatus("running"), 3000);
        break;
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
              disabled={serviceStatus === "running" || serviceStatus === "restarting"}
            >
              <PlayCircle className="mr-2 h-4 w-4" /> Start
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => handleAction("stop")}
              disabled={serviceStatus === "stopped" || serviceStatus === "restarting"}
            >
              <StopCircle className="mr-2 h-4 w-4" /> Stop
            </Button>
            <Button
              size="sm"
              onClick={() => handleAction("restart")}
              disabled={serviceStatus === "restarting"}
            >
              <RefreshCw className={cn("mr-2 h-4 w-4", serviceStatus === "restarting" && "animate-spin")} /> Restart
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
