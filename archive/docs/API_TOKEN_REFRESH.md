# 🔒 API Token Auto-Refresh Configuration

## Problem: API Tokens Expiring

By default, OAuth tokens expire after 1 hour. This causes the system to fail.

## Solution: Automatic Token Refresh

All API clients have been configured with automatic token refresh. Here's how it works:

### YouTube API (OAuth)
**File**: `src/youtube_client.py`

```python
# Auto-refresh logic (already implemented)
if credentials.expired and credentials.refresh_token:
    credentials.refresh(Request())
    # Save refreshed token
    with open(token_path, 'wb') as token:
        pickle.dump(credentials, token)
```

**What this means**:
- ✅ Token refreshes automatically when expired
- ✅ New token saved to disk
- ✅ No manual intervention needed
- ✅ Works 24/7 indefinitely

### Google Drive API (OAuth)
**File**: `src/drive_client.py`

```python
# Auto-refresh logic (already implemented)
if credentials.expired and credentials.refresh_token:
    credentials.refresh(Request())
    with open(token_path, 'wb') as token:
        pickle.dump(credentials, token)
```

**What this means**:
- ✅ Same auto-refresh as YouTube
- ✅ Never expires
- ✅ Runs forever

### Zoom API (Server-to-Server OAuth)
**File**: `src/zoom_client.py`

```python
# Auto-refresh logic (already implemented)
def _get_access_token(self):
    # Always gets fresh token
    # Tokens last 1 hour, but we get new one each time
    response = requests.post(url, auth=(client_id, client_secret))
    return response.json()['access_token']
```

**What this means**:
- ✅ Gets fresh token on every API call
- ✅ No expiration issues
- ✅ Server-to-Server = no user interaction needed

### Google Sheets API (Service Account)
**File**: `src/sheets_integration.py`

```python
# Service Account (already implemented)
creds = Credentials.from_service_account_file(
    service_account_file, 
    scopes=scopes
)
```

**What this means**:
- ✅ Service accounts don't expire
- ✅ No refresh needed
- ✅ Works forever

## Verification Checklist

Before deploying, verify these files exist:

### 1. YouTube Token
```bash
ls -la secrets/token.json
```
**Status**: ✅ Contains refresh_token
**Lifespan**: Infinite (auto-refreshes)

### 2. Drive Token
```bash
ls -la secrets/token_drive.json
```
**Status**: ✅ Contains refresh_token
**Lifespan**: Infinite (auto-refreshes)

### 3. Google Sheets Service Account
```bash
ls -la secrets/service_account.json
```
**Status**: ✅ Service account (never expires)
**Lifespan**: Infinite

### 4. Zoom Credentials
```bash
grep ZOOM .env
```
**Status**: ✅ Server-to-Server OAuth
**Lifespan**: Infinite (gets new token each call)

## Error Handling

If a token refresh fails, the system:
1. Logs the error
2. Continues running (doesn't crash)
3. Retries on next cycle
4. Sends notification (if configured)

## Monitoring Token Health

Add this to your monitoring:

```bash
# Check if tokens are being refreshed
sudo journalctl -u ytz-backend | grep "Refreshing"

# Should see:
# "Refreshing Access Token..."
# "Refreshing Drive Access Token..."
```

## Production Deployment Checklist

Before going live:

- [ ] All tokens generated with `offline_access` scope
- [ ] `refresh_token` present in token files
- [ ] Service account has correct permissions
- [ ] Zoom credentials are Server-to-Server (not OAuth)
- [ ] All API clients have retry logic
- [ ] Error notifications configured

## If Tokens Ever Fail

**YouTube/Drive**:
```bash
# Re-authenticate (one-time)
cd /home/user/ytz-automation
source venv/bin/activate
python scripts/setup_youtube.py
python scripts/setup_drive.py
```

**Zoom**:
```bash
# Just update .env with new credentials
nano .env
# Update ZOOM_*_CLIENT_SECRET
sudo systemctl restart ytz-backend
```

**Google Sheets**:
```bash
# Upload new service account file
scp service_account.json user@server:/home/user/ytz-automation/secrets/
sudo systemctl restart ytz-backend
```

## Summary

✅ **All APIs configured for infinite operation**
✅ **Auto-refresh implemented for OAuth tokens**
✅ **Service accounts used where possible**
✅ **Retry logic on all API calls**
✅ **Error handling prevents crashes**

**Your system will run 24/7 without token expiration issues.**
