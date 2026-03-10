'use client';

import * as React from 'react';
import { CheckCircle, PlusCircle, Send } from 'lucide-react';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import {
  Table,
  TableBody,
  TableCell,
  TableRow,
} from '@/components/ui/table';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectSeparator,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Button } from '@/components/ui/button';
import { type PendingRecording } from '@/lib/mock-data';
import { cn } from '@/lib/utils';
import { api } from '@/lib/api';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Input } from '../ui/input';
import { Label } from '../ui/label';
import { useToast } from '@/hooks/use-toast';

type RecordingState = {
  recordings: PendingRecording[];
  approved: string[];
};

function AddNewItemDialog({
  open,
  onOpenChange,
  onAddItem,
  itemName,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onAddItem: (item: string) => void;
  itemName: 'Team' | 'Playlist';
}) {
  const [newItem, setNewItem] = React.useState('');

  const handleAdd = () => {
    if (newItem.trim()) {
      onAddItem(newItem.trim());
      setNewItem('');
      onOpenChange(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Create New {itemName}</DialogTitle>
          <DialogDescription>
            Add a new {itemName.toLowerCase()} to the list of available options.
          </DialogDescription>
        </DialogHeader>
        <div className="grid gap-4 py-4">
          <div className="grid grid-cols-4 items-center gap-4">
            <Label htmlFor="item-name" className="text-right">
              Name
            </Label>
            <Input
              id="item-name"
              value={newItem}
              onChange={(e) => setNewItem(e.target.value)}
              className="col-span-3"
              placeholder={`e.g., Awesome ${itemName}`}
              onKeyDown={(e) => {
                if (e.key === 'Enter') {
                  e.preventDefault();
                  handleAdd();
                }
              }}
            />
          </div>
        </div>
        <DialogFooter>
          <Button type="submit" onClick={handleAdd}>Save {itemName}</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}


function RecordingRow({
  recording,
  teams,
  playlists,
  onApprove,
  onAddTeam,
  onAddPlaylist,
}: {
  recording: PendingRecording;
  teams: string[];
  playlists: string[];
  onApprove: (id: string, team: string, playlist: string) => void;
  onAddTeam: (team: string) => void;
  onAddPlaylist: (playlist: string) => void;
}) {
  const [team, setTeam] = React.useState(recording.team || '');
  const [playlist, setPlaylist] = React.useState(recording.playlist || '');
  const [isApproved, setIsApproved] = React.useState(false);
  const [isAddTeamDialogOpen, setAddTeamDialogOpen] = React.useState(false);
  const [isAddPlaylistDialogOpen, setAddPlaylistDialogOpen] = React.useState(false);

  const { toast } = useToast();

  const handleApprove = () => {
    if (!team || !playlist) {
      toast({
        title: 'Approval Failed',
        description: 'Please select a team and a playlist.',
        variant: 'destructive',
      });
      return;
    }
    setIsApproved(true);
    onApprove(recording.id, team, playlist);
  };

  const handleTeamChange = (value: string) => {
    if (value === 'add_new_team') {
      setAddTeamDialogOpen(true);
    } else {
      setTeam(value);
    }
  };

  const handlePlaylistChange = (value: string) => {
    if (value === 'add_new_playlist') {
      setAddPlaylistDialogOpen(true);
    } else {
      setPlaylist(value);
    }
  };

  return (
    <>
      <TableRow>
        <TableCell className="font-medium">{recording.topic}</TableCell>
        <TableCell className="hidden md:table-cell">{new Date(recording.date).toLocaleDateString()}</TableCell>
        <TableCell className="hidden lg:table-cell">{recording.duration}</TableCell>
        <TableCell>
          <Select value={team} onValueChange={handleTeamChange} disabled={isApproved}>
            <SelectTrigger className="w-full md:w-[180px]">
              <SelectValue placeholder="Select Team" />
            </SelectTrigger>
            <SelectContent>
              {teams.map((t) => (
                <SelectItem key={t} value={t}>
                  {t}
                </SelectItem>
              ))}
              <SelectSeparator />
              <SelectItem value="add_new_team">
                <div className="flex items-center gap-2">
                  <PlusCircle className="h-4 w-4" />
                  <span>Create new team...</span>
                </div>
              </SelectItem>
            </SelectContent>
          </Select>
        </TableCell>
        <TableCell>
          <Select value={playlist} onValueChange={handlePlaylistChange} disabled={isApproved}>
            <SelectTrigger className="w-full md:w-[200px]">
              <SelectValue placeholder="Select Playlist" />
            </SelectTrigger>
            <SelectContent>
              {playlists.map((p) => (
                <SelectItem key={p} value={p}>
                  {p}
                </SelectItem>
              ))}
              <SelectSeparator />
              <SelectItem value="add_new_playlist">
                <div className="flex items-center gap-2">
                  <PlusCircle className="h-4 w-4" />
                  <span>Create new playlist...</span>
                </div>
              </SelectItem>
            </SelectContent>
          </Select>
        </TableCell>
        <TableCell className="text-right">
          <Button
            onClick={handleApprove}
            disabled={isApproved || !team || !playlist}
            className={cn(isApproved && 'bg-chart-2 hover:bg-chart-2/90 text-white')}
          >
            {isApproved ? (
              <>
                <CheckCircle className="mr-2 h-4 w-4" />
                Approved
              </>
            ) : (
              <>
                <Send className="mr-2 h-4 w-4" />
                Approve
              </>
            )}
          </Button>
        </TableCell>
      </TableRow>
      <AddNewItemDialog
        itemName="Team"
        open={isAddTeamDialogOpen}
        onOpenChange={setAddTeamDialogOpen}
        onAddItem={(newTeam) => {
          onAddTeam(newTeam);
          setTeam(newTeam);
        }}
      />
      <AddNewItemDialog
        itemName="Playlist"
        open={isAddPlaylistDialogOpen}
        onOpenChange={setAddPlaylistDialogOpen}
        onAddItem={(newPlaylist) => {
          onAddPlaylist(newPlaylist);
          setPlaylist(newPlaylist);
        }}
      />
    </>
  );
}

export function PendingQueue() {
  const [state, setState] = React.useState<RecordingState>({
    recordings: [],
    approved: [],
  });
  const [teams, setTeams] = React.useState<string[]>([]);
  const [playlists, setPlaylists] = React.useState<string[]>([]);
  const [loading, setLoading] = React.useState(true);
  const { toast } = useToast();

  // Fetch queue and options from backend
  React.useEffect(() => {
    const fetchData = async () => {
      // Check if we have a token first
      const token = localStorage.getItem('auth_token');
      if (!token) {
        console.log('No auth token found, skipping PendingQueue fetch');
        return;
      }

      try {
        setLoading(true);
        const [queueData, options] = await Promise.all([
          api.getQueue(),
          api.getOptions()
        ]);

        // Map backend zoom_id to frontend id
        const mappedQueue = Array.isArray(queueData) ? queueData.map((item: any) => ({
          ...item,
          id: item.zoom_id || item.id, // Handle backend using zoom_id
          date: item.start_time || item.date_str // Ensure date exists
        })) : [];

        setState({ recordings: mappedQueue, approved: [] });
        setTeams(options.teams || []);
        setPlaylists(options.playlists || []);
      } catch (error) {
        console.error('Failed to fetch queue data:', error);
        // Only show toast if it's not an auth error (redirect handled elsewhere)
        if (!(error instanceof Error) || !error.message.includes('Unauthorized')) {
          toast({
            variant: "destructive",
            title: "Failed to Load",
            description: "Could not fetch pending recordings from server"
          });
        }
      } finally {
        setLoading(false);
      }
    };

    fetchData();
    // Refresh every 30 seconds
    const interval = setInterval(fetchData, 30000);
    return () => clearInterval(interval);
  }, [toast]);

  const handleApprove = async (id: string, team: string, playlist: string) => {
    try {
      // Call backend API to approve
      await api.approveRecording(id, team, playlist);

      setState((prevState) => ({
        ...prevState,
        approved: [...prevState.approved, id],
      }));

      const recording = state.recordings.find((r) => r.id === id);
      toast({
        title: 'Recording Approved',
        description: `"${recording?.topic}" is being processed.`,
      });

      // Remove from list after a delay
      setTimeout(() => {
        setState((prevState) => ({
          ...prevState,
          recordings: prevState.recordings.filter((r) => r.id !== id),
        }));
      }, 2000);
    } catch (error: any) {
      toast({
        variant: "destructive",
        title: 'Approval Failed',
        description: error.message || 'Failed to approve recording',
      });
    }
  };

  const handleAddTeam = (newTeam: string) => {
    if (!teams.includes(newTeam)) {
      setTeams([...teams, newTeam]);
      toast({
        title: 'Team Added',
        description: `"${newTeam}" is now available.`,
      });
    } else {
      toast({
        title: 'Team Already Exists',
        variant: 'destructive',
        description: `A team with the name "${newTeam}" already exists.`,
      });
    }
  };

  const handleAddPlaylist = (newPlaylist: string) => {
    if (!playlists.includes(newPlaylist)) {
      setPlaylists([...playlists, newPlaylist]);
      toast({
        title: 'Playlist Added',
        description: `"${newPlaylist}" is now available.`,
      });
    } else {
      toast({
        title: 'Playlist Already Exists',
        variant: 'destructive',
        description: `A playlist with the name "${newPlaylist}" already exists.`,
      });
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Pending Queue</CardTitle>
        <CardDescription>
          Recordings waiting for approval and assignment.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="rounded-md border">
          <Table>
            <TableBody>
              {state.recordings.length > 0 ? (
                state.recordings.map((recording) => (
                  <RecordingRow
                    key={recording.id}
                    recording={recording}
                    teams={teams}
                    playlists={playlists}
                    onApprove={handleApprove}
                    onAddTeam={handleAddTeam}
                    onAddPlaylist={handleAddPlaylist}
                  />
                ))
              ) : (
                <TableRow>
                  <TableCell colSpan={6} className="h-24 text-center">
                    No pending recordings. Great job!
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </div>
      </CardContent>
    </Card>
  );
}
