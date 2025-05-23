import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import dash
from dash import dcc, html, Input, Output, callback_context
import dash_bootstrap_components as dbc
from datetime import datetime, timedelta
import numpy as np

class InteractiveTicketDashboard:
    def __init__(self, csv_file_path):
        """Initialize the interactive dashboard with ticket data"""
        self.df = pd.read_csv(csv_file_path)
        self.prepare_data()
        self.app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
        self.setup_layout()
        self.setup_callbacks()
        
    def prepare_data(self):
        """Clean and prepare the data for analysis"""
        # Convert date columns
        self.df['DateOpened'] = pd.to_datetime(self.df['DateOpened'], format='%m/%d/%Y %H:%M')
        self.df['DateClosed'] = pd.to_datetime(self.df['DateClosed'], format='%m/%d/%Y %H:%M', errors='coerce')
        
        # Calculate resolution time in hours (only for closed tickets)
        closed_mask = self.df['DateClosed'].notna()
        self.df.loc[closed_mask, 'ResolutionHours'] = (
            self.df.loc[closed_mask, 'DateClosed'] - self.df.loc[closed_mask, 'DateOpened']
        ).dt.total_seconds() / 3600
        
        # Extract time components
        self.df['OpenedMonth'] = self.df['DateOpened'].dt.month
        self.df['OpenedDayOfWeek'] = self.df['DateOpened'].dt.day_name()
        self.df['OpenedHour'] = self.df['DateOpened'].dt.hour
        self.df['OpenedDate'] = self.df['DateOpened'].dt.date
        
        # Clean status column
        self.df['CleanStatus'] = self.df['Status'].apply(lambda x: 
            'Closed' if 'Closed' in str(x) else 
            'Open' if 'Open' in str(x) else str(x)
        )
        
        print(f"Dashboard initialized with {len(self.df)} tickets")
    
    def create_kpi_cards(self, filtered_df):
        """Create KPI cards for key metrics"""
        total_tickets = len(filtered_df)
        closed_tickets = len(filtered_df[filtered_df['CleanStatus'] == 'Closed'])
        open_tickets = len(filtered_df[filtered_df['CleanStatus'] == 'Open'])
        avg_resolution = filtered_df['ResolutionHours'].mean()
        
        closure_rate = (closed_tickets / total_tickets * 100) if total_tickets > 0 else 0
        
        cards = dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4(f"{total_tickets:,}", className="card-title text-primary"),
                        html.P("Total Tickets", className="card-subtitle"),
                    ])
                ], className="mb-3")
            ], width=3),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4(f"{closure_rate:.1f}%", className="card-title text-success"),
                        html.P("Closure Rate", className="card-subtitle"),
                    ])
                ], className="mb-3")
            ], width=3),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4(f"{open_tickets:,}", className="card-title text-warning"),
                        html.P("Open Tickets", className="card-subtitle"),
                    ])
                ], className="mb-3")
            ], width=3),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4(f"{avg_resolution:.1f}h" if not pd.isna(avg_resolution) else "N/A", 
                               className="card-title text-info"),
                        html.P("Avg Resolution Time", className="card-subtitle"),
                    ])
                ], className="mb-3")
            ], width=3),
        ])
        
        return cards
    
    def setup_layout(self):
        """Setup the dashboard layout"""
        self.app.layout = dbc.Container([
            # Header
            dbc.Row([
                dbc.Col([
                    html.H1("🎫 Support Ticket Dashboard", 
                           className="text-center mb-4 text-primary"),
                    html.Hr(),
                ])
            ]),
            
            # Filters Row
            dbc.Row([
                dbc.Col([
                    html.Label("Product Filter:", className="fw-bold"),
                    dcc.Dropdown(
                        id='product-filter',
                        options=[{'label': 'All Products', 'value': 'all'}] + 
                               [{'label': product, 'value': product} for product in self.df['Product'].unique()],
                        value='all',
                        className="mb-3"
                    )
                ], width=3),
                
                dbc.Col([
                    html.Label("Priority Filter:", className="fw-bold"),
                    dcc.Dropdown(
                        id='priority-filter',
                        options=[{'label': 'All Priorities', 'value': 'all'}] + 
                               [{'label': priority, 'value': priority} for priority in self.df['Priority'].unique()],
                        value='all',
                        className="mb-3"
                    )
                ], width=3),
                
                dbc.Col([
                    html.Label("Status Filter:", className="fw-bold"),
                    dcc.Dropdown(
                        id='status-filter',
                        options=[{'label': 'All Status', 'value': 'all'}] + 
                               [{'label': status, 'value': status} for status in self.df['CleanStatus'].unique()],
                        value='all',
                        className="mb-3"
                    )
                ], width=3),
                
                dbc.Col([
                    html.Label("Date Range:", className="fw-bold"),
                    dcc.DatePickerRange(
                        id='date-range-picker',
                        start_date=self.df['DateOpened'].min(),
                        end_date=self.df['DateOpened'].max(),
                        display_format='YYYY-MM-DD',
                        className="mb-3"
                    )
                ], width=3),
            ], className="mb-4"),
            
            # KPI Cards
            html.Div(id='kpi-cards'),
            
            # Charts Row 1
            dbc.Row([
                dbc.Col([
                    dcc.Graph(id='status-pie-chart')
                ], width=4),
                dbc.Col([
                    dcc.Graph(id='product-bar-chart')
                ], width=4),
                dbc.Col([
                    dcc.Graph(id='priority-bar-chart')
                ], width=4),
            ], className="mb-4"),
            
            # Charts Row 2
            dbc.Row([
                dbc.Col([
                    dcc.Graph(id='timeline-chart')
                ], width=8),
                dbc.Col([
                    dcc.Graph(id='top-issues-chart')
                ], width=4),
            ], className="mb-4"),
            
            # Charts Row 3
            dbc.Row([
                dbc.Col([
                    dcc.Graph(id='resolution-time-histogram')
                ], width=6),
                dbc.Col([
                    dcc.Graph(id='team-performance-chart')
                ], width=6),
            ], className="mb-4"),
            
            # Charts Row 4
            dbc.Row([
                dbc.Col([
                    dcc.Graph(id='day-of-week-chart')
                ], width=4),
                dbc.Col([
                    dcc.Graph(id='hour-of-day-chart')
                ], width=4),
                dbc.Col([
                    dcc.Graph(id='product-priority-heatmap')
                ], width=4),
            ], className="mb-4"),
            
            # Monthly trends
            dbc.Row([
                dbc.Col([
                    dcc.Graph(id='monthly-trends-chart')
                ], width=12),
            ]),
            
        ], fluid=True)
    
    def filter_data(self, product, priority, status, start_date, end_date):
        """Filter data based on user selections"""
        filtered_df = self.df.copy()
        
        if product != 'all':
            filtered_df = filtered_df[filtered_df['Product'] == product]
        if priority != 'all':
            filtered_df = filtered_df[filtered_df['Priority'] == priority]
        if status != 'all':
            filtered_df = filtered_df[filtered_df['CleanStatus'] == status]
        if start_date and end_date:
            filtered_df = filtered_df[
                (filtered_df['DateOpened'] >= pd.to_datetime(start_date)) &
                (filtered_df['DateOpened'] <= pd.to_datetime(end_date))
            ]
        
        return filtered_df
    
    def setup_callbacks(self):
        """Setup interactive callbacks"""
        
        @self.app.callback(
            [Output('kpi-cards', 'children'),
             Output('status-pie-chart', 'figure'),
             Output('product-bar-chart', 'figure'),
             Output('priority-bar-chart', 'figure'),
             Output('timeline-chart', 'figure'),
             Output('top-issues-chart', 'figure'),
             Output('resolution-time-histogram', 'figure'),
             Output('team-performance-chart', 'figure'),
             Output('day-of-week-chart', 'figure'),
             Output('hour-of-day-chart', 'figure'),
             Output('product-priority-heatmap', 'figure'),
             Output('monthly-trends-chart', 'figure')],
            [Input('product-filter', 'value'),
             Input('priority-filter', 'value'),
             Input('status-filter', 'value'),
             Input('date-range-picker', 'start_date'),
             Input('date-range-picker', 'end_date')]
        )
        def update_dashboard(product, priority, status, start_date, end_date):
            # Filter data
            filtered_df = self.filter_data(product, priority, status, start_date, end_date)
            
            # KPI Cards
            kpi_cards = self.create_kpi_cards(filtered_df)
            
            # 1. Status Pie Chart
            status_counts = filtered_df['CleanStatus'].value_counts()
            status_fig = px.pie(
                values=status_counts.values,
                names=status_counts.index,
                title="Ticket Status Distribution",
                color_discrete_map={'Closed': '#28a745', 'Open': '#dc3545', 'Reopened': '#ffc107'}
            )
            status_fig.update_traces(textposition='inside', textinfo='percent+label')
            
            # 2. Product Bar Chart
            product_counts = filtered_df['Product'].value_counts()
            product_fig = px.bar(
                x=product_counts.index,
                y=product_counts.values,
                title="Tickets by Product",
                labels={'x': 'Product', 'y': 'Number of Tickets'},
                color=product_counts.values,
                color_continuous_scale='viridis'
            )
            product_fig.update_traces(texttemplate='%{y}', textposition='outside')
            
            # 3. Priority Bar Chart
            priority_counts = filtered_df['Priority'].value_counts()
            priority_order = ['High', 'Medium', 'Low']
            priority_counts = priority_counts.reindex([p for p in priority_order if p in priority_counts.index])
            
            priority_fig = px.bar(
                x=priority_counts.index,
                y=priority_counts.values,
                title="Priority Distribution",
                labels={'x': 'Priority', 'y': 'Number of Tickets'},
                color=priority_counts.index,
                color_discrete_map={'High': '#dc3545', 'Medium': '#ffc107', 'Low': '#28a745'}
            )
            priority_fig.update_traces(texttemplate='%{y}', textposition='outside')
            
            # 4. Timeline Chart
            daily_tickets = filtered_df.groupby('OpenedDate').size().reset_index()
            daily_tickets.columns = ['Date', 'Tickets']
            timeline_fig = px.line(
                daily_tickets,
                x='Date',
                y='Tickets',
                title="Tickets Opened Over Time",
                markers=True
            )
            timeline_fig.update_traces(line_color='#007bff', line_width=3)
            timeline_fig.update_layout(hovermode='x unified')
            
            # 5. Top Issues Chart
            issue_counts = filtered_df['Issue'].value_counts().head(8)
            issues_fig = px.bar(
                x=issue_counts.values,
                y=[issue[:25] + '...' if len(issue) > 25 else issue for issue in issue_counts.index],
                orientation='h',
                title="Top Issues",
                labels={'x': 'Number of Tickets', 'y': 'Issue Type'},
                color=issue_counts.values,
                color_continuous_scale='reds'
            )
            issues_fig.update_traces(texttemplate='%{x}', textposition='outside')
            
            # 6. Resolution Time Histogram
            resolution_data = filtered_df['ResolutionHours'].dropna()
            if len(resolution_data) > 0:
                resolution_fig = px.histogram(
                    x=resolution_data,
                    nbins=30,
                    title="Resolution Time Distribution",
                    labels={'x': 'Hours to Resolution', 'y': 'Number of Tickets'},
                    color_discrete_sequence=['#17a2b8']
                )
                # Add mean and median lines
                resolution_fig.add_vline(
                    x=resolution_data.mean(),
                    line_dash="dash",
                    line_color="red",
                    annotation_text=f"Mean: {resolution_data.mean():.1f}h"
                )
                resolution_fig.add_vline(
                    x=resolution_data.median(),
                    line_dash="dash",
                    line_color="orange",
                    annotation_text=f"Median: {resolution_data.median():.1f}h"
                )
            else:
                resolution_fig = px.bar(x=[0], y=[0], title="No Resolution Data Available")
            
            # 7. Team Performance Chart
            team_stats = filtered_df.groupby('AssignedTo').agg({
                'TicketID': 'count',
                'ResolutionHours': 'mean'
            }).round(1).reset_index()
            team_stats.columns = ['Team Member', 'Total Tickets', 'Avg Resolution (hrs)']
            
            team_fig = px.scatter(
                team_stats,
                x='Total Tickets',
                y='Avg Resolution (hrs)',
                size='Total Tickets',
                hover_name='Team Member',
                title="Team Performance: Workload vs Resolution Time",
                color='Total Tickets',
                color_continuous_scale='viridis'
            )
            
            # 8. Day of Week Chart
            day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            day_counts = filtered_df['OpenedDayOfWeek'].value_counts().reindex(day_order, fill_value=0)
            
            day_fig = px.bar(
                x=day_counts.index,
                y=day_counts.values,
                title="Tickets by Day of Week",
                labels={'x': 'Day of Week', 'y': 'Number of Tickets'},
                color=day_counts.values,
                color_continuous_scale='blues'
            )
            day_fig.update_traces(texttemplate='%{y}', textposition='outside')
            
            # 9. Hour of Day Chart
            hour_counts = filtered_df['OpenedHour'].value_counts().sort_index()
            hour_fig = px.line(
                x=hour_counts.index,
                y=hour_counts.values,
                title="Tickets by Hour of Day",
                labels={'x': 'Hour of Day', 'y': 'Number of Tickets'},
                markers=True
            )
            hour_fig.update_traces(line_color='#fd7e14', line_width=3, marker_size=8)
            
            # 10. Product-Priority Heatmap
            pivot_table = pd.crosstab(filtered_df['Product'], filtered_df['Priority'])
            heatmap_fig = px.imshow(
                pivot_table.values,
                x=pivot_table.columns,
                y=pivot_table.index,
                title="Product vs Priority Heatmap",
                labels=dict(x="Priority", y="Product", color="Number of Tickets"),
                color_continuous_scale='reds',
                text_auto=True
            )
            
            # 11. Monthly Trends
            monthly_data = filtered_df.groupby([
                filtered_df['DateOpened'].dt.to_period('M'), 'Product'
            ]).size().unstack(fill_value=0)
            
            monthly_fig = go.Figure()
            for product in monthly_data.columns:
                monthly_fig.add_trace(go.Scatter(
                    x=monthly_data.index.astype(str),
                    y=monthly_data[product],
                    mode='lines+markers',
                    name=product,
                    line=dict(width=3),
                    marker=dict(size=8)
                ))
            
            monthly_fig.update_layout(
                title="Monthly Ticket Trends by Product",
                xaxis_title="Month",
                yaxis_title="Number of Tickets",
                hovermode='x unified'
            )
            
            return (kpi_cards, status_fig, product_fig, priority_fig, timeline_fig, 
                   issues_fig, resolution_fig, team_fig, day_fig, hour_fig, 
                   heatmap_fig, monthly_fig)
    
    def add_insights_tab(self):
        """Add insights and recommendations tab (optional enhancement)"""
        pass
    
    def run_server(self, debug=True, port=8050):
        """Run the Dash server"""
        print(f"Starting dashboard server...")
        print(f"Dashboard will be available at: http://localhost:{port}")
        print("Press Ctrl+C to stop the server")
        self.app.run(debug=debug, port=port)

# Usage Example:
if __name__ == "__main__":
    # Initialize interactive dashboard
    dashboard = InteractiveTicketDashboard('support_tickets_2500.csv')  # Replace with your CSV file path
    
    # Run the server
    dashboard.run_server(debug=True, port=8050)
    
    print("""
    🎯 Interactive Dashboard Features:
    
    📊 Real-time Filtering:
    • Filter by Product, Priority, Status
    • Date range selection
    • All charts update dynamically
    
    🎨 Interactive Visualizations:
    • Hover for detailed information
    • Zoom and pan capabilities
    • Click legends to show/hide data
    
    📈 Key Metrics Dashboard:
    • KPI cards with live updates
    • 12 interactive charts
    • Team performance analysis
    • Time pattern insights
    
    🔧 Usage:
    1. Open http://localhost:8050 in your browser
    2. Use filters to explore different data segments
    3. Hover over charts for detailed tooltips
    4. Click and drag to zoom into specific time periods
    
    💡 Pro Tips:
    • Double-click chart legends to isolate data series
    • Use date picker for custom time ranges
    • Combine multiple filters for deep analysis
    """)