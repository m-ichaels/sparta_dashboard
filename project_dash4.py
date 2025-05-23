import pandas as pd
import dash
from dash import dcc, html, Input, Output
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date

# Load and clean data
df = pd.read_csv("support_tickets_2500.csv", parse_dates=["DateOpened", "DateClosed"])
df["ResolutionTimeHours"] = (df["DateClosed"] - df["DateOpened"]).dt.total_seconds() / 3600
df["Status"] = df["Status"].fillna("Unknown")
df["AssignedTo"] = df["AssignedTo"].fillna("Unassigned")
df["Resolution"] = df["Resolution"].fillna("Unresolved")

# Add additional date/time features for analysis
df["DayOfWeek"] = df["DateOpened"].dt.day_name()
df["HourOfDay"] = df["DateOpened"].dt.hour
df["MonthYear"] = df["DateOpened"].dt.to_period('M').astype(str)

# Add first contact time calculation (assuming first response is tracked somehow)
# For demo purposes, we'll simulate first contact time as a fraction of resolution time
df["FirstContactTimeHours"] = df["ResolutionTimeHours"] * 0.1  # Simulated

# Add reopen indicator (simulated - in real scenario this would be tracked)
df["WasReopened"] = (df["TicketID"] % 20 == 0)  # Simulated: every 20th ticket was reopened

# Get date range for filters
min_date = df["DateOpened"].min().date()
max_date = df["DateOpened"].max().date()

# Get resolution time range for filters
min_resolution_time = df["ResolutionTimeHours"].min()
max_resolution_time = df["ResolutionTimeHours"].max()

# Professional Color Palette
COLORS = {
    'primary': '#1e40af',      # Professional blue
    'secondary': '#64748b',    # Slate gray
    'accent': '#0f766e',       # Teal
    'success': '#059669',      # Green
    'warning': '#d97706',      # Amber
    'danger': '#dc2626',       # Red
    'info': '#0284c7',         # Sky blue
    'light': '#f8fafc',        # Light gray
    'dark': '#1e293b',         # Dark slate
    'background': '#f1f5f9'    # Light blue-gray
}

# Chart color palette for consistency
CHART_COLORS = [
    COLORS['primary'], COLORS['accent'], COLORS['success'], 
    COLORS['warning'], COLORS['danger'], COLORS['info'],
    '#6366f1', '#8b5cf6', '#ec4899', '#f59e0b'
]

# Initialize Dash app
app = dash.Dash(__name__)
app.title = "Support Tickets Dashboard"

