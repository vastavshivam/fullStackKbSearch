from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import HTMLResponse
from api.widget import widget_configs, analytics_events
import json

router = APIRouter()

@router.get("/dashboard", response_class=HTMLResponse)
async def widget_dashboard():
    """Simple dashboard for managing widgets"""
    
    # Get total stats
    total_widgets = len(widget_configs)
    total_events = len(analytics_events)
    
    # Generate widgets HTML
    widgets_html = ""
    for client_id, config in widget_configs.items():
        client_events = [e for e in analytics_events if e.client_id == client_id]
        widgets_html += f"""
        <div style="border: 1px solid #ddd; border-radius: 8px; padding: 16px; margin-bottom: 16px;">
            <h3>Widget: {config.chat_title}</h3>
            <p><strong>Client ID:</strong> {client_id}</p>
            <p><strong>Domain:</strong> {config.domain or 'Not set'}</p>
            <p><strong>Theme:</strong> {config.theme}</p>
            <p><strong>Position:</strong> {config.position}</p>
            <p><strong>Events:</strong> {len(client_events)}</p>
            
            <div style="margin-top: 12px;">
                <h4>Embed Code:</h4>
                <textarea readonly style="width: 100%; height: 60px; font-family: monospace; font-size: 12px; background: #f5f5f5; border: 1px solid #ddd; border-radius: 4px; padding: 8px;"><!-- AI Knowledge Base Widget -->
<script async src="http://localhost:8004/api/widget/script/{client_id}"></script></textarea>
            </div>
            
            <div style="margin-top: 12px;">
                <button onclick="deleteWidget('{client_id}')" style="background: #dc3545; color: white; border: none; padding: 8px 16px; border-radius: 4px; cursor: pointer;">Delete Widget</button>
                <button onclick="viewAnalytics('{client_id}')" style="background: #007bff; color: white; border: none; padding: 8px 16px; border-radius: 4px; cursor: pointer; margin-left: 8px;">View Analytics</button>
            </div>
        </div>
        """
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Widget Dashboard</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 0; background: #f8f9fa; }}
            .container {{ max-width: 1200px; margin: 0 auto; padding: 20px; }}
            .header {{ background: #007bff; color: white; padding: 20px; margin: -20px -20px 20px; border-radius: 8px; }}
            .stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px; margin-bottom: 24px; }}
            .stat-card {{ background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); text-align: center; }}
            .stat-number {{ font-size: 2em; font-weight: bold; color: #007bff; }}
            .create-widget {{ background: #28a745; color: white; border: none; padding: 12px 24px; border-radius: 6px; cursor: pointer; font-size: 16px; margin-bottom: 24px; }}
            .widgets-list {{ background: white; border-radius: 8px; padding: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🔧 Widget Dashboard</h1>
                <p>Manage your embedded AI assistant widgets</p>
            </div>
            
            <div class="stats">
                <div class="stat-card">
                    <div class="stat-number">{total_widgets}</div>
                    <div>Total Widgets</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">{total_events}</div>
                    <div>Total Events</div>
                </div>
            </div>
            
            <button class="create-widget" onclick="createNewWidget()">+ Create New Widget</button>
            
            <div class="widgets-list">
                <h2>Your Widgets</h2>
                {widgets_html if widgets_html else '<p>No widgets created yet. Click "Create New Widget" to get started!</p>'}
            </div>
        </div>
        
        <script>
            async function createNewWidget() {{
                try {{
                    const response = await fetch('/api/widget/generate', {{
                        method: 'POST',
                        headers: {{ 'Content-Type': 'application/json' }}
                    }});
                    const data = await response.json();
                    
                    if (response.ok) {{
                        alert('Widget created! Client ID: ' + data.client_id);
                        location.reload();
                    }} else {{
                        alert('Error creating widget: ' + data.detail);
                    }}
                }} catch (error) {{
                    alert('Error: ' + error.message);
                }}
            }}
            
            async function deleteWidget(clientId) {{
                if (!confirm('Are you sure you want to delete this widget?')) return;
                
                try {{
                    const response = await fetch('/api/widget/config/' + clientId, {{
                        method: 'DELETE'
                    }});
                    
                    if (response.ok) {{
                        alert('Widget deleted!');
                        location.reload();
                    }} else {{
                        alert('Error deleting widget');
                    }}
                }} catch (error) {{
                    alert('Error: ' + error.message);
                }}
            }}
            
            async function viewAnalytics(clientId) {{
                try {{
                    const response = await fetch('/api/widget/analytics/' + clientId);
                    const data = await response.json();
                    
                    let message = `Analytics for Widget ${{clientId}}:\\n\\n`;
                    message += `Total Events: ${{data.total_events}}\\n`;
                    message += `Event Breakdown:\\n`;
                    
                    for (const [type, count] of Object.entries(data.event_breakdown)) {{
                        message += `- ${{type}}: ${{count}}\\n`;
                    }}
                    
                    alert(message);
                }} catch (error) {{
                    alert('Error fetching analytics: ' + error.message);
                }}
            }}
        </script>
    </body>
    </html>
    """
    
    return html_content
