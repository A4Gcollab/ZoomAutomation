'use client';

import DashboardLayout from "@/components/dashboard-layout";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Link2, PlusCircle, Trash2 } from "lucide-react";

const linkedChannels = [
  { id: 'UCrxNv_iH_WVtlt3NaA-NZxw', name: 'YTZ Automation Channel', subscribers: '-', status: 'Linked' },
];


export default function YouTubePage() {
  return (
    <DashboardLayout>
      <div className="flex-1 space-y-6 p-4 md:p-8">
        <div className="flex items-center justify-between">
          <h1 className="text-3xl font-bold tracking-tight">
            YouTube Channels
          </h1>
          <Button>
            <PlusCircle className="mr-2" />
            Link New Channel
          </Button>
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
                            <TableHead>Subscribers</TableHead>
                            <TableHead>Status</TableHead>
                            <TableHead className="text-right">Actions</TableHead>
                        </TableRow>
                    </TableHeader>
                    <TableBody>
                        {linkedChannels.map((channel) => (
                            <TableRow key={channel.id}>
                                <TableCell className="font-medium">{channel.name}</TableCell>
                                <TableCell>{channel.subscribers}</TableCell>
                                <TableCell><Badge className="bg-chart-2 text-white">{channel.status}</Badge></TableCell>
                                <TableCell className="text-right">
                                    <Button variant="ghost" size="icon" asChild>
                                        <a href={`https://www.youtube.com/channel/${channel.id}`} target="_blank" rel="noopener noreferrer">
                                            <Link2 className="h-4 w-4" />
                                        </a>
                                    </Button>
                                    <Button variant="ghost" size="icon" className="text-destructive hover:text-destructive">
                                        <Trash2 className="h-4 w-4" />
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
