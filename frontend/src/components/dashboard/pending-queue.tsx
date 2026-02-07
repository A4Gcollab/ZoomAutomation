'use client';

import * as React from 'react';
import { CheckCircle, PlusCircle, Send, Search, Filter, X, CheckSquare, Square, Loader2 } from 'lucide-react';
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
  TableHead,
  TableHeader,
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
import { Input } from '@/components/ui/input';
import { Checkbox } from '@/components/ui/checkbox';
import { Badge } from '@/components/ui/badge';
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
import { Label } from '../ui/label';
import { useToast } from '@/hooks/use-toast';

type RecordingState = {
  recordings: PendingRecording[];
  approved: string[];
  processing: string[];
};

type FilterState = {
  search: string;
  dateFrom: string;
  dateTo: string;
  team: string;
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

function BulkApproveDialog({
  open,
  onOpenChange,
  selectedCount,
  teams,
  playlists,
  onConfirm,
  onAddTeam,
  onAddPlaylist,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  selectedCount: number;
  teams: string[];
  playlists: string[];
  onConfirm: (team: string, playlist: string) => void;
  onAddTeam: (team: string) => void;
  onAddPlaylist: (playlist: string) => void;
}) {
  const [team, setTeam] = React.useState('');
  const [playlist, setPlaylist] = React.useState('');
  const [isAddTeamDialogOpen, setAddTeamDialogOpen] = React.useState(false);
  const [isAddPlaylistDialogOpen, setAddPlaylistDialogOpen] = React.useState(false);

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
      <Dialog open={open} onOpenChange={onOpenChange}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Bulk Approve {selectedCount} Recording{selectedCount > 1 ? 's' : ''}</DialogTitle>
            <DialogDescription>
              All selected recordings will be assigned the same team and playlist.
            </DialogDescription>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="grid grid-cols-4 items-center gap-4">
              <Label className="text-right">Team</Label>
              <div className="col-span-3">
                <Select value={team} onValueChange={handleTeamChange}>
                  <SelectTrigger>
                    <SelectValue placeholder="Select Team" />
                  </SelectTrigger>
                  <SelectContent>
                    {teams.map((t) => (
                      <SelectItem key={t} value={t}>{t}</SelectItem>
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
              </div>
            </div>
            <div className="grid grid-cols-4 items-center gap-4">
              <Label className="text-right">Playlist</Label>
              <div className="col-span-3">
                <Select value={playlist} onValueChange={handlePlaylistChange}>
                  <SelectTrigger>
                    <SelectValue placeholder="Select Playlist" />
                  </SelectTrigger>
                  <SelectContent>
                    {playlists.map((p) => (
                      <SelectItem key={p} value={p}>{p}</SelectItem>
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
              </div>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => onOpenChange(false)}>Cancel</Button>
            <Button
              onClick={() => onConfirm(team, playlist)}
              disabled={!team || !playlist}
            >
              Approve {selectedCount} Recording{selectedCount > 1 ? 's' : ''}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
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


function RecordingRow({
  recording,
  teams,
  playlists,
  onApprove,
  onAddTeam,
  onAddPlaylist,
  isSelected,
  onSelect,
  isProcessing,
}: {
  recording: PendingRecording;
  teams: string[];
  playlists: string[];
  onApprove: (id: string, team: string, playlist: string) => void;
  onAddTeam: (team: string) => void;
  onAddPlaylist: (playlist: string) => void;
  isSelected: boolean;
  onSelect: (id: string, selected: boolean) => void;
  isProcessing: boolean;
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

  const disabled = isApproved || isProcessing;

  return (
    <>
      <TableRow className={cn(isSelected && "bg-muted/50")}>
        {/* Checkbox for bulk selection */}
        <TableCell className="w-[50px]">
          <Checkbox
            checked={isSelected}
            onCheckedChange={(checked) => onSelect(recording.id, !!checked)}
            disabled={disabled}
          />
        </TableCell>
        <TableCell className="font-medium">
          <div className="flex flex-col">
            <span className="line-clamp-2">{recording.topic}</span>
            {/* Mobile: Show date and duration inline */}
            <div className="flex gap-2 mt-1 md:hidden">
              <Badge variant="outline" className="text-xs">
                {new Date(recording.date).toLocaleDateString()}
              </Badge>
              {recording.duration && (
                <Badge variant="secondary" className="text-xs">
                  {recording.duration}
                </Badge>
              )}
            </div>
          </div>
        </TableCell>
        <TableCell className="hidden md:table-cell">
          {new Date(recording.date).toLocaleDateString()}
        </TableCell>
        <TableCell className="hidden lg:table-cell">{recording.duration}</TableCell>
        <TableCell>
          <Select value={team} onValueChange={handleTeamChange} disabled={disabled}>
            <SelectTrigger className="w-full md:w-[150px]">
              <SelectValue placeholder="Team" />
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
                  <span>New team...</span>
                </div>
              </SelectItem>
            </SelectContent>
          </Select>
        </TableCell>
        <TableCell>
          <Select value={playlist} onValueChange={handlePlaylistChange} disabled={disabled}>
            <SelectTrigger className="w-full md:w-[150px]">
              <SelectValue placeholder="Playlist" />
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
                  <span>New playlist...</span>
                </div>
              </SelectItem>
            </SelectContent>
          </Select>
        </TableCell>
        <TableCell className="text-right">
          <Button
            onClick={handleApprove}
            disabled={disabled || !team || !playlist}
            size="sm"
            className={cn(
              "w-full md:w-auto",
              isApproved && 'bg-green-600 hover:bg-green-600/90 text-white'
            )}
          >
            {isProcessing ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                <span className="hidden sm:inline">Processing</span>
              </>
            ) : isApproved ? (
              <>
                <CheckCircle className="mr-2 h-4 w-4" />
                <span className="hidden sm:inline">Approved</span>
              </>
            ) : (
              <>
                <Send className="mr-2 h-4 w-4" />
                <span className="hidden sm:inline">Approve</span>
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
    processing: [],
  });
  const [teams, setTeams] = React.useState<string[]>([]);
  const [playlists, setPlaylists] = React.useState<string[]>([]);
  const [loading, setLoading] = React.useState(true);
  const [selectedIds, setSelectedIds] = React.useState<Set<string>>(new Set());
  const [showBulkDialog, setShowBulkDialog] = React.useState(false);
  const [showFilters, setShowFilters] = React.useState(false);
  const [filters, setFilters] = React.useState<FilterState>({
    search: '',
    dateFrom: '',
    dateTo: '',
    team: '',
  });
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

        setState(prev => ({ ...prev, recordings: mappedQueue }));
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

  // Filter recordings
  const filteredRecordings = React.useMemo(() => {
    return state.recordings.filter((rec) => {
      // Search filter
      if (filters.search) {
        const searchLower = filters.search.toLowerCase();
        if (!rec.topic?.toLowerCase().includes(searchLower)) {
          return false;
        }
      }

      // Date from filter
      if (filters.dateFrom) {
        const recDate = new Date(rec.date);
        const fromDate = new Date(filters.dateFrom);
        if (recDate < fromDate) return false;
      }

      // Date to filter
      if (filters.dateTo) {
        const recDate = new Date(rec.date);
        const toDate = new Date(filters.dateTo);
        toDate.setHours(23, 59, 59); // End of day
        if (recDate > toDate) return false;
      }

      // Team filter (if recording already has a team assigned)
      if (filters.team && rec.team && rec.team !== filters.team) {
        return false;
      }

      return true;
    });
  }, [state.recordings, filters]);

  const handleApprove = async (id: string, team: string, playlist: string) => {
    setState(prev => ({ ...prev, processing: [...prev.processing, id] }));

    try {
      // Call backend API to approve
      await api.approveRecording(id, team, playlist);

      setState((prevState) => ({
        ...prevState,
        approved: [...prevState.approved, id],
        processing: prevState.processing.filter(pid => pid !== id),
      }));

      const recording = state.recordings.find((r) => r.id === id);
      toast({
        title: 'Recording Approved',
        description: `"${recording?.topic}" is being processed.`,
      });

      // Remove from list and selection after a delay
      setTimeout(() => {
        setState((prevState) => ({
          ...prevState,
          recordings: prevState.recordings.filter((r) => r.id !== id),
        }));
        setSelectedIds(prev => {
          const next = new Set(prev);
          next.delete(id);
          return next;
        });
      }, 2000);
    } catch (error: any) {
      setState(prev => ({ ...prev, processing: prev.processing.filter(pid => pid !== id) }));
      toast({
        variant: "destructive",
        title: 'Approval Failed',
        description: error.message || 'Failed to approve recording',
      });
    }
  };

  const handleBulkApprove = async (team: string, playlist: string) => {
    if (!team || !playlist) {
      toast({
        variant: "destructive",
        title: 'Bulk Approval Failed',
        description: 'Please select a team and playlist.',
      });
      return;
    }

    setShowBulkDialog(false);
    const ids = Array.from(selectedIds);

    // Add all to processing
    setState(prev => ({ ...prev, processing: [...prev.processing, ...ids] }));

    let successCount = 0;
    let failCount = 0;

    for (const id of ids) {
      try {
        await api.approveRecording(id, team, playlist);
        setState(prev => ({
          ...prev,
          approved: [...prev.approved, id],
          processing: prev.processing.filter(pid => pid !== id),
        }));
        successCount++;
      } catch (error) {
        console.error(`Failed to approve ${id}:`, error);
        setState(prev => ({ ...prev, processing: prev.processing.filter(pid => pid !== id) }));
        failCount++;
      }
    }

    // Remove approved recordings after delay
    setTimeout(() => {
      setState(prev => ({
        ...prev,
        recordings: prev.recordings.filter(r => !ids.includes(r.id) || !prev.approved.includes(r.id)),
      }));
      setSelectedIds(new Set());
    }, 2000);

    if (successCount > 0) {
      toast({
        title: 'Bulk Approval Complete',
        description: `${successCount} recording${successCount > 1 ? 's' : ''} approved${failCount > 0 ? `, ${failCount} failed` : ''}.`,
      });
    } else {
      toast({
        variant: "destructive",
        title: 'Bulk Approval Failed',
        description: `All ${failCount} recording${failCount > 1 ? 's' : ''} failed to approve.`,
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

  const toggleSelectAll = () => {
    if (selectedIds.size === filteredRecordings.length) {
      setSelectedIds(new Set());
    } else {
      setSelectedIds(new Set(filteredRecordings.map(r => r.id)));
    }
  };

  const handleSelect = (id: string, selected: boolean) => {
    setSelectedIds(prev => {
      const next = new Set(prev);
      if (selected) {
        next.add(id);
      } else {
        next.delete(id);
      }
      return next;
    });
  };

  const clearFilters = () => {
    setFilters({ search: '', dateFrom: '', dateTo: '', team: '' });
  };

  const hasActiveFilters = filters.search || filters.dateFrom || filters.dateTo || filters.team;

  return (
    <Card>
      <CardHeader>
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <CardTitle>Pending Queue</CardTitle>
            <CardDescription>
              {filteredRecordings.length} recording{filteredRecordings.length !== 1 ? 's' : ''} waiting for approval
              {hasActiveFilters && ` (filtered from ${state.recordings.length})`}
            </CardDescription>
          </div>
          <div className="flex items-center gap-2">
            {selectedIds.size > 0 && (
              <Button onClick={() => setShowBulkDialog(true)} size="sm">
                <CheckSquare className="mr-2 h-4 w-4" />
                Approve {selectedIds.size} Selected
              </Button>
            )}
            <Button
              variant="outline"
              size="sm"
              onClick={() => setShowFilters(!showFilters)}
              className={cn(hasActiveFilters && "border-primary")}
            >
              <Filter className="mr-2 h-4 w-4" />
              Filter
              {hasActiveFilters && <Badge variant="secondary" className="ml-2">{
                [filters.search, filters.dateFrom, filters.dateTo, filters.team].filter(Boolean).length
              }</Badge>}
            </Button>
          </div>
        </div>

        {/* Search and Filters */}
        <div className="space-y-3 pt-4">
          {/* Always visible search bar */}
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Search by title..."
              value={filters.search}
              onChange={(e) => setFilters(prev => ({ ...prev, search: e.target.value }))}
              className="pl-10"
            />
            {filters.search && (
              <Button
                variant="ghost"
                size="sm"
                className="absolute right-1 top-1/2 -translate-y-1/2 h-7 w-7 p-0"
                onClick={() => setFilters(prev => ({ ...prev, search: '' }))}
              >
                <X className="h-4 w-4" />
              </Button>
            )}
          </div>

          {/* Collapsible filters */}
          {showFilters && (
            <div className="flex flex-col sm:flex-row gap-3 p-4 bg-muted/50 rounded-lg">
              <div className="flex-1 space-y-1">
                <Label className="text-xs text-muted-foreground">From Date</Label>
                <Input
                  type="date"
                  value={filters.dateFrom}
                  onChange={(e) => setFilters(prev => ({ ...prev, dateFrom: e.target.value }))}
                  className="h-9"
                />
              </div>
              <div className="flex-1 space-y-1">
                <Label className="text-xs text-muted-foreground">To Date</Label>
                <Input
                  type="date"
                  value={filters.dateTo}
                  onChange={(e) => setFilters(prev => ({ ...prev, dateTo: e.target.value }))}
                  className="h-9"
                />
              </div>
              <div className="flex-1 space-y-1">
                <Label className="text-xs text-muted-foreground">Team</Label>
                <Select
                  value={filters.team}
                  onValueChange={(val) => setFilters(prev => ({ ...prev, team: val === 'all' ? '' : val }))}
                >
                  <SelectTrigger className="h-9">
                    <SelectValue placeholder="All Teams" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Teams</SelectItem>
                    {teams.map((t) => (
                      <SelectItem key={t} value={t}>{t}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              {hasActiveFilters && (
                <div className="flex items-end">
                  <Button variant="ghost" size="sm" onClick={clearFilters} className="h-9">
                    <X className="mr-2 h-4 w-4" />
                    Clear
                  </Button>
                </div>
              )}
            </div>
          )}
        </div>
      </CardHeader>
      <CardContent>
        <div className="rounded-md border overflow-x-auto">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="w-[50px]">
                  <Checkbox
                    checked={filteredRecordings.length > 0 && selectedIds.size === filteredRecordings.length}
                    onCheckedChange={toggleSelectAll}
                    disabled={filteredRecordings.length === 0}
                  />
                </TableHead>
                <TableHead>Title</TableHead>
                <TableHead className="hidden md:table-cell">Date</TableHead>
                <TableHead className="hidden lg:table-cell">Duration</TableHead>
                <TableHead>Team</TableHead>
                <TableHead>Playlist</TableHead>
                <TableHead className="text-right">Action</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {loading ? (
                <TableRow>
                  <TableCell colSpan={7} className="h-24 text-center">
                    <div className="flex items-center justify-center gap-2">
                      <Loader2 className="h-5 w-5 animate-spin" />
                      <span>Loading recordings...</span>
                    </div>
                  </TableCell>
                </TableRow>
              ) : filteredRecordings.length > 0 ? (
                filteredRecordings.map((recording) => (
                  <RecordingRow
                    key={recording.id}
                    recording={recording}
                    teams={teams}
                    playlists={playlists}
                    onApprove={handleApprove}
                    onAddTeam={handleAddTeam}
                    onAddPlaylist={handleAddPlaylist}
                    isSelected={selectedIds.has(recording.id)}
                    onSelect={handleSelect}
                    isProcessing={state.processing.includes(recording.id)}
                  />
                ))
              ) : (
                <TableRow>
                  <TableCell colSpan={7} className="h-24 text-center">
                    {hasActiveFilters ? (
                      <div className="flex flex-col items-center gap-2">
                        <span>No recordings match your filters.</span>
                        <Button variant="link" onClick={clearFilters}>Clear filters</Button>
                      </div>
                    ) : (
                      "No pending recordings. Great job!"
                    )}
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </div>
      </CardContent>

      <BulkApproveDialog
        open={showBulkDialog}
        onOpenChange={setShowBulkDialog}
        selectedCount={selectedIds.size}
        teams={teams}
        playlists={playlists}
        onConfirm={handleBulkApprove}
        onAddTeam={handleAddTeam}
        onAddPlaylist={handleAddPlaylist}
      />
    </Card>
  );
}
