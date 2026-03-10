'use client';

import React, { useState } from 'react';
import DashboardLayout from "@/components/dashboard-layout";
import { useUser } from '@/firebase/auth/use-user';
import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { useToast } from '@/hooks/use-toast';
import { Loader2 } from 'lucide-react';

export default function SettingsPage() {
    const { user } = useUser();
    const { toast } = useToast();
    const [displayName, setDisplayName] = useState(user?.displayName || '');
    const [isSaving, setIsSaving] = useState(false);

    const handleSave = () => {
        setIsSaving(true);
        // Simulate an API call
        setTimeout(() => {
            // In a real app, you would update the user object from the `useUser` hook.
            // For this demo, we'll just show a success message.
            toast({
                title: 'Profile Updated',
                description: 'Your changes have been saved successfully.',
            });
            setIsSaving(false);
        }, 1500);
    };

    if (!user) {
        return (
            <DashboardLayout>
                <div className="flex h-full w-full items-center justify-center">
                    <Loader2 className="animate-spin h-12 w-12 text-primary" />
                </div>
            </DashboardLayout>
        )
    }

  return (
    <DashboardLayout>
      <div className="flex-1 space-y-6 p-4 md:p-8">
        <h1 className="text-3xl font-bold tracking-tight">
          Settings
        </h1>
        
        <Card>
            <CardHeader>
                <CardTitle>Profile</CardTitle>
                <CardDescription>
                    This is how others will see you on the site.
                </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
                <div className="space-y-2">
                    <Label htmlFor="email">Email</Label>
                    <Input id="email" value={user.email || ''} disabled />
                </div>
                <div className="space-y-2">
                    <Label htmlFor="displayName">Display Name</Label>
                    <Input 
                        id="displayName" 
                        value={displayName} 
                        onChange={(e) => setDisplayName(e.target.value)}
                    />
                </div>
                <div className="space-y-2">
                    <Label>Profile Picture</Label>
                    <div className="flex items-center gap-4">
                        <Avatar className="h-20 w-20">
                            <AvatarImage src={user.photoURL || ''} />
                            <AvatarFallback>
                                {user.displayName ? user.displayName.charAt(0).toUpperCase() : user.email?.charAt(0).toUpperCase()}
                            </AvatarFallback>
                        </Avatar>
                        <Button variant="outline">Change Picture</Button>
                    </div>
                </div>
            </CardContent>
            <CardFooter>
                <Button onClick={handleSave} disabled={isSaving}>
                    {isSaving && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                    Save Changes
                </Button>
            </CardFooter>
        </Card>

      </div>
    </DashboardLayout>
  );
}
