'use client';

import { useUser } from "@/firebase/auth/use-user";
import { useRouter } from "next/navigation";
import { useEffect } from "react";
import DashboardLayout from "@/components/dashboard-layout";
import { CompletedHistory } from "@/components/dashboard/completed-history";
import { ErrorLogs } from "@/components/dashboard/error-logs";
import { PendingQueue } from "@/components/dashboard/pending-queue";
import { ServiceControl } from "@/components/dashboard/service-control";
import { LiveConsole } from "@/components/dashboard/live-console";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

export default function Home() {
  const { user, loading } = useUser();
  const router = useRouter();

  useEffect(() => {
    if (!loading && !user) {
      router.replace('/login');
    }
  }, [loading, user, router]);

  // Show loading while auth is initializing
  if (loading) {
    return (
      <div className="flex h-screen w-full items-center justify-center flex-col gap-4 bg-background">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary"></div>
        <p className="text-muted-foreground text-sm">Loading...</p>
      </div>
    );
  }

  // Not authenticated - show loading while redirect happens
  if (!user) {
    return (
      <div className="flex h-screen w-full items-center justify-center flex-col gap-4 bg-background">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary"></div>
      </div>
    );
  }

  // Authenticated - show dashboard
  return (
    <DashboardLayout>
      <div className="flex-1 space-y-4 sm:space-y-6 p-3 sm:p-4 md:p-8">
        <div className="flex items-center justify-between">
          <h1 className="text-2xl sm:text-3xl font-bold tracking-tight">
            Dashboard
          </h1>
        </div>

        <ServiceControl />

        <Tabs defaultValue="pending" className="space-y-4">
          <TabsList className="w-full sm:w-auto grid grid-cols-3 sm:inline-flex">
            <TabsTrigger value="pending" className="text-xs sm:text-sm">
              <span className="hidden sm:inline">Pending Queue</span>
              <span className="sm:hidden">Pending</span>
            </TabsTrigger>
            <TabsTrigger value="completed" className="text-xs sm:text-sm">
              <span className="hidden sm:inline">Completed History</span>
              <span className="sm:hidden">History</span>
            </TabsTrigger>
            <TabsTrigger value="logs" className="text-xs sm:text-sm">
              <span className="hidden sm:inline">System Logs</span>
              <span className="sm:hidden">Logs</span>
            </TabsTrigger>
          </TabsList>
          <TabsContent value="pending" className="space-y-4">
            <PendingQueue />
          </TabsContent>
          <TabsContent value="completed" className="space-y-4">
            <CompletedHistory />
          </TabsContent>
          <TabsContent value="logs" className="space-y-4">
            <ErrorLogs />
          </TabsContent>
        </Tabs>
      </div>

      {/* Floating Live Console */}
      <LiveConsole />
    </DashboardLayout>
  );
}
