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
import { FileSpreadsheet } from "lucide-react";

export function ErrorLogs() {
  return (
    <Card>
      <CardHeader>
        <CardTitle>System Logs</CardTitle>
        <CardDescription>
          All system events and errors are logged in a dedicated Google Sheet for
          analysis and auditing.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <a
          href="https://docs.google.com/spreadsheets/"
          target="_blank"
          rel="noopener noreferrer"
        >
          <Button>
            <FileSpreadsheet className="mr-2 h-4 w-4" />
            View Logs in Google Sheets
          </Button>
        </a>
      </CardContent>
    </Card>
  );
}
