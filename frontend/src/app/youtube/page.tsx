'use client';

import DashboardLayout from "@/components/dashboard-layout";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Link2, ExternalLink } from "lucide-react";

const linkedChannels = [
  {
    id: 'UCrxNv_iH_WVtlt3NaA-NZxw',
    name: 'Zoom Automation',
    url: 'https://youtube.com',
    studioUrl: 'https://studio.youtube.com/channel/UCrxNv_iH_WVtlt3NaA-NZxw/videos/upload?filter=%5B%5D&sort=%7B%22columnType%22%3A%22date%22%2C%22sortOrder%22%3A%22DESCENDING%22%7D',
    status: 'Active',
  },
];


export default function YouTubePage() {
  return (
    <DashboardLayout>
      <div className="flex-1 space-y-6 p-4 md:p-8">
        <div className="flex items-center justify-between">
          <h1 className="text-3xl font-bold tracking-tight">
            YouTube Channels
          </h1>
        </div>
        <p className="text-muted-foreground">Manage your YouTube channel integrations here.</p>

        <Card>
          <CardHeader>
            <CardTitle>Linked Channels</CardTitle>
            <CardDescription>
              These channels are connected to the automation service.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Channel</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {linkedChannels.map((channel) => (
                  <TableRow key={channel.id}>
                    <TableCell className="font-medium">{channel.name}</TableCell>
                    <TableCell><Badge className="bg-chart-2 text-white">{channel.status}</Badge></TableCell>
                    <TableCell className="text-right space-x-2">
                      <Button variant="ghost" size="icon" asChild>
                        <a href={channel.url} target="_blank" rel="noopener noreferrer" title="View Channel">
                          <Link2 className="h-4 w-4" />
                        </a>
                      </Button>
                      <Button variant="ghost" size="icon" asChild>
                        <a href={channel.studioUrl} target="_blank" rel="noopener noreferrer" title="YouTube Studio">
                          <ExternalLink className="h-4 w-4" />
                        </a>
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>

      </div>
    </DashboardLayout>
  );
}
