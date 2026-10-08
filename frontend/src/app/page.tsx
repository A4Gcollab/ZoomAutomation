'use client';

import { useUser } from "@/firebase/auth/use-user";
import { useRouter } from "next/navigation";
import { useEffect } from "react";
import DashboardLayout from "@/components/dashboard-layout";
import { CompletedHistory } from "@/components/dashboard/completed-history";
import { ErrorLogs } from "@/components/dashboard/error-logs";
import { PendingQueue } from "@/components/dashboard/pending-queue";
import { ServiceControl } from "@/components/dashboard/service-control";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

export default function Home() {
  const { user, loading } = useUser();
  const router = useRouter();

  useEffect(() => {
    // Only redirect to login if we're done loading AND there's no user
    // This prevents redirect loops when coming back from Google OAuth
    if (!loading && !user) {
      // Small delay to ensure Firebase auth state has fully initialized
      const timer = setTimeout(() => {
        router.push('/login');
      }, 100);
      return () => clearTimeout(timer);
    }
  }, [user, loading, router]);

  // Show loading spinner while checking auth state
  if (loading) {
    return (
      <div className="flex h-screen w-full items-center justify-center">
        <div className="animate-spin rounded-full h-32 w-32 border-t-2 border-b-2 border-primary"></div>
      </div>
    );
  }

  // If not loading but no user, show loading while redirect happens
  if (!user) {
    return (
      <div className="flex h-screen w-full items-center justify-center">
        <div className="animate-spin rounded-full h-32 w-32 border-t-2 border-b-2 border-primary"></div>
      </div>
    );
  }

  return (
    <DashboardLayout>
      <div className="flex-1 space-y-6 p-4 md:p-8">
        <div className="flex items-center justify-between space-y-2">
          <h1 className="text-3xl font-bold tracking-tight">
            Dashboard
          </h1>
        </div>

        <ServiceControl />

        <Tabs defaultValue="pending" className="space-y-4">
          <TabsList>
            <TabsTrigger value="pending">Pending Queue</TabsTrigger>
            <TabsTrigger value="completed">Completed History</TabsTrigger>
            <TabsTrigger value="logs">System Logs</TabsTrigger>
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
    </DashboardLayout>
  );
}