# Professional CSS styling
app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>Support Tickets Dashboard</title>
        {%favicon%}
        {%css%}
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
            
            body {
                background-color: #f1f5f9;
                margin: 0;
                padding: 0;
                font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                color: #1e293b;
            }
            
            .main-container {
                max-width: 1400px;
                margin: 0 auto;
                padding: 24px;
            }
            
            .dashboard-header {
                background: linear-gradient(135deg, #1e40af 0%, #0f766e 100%);
                color: white;
                padding: 32px;
                border-radius: 12px;
                margin-bottom: 32px;
                box-shadow: 0 4px 20px rgba(30, 64, 175, 0.15);
            }
            
            .dashboard-title {
                font-size: 2.25rem;
                font-weight: 700;
                margin: 0;
                text-align: center;
                letter-spacing: -0.025em;
            }
            
            .dashboard-subtitle {
                font-size: 1.125rem;
                font-weight: 400;
                margin: 8px 0 0 0;
                text-align: center;
                opacity: 0.9;
            }
            
            .filter-container {
                background-color: white;
                padding: 24px;
                border-radius: 12px;
                box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
                margin-bottom: 24px;
                border: 1px solid #e2e8f0;
            }
            
            .filter-row {
                display: flex;
                flex-wrap: wrap;
                gap: 16px;
                margin-bottom: 20px;
            }
            
            .filter-row:last-child {
                margin-bottom: 0;
            }
            
            .filter-item {
                flex: 1;
                min-width: 200px;
            }
            
            .filter-item-wide {
                flex: 2;
                min-width: 300px;
            }
            
            .filter-section {
                margin-bottom: 8px;
            }
            
            .filter-section label {
                font-weight: 600;
                color: #374151;
                margin-bottom: 8px;
                display: block;
                font-size: 0.875rem;
                text-transform: uppercase;
                letter-spacing: 0.025em;
            }
            
            .kpi-container {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
                gap: 20px;
                margin-bottom: 32px;
            }
            
            .kpi-card {
                background: white;
                padding: 24px;
                border-radius: 12px;
                text-align: center;
                box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
                border: 1px solid #e2e8f0;
                transition: transform 0.2s ease, box-shadow 0.2s ease;
                position: relative;
                overflow: hidden;
            }
            
            .kpi-card:hover {
                transform: translateY(-2px);
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
            }
            
            .kpi-card::before {
                content: '';
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                height: 4px;
                background: linear-gradient(90deg, #1e40af, #0f766e);
            }
            
            .kpi-value {
                font-size: 2.5rem;
                font-weight: 700;
                color: #1e40af;
                margin-bottom: 8px;
                line-height: 1;
            }
            
            .kpi-label {
                font-size: 0.875rem;
                color: #64748b;
                font-weight: 500;
                text-transform: uppercase;
                letter-spacing: 0.05em;
            }
            
            .chart-container {
                background-color: white;
                border-radius: 12px;
                box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
                border: 1px solid #e2e8f0;
                margin-bottom: 24px;
                overflow: hidden;
            }
            
            .chart-title {
                padding: 20px 24px 0 24px;
                font-size: 1.125rem;
                font-weight: 600;
                color: #1e293b;
                margin: 0;
            }
            
            .dash-graph {
                padding: 16px;
            }
            
            .row {
                display: grid;
                gap: 24px;
                margin-bottom: 24px;
            }
            
            .row-3 { grid-template-columns: repeat(3, 1fr); }
            .row-2 { grid-template-columns: repeat(2, 1fr); }
            .row-1 { grid-template-columns: 1fr; }
            
            @media (max-width: 1024px) {
                .row-3 { grid-template-columns: 1fr; }
                .row-2 { grid-template-columns: 1fr; }
                .filter-row { flex-direction: column; }
            }
            
            @media (max-width: 768px) {
                .main-container { padding: 16px; }
                .dashboard-header { padding: 24px 16px; }
                .dashboard-title { font-size: 1.75rem; }
                .kpi-container { grid-template-columns: 1fr; }
            }
            
            .Select-control {
                border: 1px solid #d1d5db !important;
                border-radius: 8px !important;
                box-shadow: none !important;
            }
            
            .Select-control:hover {
                border-color: #1e40af !important;
            }
            
            .Select-option:hover {
                background-color: #eff6ff !important;
            }
            
            .DateInput {
                width: 100% !important;
            }
            
            .DateRangePickerInput {
                border: 1px solid #d1d5db !important;
                border-radius: 8px !important;
                background: white !important;
                box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05) !important;
            }
            
            .DateRangePickerInput:hover {
                border-color: #1e40af !important;
                box-shadow: 0 2px 4px rgba(30, 64, 175, 0.1) !important;
            }
            
            .DateInput_input {
                background: transparent !important;
                border: none !important;
                padding: 8px 12px !important;
                font-family: 'Inter', sans-serif !important;
                font-size: 14px !important;
                color: #374151 !important;
            }
            
            .DateInput_input:focus {
                outline: none !important;
                box-shadow: none !important;
            }
            
            .DateRangePickerInput_arrow {
                color: #64748b !important;
            }
        </style>
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
'''

# Layout
app.layout = html.Div([
    html.Div([
        html.Div([
            html.H1("Support Tickets Dashboard", className="dashboard-title"),
            html.P("Real-time analytics and insights for customer support operations", 
                   className="dashboard-subtitle")
        ], className="dashboard-header"),
        
        # Enhanced Filters
        html.Div([
            # First row of filters
            html.Div([
                html.Div([
                    html.Label("Date Range", className="filter-section"),
                    dcc.DatePickerRange(
                        id="date-range-filter",
                        start_date=min_date,
                        end_date=max_date,
                        display_format='YYYY-MM-DD',
                        style={'width': '100%'}
                    )
                ], className="filter-item"),
                
                html.Div([
                    html.Label("Product", className="filter-section"),
                    dcc.Dropdown(
                        options=[{"label": prod, "value": prod} for prod in sorted(df["Product"].unique())],
                        id="product-filter",
                        multi=True,
                        placeholder="Select products..."
                    )
                ], className="filter-item"),

                html.Div([
                    html.Label("Priority", className="filter-section"),
                    dcc.Dropdown(
                        options=[{"label": p, "value": p} for p in sorted(df["Priority"].unique())],
                        id="priority-filter",
                        multi=True,
                        placeholder="Select priorities..."
                    )
                ], className="filter-item"),
            ], className="filter-row"),
            
            # Second row of filters
            html.Div([
                html.Div([
                    html.Label("Status", className="filter-section"),
                    dcc.Dropdown(
                        options=[{"label": s, "value": s} for s in sorted(df["Status"].unique())],
                        id="status-filter",
                        multi=True,
                        placeholder="Select statuses..."
                    )
                ], className="filter-item"),
                
                html.Div([
                    html.Label("Assigned To", className="filter-section"),
                    dcc.Dropdown(
                        options=[{"label": agent, "value": agent} for agent in sorted(df["AssignedTo"].unique())],
                        id="assigned-to-filter",
                        multi=True,
                        placeholder="Select team members..."
                    )
                ], className="filter-item"),
                
                html.Div([
                    html.Label("Issue Type", className="filter-section"),
                    dcc.Dropdown(
                        options=[{"label": issue, "value": issue} for issue in sorted(df["Issue"].unique())],
                        id="issue-type-filter",
                        multi=True,
                        placeholder="Select issue types..."
                    )
                ], className="filter-item"),
            ], className="filter-row"),
            
            # Third row - Resolution time range
            html.Div([
                html.Div([
                    html.Label("Resolution Time Range (Hours)", className="filter-section"),
                    dcc.RangeSlider(
                        id="resolution-time-filter",
                        min=0,
                        max=max_resolution_time if not pd.isna(max_resolution_time) else 100,
                        value=[0, max_resolution_time if not pd.isna(max_resolution_time) else 100],
                        marks={
                            0: '0h',
                            24: '24h',
                            48: '48h',
                            72: '72h',
                            168: '1w',
                            int(max_resolution_time) if not pd.isna(max_resolution_time) else 100: f'{int(max_resolution_time) if not pd.isna(max_resolution_time) else 100}h'
                        },
                        tooltip={"placement": "bottom", "always_visible": True}
                    )
                ], className="filter-item-wide"),
            ], className="filter-row"),
        ], className="filter-container"),

        # KPI Cards
        html.Div([
            html.Div([
                html.Div("0", id="total-tickets-kpi", className="kpi-value"),
                html.Div("Total Tickets", className="kpi-label")
            ], className="kpi-card"),
            
            html.Div([
                html.Div("0%", id="closure-rate-kpi", className="kpi-value"),
                html.Div("Closure Rate", className="kpi-label")
            ], className="kpi-card"),
            
            html.Div([
                html.Div("0h", id="avg-resolution-kpi", className="kpi-value"),
                html.Div("Avg Resolution Time", className="kpi-label")
            ], className="kpi-card"),
            
            html.Div([
                html.Div("0h", id="avg-first-contact-kpi", className="kpi-value"),
                html.Div("First Contact Time", className="kpi-label")
            ], className="kpi-card"),
            
            html.Div([
                html.Div("0%", id="reopen-rate-kpi", className="kpi-value"),
                html.Div("Reopen Rate", className="kpi-label")
            ], className="kpi-card"),
        ], className="kpi-container"),

        # Charts Grid
        html.Div([
            html.Div([dcc.Graph(id="status-pie-chart")], className="chart-container"),
            html.Div([dcc.Graph(id="tickets-by-product")], className="chart-container"),
            html.Div([dcc.Graph(id="priority-distribution")], className="chart-container"),
        ], className="row row-3"),
        
        html.Div([
            html.Div([dcc.Graph(id="top-issues")], className="chart-container"),
            html.Div([dcc.Graph(id="tickets-over-time")], className="chart-container"),
        ], className="row row-2"),
        
        html.Div([
            html.Div([dcc.Graph(id="resolution-time-hist")], className="chart-container"),
            html.Div([dcc.Graph(id="team-performance")], className="chart-container"),
        ], className="row row-2"),
        
        html.Div([
            html.Div([dcc.Graph(id="tickets-by-day")], className="chart-container"),
            html.Div([dcc.Graph(id="tickets-by-hour")], className="chart-container"),
        ], className="row row-2"),
        
        html.Div([
            html.Div([dcc.Graph(id="product-priority-heatmap")], className="chart-container"),
            html.Div([dcc.Graph(id="monthly-trends")], className="chart-container"),
        ], className="row row-2"),
    ], className="main-container")
])

# Helper function to style charts consistently
def style_chart(fig, title):
    fig.update_layout(
        title=dict(
            text=title,
            font=dict(size=16, color=COLORS['dark'], family="Inter"),
            x=0.02,
            y=0.95
        ),
        plot_bgcolor='white',
        paper_bgcolor='white',
        font=dict(family="Inter", color=COLORS['dark']),
        margin=dict(l=40, r=40, t=60, b=40),
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.2,
            xanchor="center",
            x=0.5
        )
    )
    return fig

# Enhanced Callbacks for KPIs and Charts with all filters
@app.callback(
    [Output("total-tickets-kpi", "children"),
     Output("closure-rate-kpi", "children"),
     Output("avg-resolution-kpi", "children"),
     Output("avg-first-contact-kpi", "children"),
     Output("reopen-rate-kpi", "children"),
     Output("status-pie-chart", "figure"),
     Output("tickets-by-product", "figure"),
     Output("priority-distribution", "figure"),
     Output("top-issues", "figure"),
     Output("tickets-over-time", "figure"),
     Output("resolution-time-hist", "figure"),
     Output("team-performance", "figure"),
     Output("tickets-by-day", "figure"),
     Output("tickets-by-hour", "figure"),
     Output("product-priority-heatmap", "figure"),
     Output("monthly-trends", "figure")],
    [Input("date-range-filter", "start_date"),
     Input("date-range-filter", "end_date"),
     Input("product-filter", "value"),
     Input("priority-filter", "value"),
     Input("status-filter", "value"),
     Input("assigned-to-filter", "value"),
     Input("issue-type-filter", "value"),
     Input("resolution-time-filter", "value")]
)
def update_dashboard(start_date, end_date, selected_products, selected_priorities, 
                    selected_statuses, selected_assigned_to, selected_issues, resolution_time_range):
    dff = df.copy()
    
    # Apply date range filter
    if start_date and end_date:
        dff = dff[(dff["DateOpened"].dt.date >= pd.to_datetime(start_date).date()) & 
                  (dff["DateOpened"].dt.date <= pd.to_datetime(end_date).date())]
    
    # Apply other filters
    if selected_products:
        dff = dff[dff["Product"].isin(selected_products)]
    if selected_priorities:
        dff = dff[dff["Priority"].isin(selected_priorities)]
    if selected_statuses:
        dff = dff[dff["Status"].isin(selected_statuses)]
    if selected_assigned_to:
        dff = dff[dff["AssignedTo"].isin(selected_assigned_to)]
    if selected_issues:
        dff = dff[dff["Issue"].isin(selected_issues)]
    
    # Apply resolution time filter
    if resolution_time_range:
        min_res_time, max_res_time = resolution_time_range
        dff = dff[(dff["ResolutionTimeHours"].isna()) | 
                  ((dff["ResolutionTimeHours"] >= min_res_time) & 
                   (dff["ResolutionTimeHours"] <= max_res_time))]

    # Calculate KPIs
    total_tickets = len(dff)
    closed_tickets = len(dff[dff["Status"] == "Closed"])
    closure_rate = (closed_tickets / total_tickets * 100) if total_tickets > 0 else 0
    avg_resolution_time = dff["ResolutionTimeHours"].mean() if not dff["ResolutionTimeHours"].isna().all() else 0
    avg_first_contact = dff["FirstContactTimeHours"].mean() if not dff["FirstContactTimeHours"].isna().all() else 0
    reopened_tickets = len(dff[dff["WasReopened"] == True])
    reopen_rate = (reopened_tickets / total_tickets * 100) if total_tickets > 0 else 0

    # Format KPI values
    kpi_total = f"{total_tickets:,}"
    kpi_closure = f"{closure_rate:.1f}%"
    kpi_resolution = f"{avg_resolution_time:.1f}h"
    kpi_first_contact = f"{avg_first_contact:.1f}h"
    kpi_reopen = f"{reopen_rate:.1f}%"

    # Handle empty dataframe
    if len(dff) == 0:
        empty_fig = px.bar()
        empty_fig = style_chart(empty_fig, "No Data Available")
        return (kpi_total, kpi_closure, kpi_resolution, kpi_first_contact, kpi_reopen,
                *[empty_fig] * 11)

    # 1. Ticket Status Distribution
    status_counts = dff["Status"].value_counts()
    fig1 = px.pie(values=status_counts.values, names=status_counts.index,
                  color_discrete_sequence=CHART_COLORS)
    fig1 = style_chart(fig1, "Ticket Status Distribution")
    
    # 2. Tickets by Product
    product_counts = dff["Product"].value_counts()
    fig2 = px.bar(x=product_counts.index, y=product_counts.values,
                  color_discrete_sequence=[COLORS['primary']])
    fig2 = style_chart(fig2, "Tickets by Product")
    fig2.update_xaxes(title=dict(text="Product", font=dict(color=COLORS['dark'])))
    fig2.update_yaxes(title=dict(text="Number of Tickets", font=dict(color=COLORS['dark'])))
    
    # 3. Priority Distribution
    priority_counts = dff["Priority"].value_counts()
    priority_colors = {
        'Critical': COLORS['danger'],
        'High': COLORS['warning'], 
        'Medium': COLORS['info'],
        'Low': COLORS['success']
    }
    fig3 = px.bar(x=priority_counts.index, y=priority_counts.values,
                  color=priority_counts.index, color_discrete_map=priority_colors)
    fig3 = style_chart(fig3, "Priority Distribution")
    fig3.update_xaxes(title=dict(text="Priority", font=dict(color=COLORS['dark'])))
    fig3.update_yaxes(title=dict(text="Number of Tickets", font=dict(color=COLORS['dark'])))
    
    # 4. Top Issues
    issue_counts = dff["Issue"].value_counts().head(10)
    fig4 = px.bar(x=issue_counts.values, y=issue_counts.index, orientation='h',
                  color_discrete_sequence=[COLORS['accent']])
    fig4 = style_chart(fig4, "Top 10 Issues")
    fig4.update_xaxes(title=dict(text="Number of Tickets", font=dict(color=COLORS['dark'])))
    fig4.update_yaxes(title=dict(text="Issue Type", font=dict(color=COLORS['dark'])))
    
    # 5. Tickets Over Time
    daily_tickets = dff.groupby(dff["DateOpened"].dt.date).size().reset_index()
    daily_tickets.columns = ["Date", "Count"]
    fig5 = px.line(daily_tickets, x="Date", y="Count",
                   color_discrete_sequence=[COLORS['primary']])
    fig5 = style_chart(fig5, "Tickets Opened Over Time")
    fig5.update_traces(line=dict(width=3))
    
    # 6. Resolution Time Distribution
    resolution_data = dff.dropna(subset=["ResolutionTimeHours"])
    if len(resolution_data) > 0:
        fig6 = px.histogram(resolution_data, x="ResolutionTimeHours", nbins=30,
                            color_discrete_sequence=[COLORS['info']])
    else:
        fig6 = px.histogram(pd.DataFrame({'ResolutionTimeHours': [0]}), x="ResolutionTimeHours")
    fig6 = style_chart(fig6, "Resolution Time Distribution")
    
    # 7. Team Performance
    team_stats = dff.groupby("AssignedTo").agg({
        "TicketID": "count",
        "ResolutionTimeHours": "mean"
    }).reset_index()
    team_stats.columns = ["Team Member", "Total Tickets", "Avg Resolution Time"]
    team_stats = team_stats[team_stats["Team Member"] != "Unassigned"].head(10)
    
    if len(team_stats) > 0:
        fig7 = px.bar(team_stats, x="Team Member", y="Total Tickets",
                      color_discrete_sequence=[COLORS['success']],
                      hover_data={"Avg Resolution Time": ":.1f"})
    else:
        fig7 = px.bar()
    fig7 = style_chart(fig7, "Team Performance - Total Tickets")
    
    # 8. Tickets by Day of Week
    day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    day_counts = dff["DayOfWeek"].value_counts().reindex(day_order, fill_value=0)
    fig8 = px.bar(x=day_counts.index, y=day_counts.values,
                  color_discrete_sequence=[COLORS['warning']])
    fig8 = style_chart(fig8, "Tickets by Day of Week")
    
    # 9. Tickets by Hour
    hour_counts = dff["HourOfDay"].value_counts().sort_index()
    fig9 = px.line(x=hour_counts.index, y=hour_counts.values,
                   color_discrete_sequence=[COLORS['accent']])
    fig9 = style_chart(fig9, "Tickets by Hour of Day")
    fig9.update_traces(line=dict(width=3))
    
    # 10. Product vs Priority Heatmap
    if len(dff) > 0:
        heatmap_data = pd.crosstab(dff["Product"], dff["Priority"])
        if not heatmap_data.empty:
            fig10 = px.imshow(heatmap_data.values, 
                              x=heatmap_data.columns, 
                              y=heatmap_data.index,
                              color_continuous_scale="Blues")
        else:
            fig10 = px.imshow([[0]], color_continuous_scale="Blues")
    else:
        fig10 = px.imshow([[0]], color_continuous_scale="Blues")
    fig10 = style_chart(fig10, "Product vs Priority Distribution")
    
    # 11. Monthly Trends
    monthly_product = dff.groupby(["MonthYear", "Product"]).size().reset_index()
    monthly_product.columns = ["Month", "Product", "Count"]
    if len(monthly_product) > 0:
        fig11 = px.line(monthly_product, x="Month", y="Count", color="Product",
                        color_discrete_sequence=CHART_COLORS)
    else:
        fig11 = px.line()
    fig11 = style_chart(fig11, "Monthly Ticket Trends by Product")
    
    return (kpi_total, kpi_closure, kpi_resolution, kpi_first_contact, kpi_reopen,
            fig1, fig2, fig3, fig4, fig5, fig6, fig7, fig8, fig9, fig10, fig11)

if __name__ == "__main__":
    app.run(debug=True)