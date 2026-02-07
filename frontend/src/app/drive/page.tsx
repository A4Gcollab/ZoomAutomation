'use client';

import DashboardLayout from "@/components/dashboard-layout";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Folder, ExternalLink } from "lucide-react";

const linkedFolders = [
    {
        id: '1qalNa2vYt5JXnw7XOy8GeTGZnveP0-s5',
        name: 'Video Recordings',
        url: 'https://drive.google.com/open?id=1qalNa2vYt5JXnw7XOy8GeTGZnveP0-s5',
        status: 'Active',
    },
    {
        id: '16B8FVZ28pUH77ehka-0iuyLgDeEaQZN4',
        name: 'Transcripts',
        url: 'https://drive.google.com/open?id=16B8FVZ28pUH77ehka-0iuyLgDeEaQZN4',
        status: 'Active',
    },
];

export default function DrivePage() {
  return (
    <DashboardLayout>
      <div className="flex-1 space-y-6 p-4 md:p-8">
        <div className="flex items-center justify-between">
            <h1 className="text-3xl font-bold tracking-tight">
            Google Drive Folders
            </h1>
        </div>
        <p className="text-muted-foreground">Manage your Google Drive folder integrations here.</p>

        <Card>
            <CardHeader>
                <CardTitle>Linked Folders</CardTitle>
                <CardDescription>
                    These folders are used for storing raw recordings and transcripts.
                </CardDescription>
            </CardHeader>
            <CardContent>
                <Table>
                    <TableHeader>
                        <TableRow>
                            <TableHead>Folder Name</TableHead>
                            <TableHead>Status</TableHead>
                            <TableHead className="text-right">Actions</TableHead>
                        </TableRow>
                    </TableHeader>
                    <TableBody>
                        {linkedFolders.map((folder) => (
                            <TableRow key={folder.id}>
                                <TableCell className="font-medium flex items-center gap-2">
                                    <Folder className="h-4 w-4 text-muted-foreground" />
                                    {folder.name}
                                </TableCell>
                                <TableCell><Badge className="bg-chart-2 text-white">{folder.status}</Badge></TableCell>
                                <TableCell className="text-right">
                                    <Button variant="ghost" size="icon" asChild>
                                        <a href={folder.url} target="_blank" rel="noopener noreferrer" title="Open in Drive">
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
