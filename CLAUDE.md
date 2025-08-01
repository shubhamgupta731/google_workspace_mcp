# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Running the Server
```bash
# Run in stdio mode (default for MCP clients)
uv run main.py

# Run in HTTP mode for debugging
uv run main.py --transport streamable-http

# Run with specific tools only
uv run main.py --tools gmail drive calendar

# Run in single-user mode
uv run main.py --single-user
```

### Installing from PyPI
```bash
# Quick run with uvx (no installation needed)
uvx workspace-mcp

# With specific tools
uvx workspace-mcp --tools gmail drive calendar tasks
```

### Docker
```bash
# Build the image
docker build -t workspace-mcp .

# Run the container
docker run -p 8000:8000 -v $(pwd):/app workspace-mcp --transport streamable-http
```

### Linting and Code Quality
```bash
# Run ruff for linting and formatting
uv run ruff check .
uv run ruff format .
```

## Architecture Overview

### Core Components

1. **FastMCP-based Server** (`core/server.py`)
   - Built on FastMCP for high performance
   - Supports both stdio and streamable-http transports
   - Transport-aware OAuth callback handling
   - Centralized error handling and logging

2. **Authentication System** (`auth/`)
   - `service_decorator.py`: Core decorator pattern for service injection
   - `google_auth.py`: OAuth 2.0 flow handling with token refresh
   - `scopes.py`: Centralized scope management
   - `oauth_callback_server.py`: Handles OAuth callbacks for both transport modes
   - Service caching with 30-minute TTL to reduce authentication overhead
   - Thread-safe session management

3. **Service Modules** (`g*/`)
   Each Google service has its own module:
   - `gcalendar/`: Google Calendar tools
   - `gdrive/`: Google Drive tools  
   - `gmail/`: Gmail tools
   - `gdocs/`: Google Docs tools with comment support
   - `gsheets/`: Google Sheets tools with comment support
   - `gslides/`: Google Slides tools with comment support
   - `gforms/`: Google Forms tools
   - `gtasks/`: Google Tasks tools
   - `gchat/`: Google Chat tools
   - `gsearch/`: Google Custom Search tools

### Key Patterns

1. **Service Decorator Pattern**
   ```python
   @require_google_service("drive", "drive_read")
   async def your_tool(service, param1: str):
       # service is automatically injected and cached
       return service.files().list().execute()
   ```

### Recent Updates

#### Enhanced Calendar Attendee Support
The Google Calendar tools now support full EventAttendee entity handling:

1. **Reading Attendee Information**:
   - `get_event` now displays full attendee details including response status (accepted/declined/tentative/needsAction)
   - `get_events` has new `include_attendees` parameter to show response summary
   - New `get_event_attendees` tool provides comprehensive attendee details

2. **Creating/Modifying Events with Attendees**:
   - Both `create_event` and `modify_event` now accept attendee dictionaries:
   ```python
   attendees=[
       {"email": "john@example.com", "optional": True},
       {"email": "jane@example.com", "displayName": "Jane Smith", "additionalGuests": 2}
   ]
   ```
   - Backward compatible with simple email string lists

2. **Multi-Service Support**
   ```python
   @require_multiple_services({
       "drive": "drive_read",
       "docs": "docs_read"
   })
   async def cross_service_tool(services, doc_id: str):
       drive_service = services["drive"]
       docs_service = services["docs"]
   ```

3. **Error Handling**
   - Native exceptions instead of manual error construction
   - Authentication errors trigger OAuth flow
   - Graceful handling of API rate limits and quotas

### Environment Variables

Required for OAuth:
- `GOOGLE_OAUTH_CLIENT_ID`: OAuth client ID from Google Cloud
- `GOOGLE_OAUTH_CLIENT_SECRET`: OAuth client secret
- `OAUTHLIB_INSECURE_TRANSPORT=1`: Required for development (http:// callbacks)

Optional:
- `USER_GOOGLE_EMAIL`: Default email for single-user mode
- `GOOGLE_PSE_API_KEY`: API key for Google Custom Search
- `GOOGLE_PSE_ENGINE_ID`: Programmable Search Engine ID
- `WORKSPACE_MCP_PORT`: Server port (default: 8000)
- `WORKSPACE_MCP_BASE_URI`: Base URI (default: http://localhost)
- `GOOGLE_CLIENT_SECRET_PATH`: Path to client_secret.json file

### Adding New Tools

1. Create a new tool in the appropriate service module
2. Use the `@require_google_service` decorator
3. The decorator handles:
   - Authentication and token refresh
   - Service instantiation and caching
   - Error handling
   - Scope validation

Example:
```python
from auth.service_decorator import require_google_service

@require_google_service("drive", "drive_read")
async def new_drive_tool(service, folder_id: str):
    """Tool description for MCP"""
    result = service.files().list(
        q=f"'{folder_id}' in parents",
        fields="files(id, name, mimeType)"
    ).execute()
    return result.get('files', [])
```

### OAuth Flow

1. Tools requiring authentication return an auth URL on first call
2. User authorizes in browser
3. Server handles callback automatically:
   - Stdio mode: Starts minimal HTTP server on port 8000
   - HTTP mode: Uses existing FastAPI endpoints
4. Tokens are stored in `.credentials/` directory
5. Automatic token refresh on expiration

### Service Caching

- Services are cached for 30 minutes after creation
- Cache key includes email and requested scopes
- Thread-safe implementation using locks
- Reduces API calls and improves performance

### Security Considerations

- Never commit `client_secret.json` or `.credentials/`
- Use HTTPS for production OAuth callbacks
- Credentials stored per-email in `.credentials/`
- Automatic cleanup of expired cache entries