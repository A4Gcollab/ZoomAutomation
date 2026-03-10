
class SheetSchemaV2:
    # Tab Names
    TAB_MAIN = "Main"
    TAB_DASHBOARD = "Dashboard"
    TAB_LOGS = "System Logs"
    TAB_SETTINGS = "Settings"

    # Main Sheet Columns
    COL_DATE = "Date"
    COL_MEETING_ID = "Meeting ID"
    COL_TITLE = "Title"
    COL_TEAM = "Team"
    COL_PLAYLIST = "Playlist"
    COL_STATUS = "Status"
    COL_APPROVED_BY = "Approved By"
    COL_YOUTUBE_URL = "YouTube URL"
    COL_DRIVE_URL = "Drive Folder"
    
    HEADERS_MAIN = [
        COL_DATE, COL_MEETING_ID, COL_TITLE, COL_TEAM, 
        COL_PLAYLIST, COL_STATUS, COL_APPROVED_BY, 
        COL_YOUTUBE_URL, COL_DRIVE_URL
    ]

    # Settings Keys (Column A)
    KEY_COMMAND = "COMMAND"
    KEY_LAST_RUN = "LAST_RUN"
    
    # Command Values
    CMD_IDLE = "IDLE"
    CMD_START = "START"
    CMD_REFRESH = "REFRESH"
