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
import {
  pendingRecordings as initialData,
  teams as initialTeams,
  playlists as initialPlaylists,
  type PendingRecording,
} from '@/lib/mock-data';
import { cn } from '@/lib/utils';
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
    recordings: initialData,
    approved: [],
  });
  const [teams, setTeams] = React.useState(initialTeams);
  const [playlists, setPlaylists] = React.useState(initialPlaylists);
  const { toast } = useToast();

  const handleApprove = (id: string, team: string, playlist: string) => {
    setState((prevState) => ({
      ...prevState,
      approved: [...prevState.approved, id],
    }));

    // In a real app, this would trigger a server action.
    // For now, we'll just show a toast and remove it from the list after a delay.
    toast({
      title: 'Recording Approved',
      description: `"${initialData.find((r) => r.id === id)?.topic}" is being processed.`,
    });

    setTimeout(() => {
      setState((prevState) => ({
        ...prevState,
        recordings: prevState.recordings.filter((r) => r.id !== id),
      }));
    }, 2000);
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
