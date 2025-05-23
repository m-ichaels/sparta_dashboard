import pandas as pd
import dash
from dash import dcc, html, Input, Output
import plotly.express as px

# Load and clean data
df = pd.read_csv("support_tickets_2500.csv", parse_dates=["DateOpened", "DateClosed"])
df["ResolutionTimeHours"] = (df["DateClosed"] - df["DateOpened"]).dt.total_seconds() / 3600
df["Status"] = df["Status"].fillna("Unknown")
df["AssignedTo"] = df["AssignedTo"].fillna("Unassigned")
df["Resolution"] = df["Resolution"].fillna("Unresolved")

# Initialize Dash app
app = dash.Dash(__name__)
app.title = "Support Tickets Dashboard"

# Custom CSS styling
app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>Support Tickets Dashboard</title>
        {%favicon%}
        {%css%}
        <style>
            body {
                background-color: #f5f7fa;
                margin: 0;
                padding: 0;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            .dash-graph {
                border-radius: 5px;
                box-shadow: 0 2px 5px rgba(0,0,0,0.1);
                background-color: white;
                padding: 15px;
                margin-bottom: 20px;
            }
            .filter-item {
                margin-bottom: 10px;
            }
            .Select-control {
                border-radius: 4px !important;
            }
            h1 {
                font-family: 'Segoe UI', Arial, sans-serif;
                color: #2c3e50;
                margin-bottom: 30px;
            }
            .filter-container {
                background-color: white;
                padding: 20px;
                border-radius: 5px;
                box-shadow: 0 2px 5px rgba(0,0,0,0.1);
                margin-bottom: 20px;
            }
            .filter-section {
                margin-bottom: 15px;
            }
            .filter-section label {
                font-weight: 600;
                color: #34495e;
                margin-bottom: 5px;
                display: block;
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
    html.H1("Support Tickets Dashboard", style={'textAlign': 'center'}),
    
    html.Div([
        html.Div([
            html.Label("Filter by Product", className="filter-section"),
            dcc.Dropdown(
                options=[{"label": prod, "value": prod} for prod in sorted(df["Product"].unique())],
                id="product-filter",
                multi=True,
                className="filter-item"
            )
        ], style={"width": "30%", "display": "inline-block", "padding": "10px"}),

        html.Div([
            html.Label("Filter by Priority", className="filter-section"),
            dcc.Dropdown(
                options=[{"label": p, "value": p} for p in sorted(df["Priority"].unique())],
                id="priority-filter",
                multi=True,
                className="filter-item"
            )
        ], style={"width": "30%", "display": "inline-block", "padding": "10px"}),

        html.Div([
            html.Label("Filter by Status", className="filter-section"),
            dcc.Dropdown(
                options=[{"label": s, "value": s} for s in sorted(df["Status"].unique())],
                id="status-filter",
                multi=True,
                className="filter-item"
            )
        ], style={"width": "30%", "display": "inline-block", "padding": "10px"}),
    ], className="filter-container"),

    html.Div([
        dcc.Graph(id="tickets-by-product", className="dash-graph"),
        dcc.Graph(id="tickets-by-priority", className="dash-graph"),
        dcc.Graph(id="status-over-time", className="dash-graph"),
        dcc.Graph(id="resolution-time", className="dash-graph")
    ], style={"padding": "0 20px"})
], style={"padding": "20px"})

# Callbacks
@app.callback(
    Output("tickets-by-product", "figure"),
    Output("tickets-by-priority", "figure"),
    Output("status-over-time", "figure"),
    Output("resolution-time", "figure"),
    Input("product-filter", "value"),
    Input("priority-filter", "value"),
    Input("status-filter", "value")
)
def update_graphs(selected_products, selected_priorities, selected_statuses):
    dff = df.copy()
    if selected_products:
        dff = dff[dff["Product"].isin(selected_products)]
    if selected_priorities:
        dff = dff[dff["Priority"].isin(selected_priorities)]
    if selected_statuses:
        dff = dff[dff["Status"].isin(selected_statuses)]

    # Create figures with consistent styling
    fig1 = px.histogram(dff, x="Product", title="Ticket Count by Product", color="Product")
    fig1.update_layout(plot_bgcolor='white', paper_bgcolor='white')
    
    fig2 = px.histogram(dff, x="Priority", title="Ticket Count by Priority", color="Priority")
    fig2.update_layout(plot_bgcolor='white', paper_bgcolor='white')
    
    fig3 = px.histogram(dff, x="DateOpened", title="Ticket Status Over Time", color="Status", nbins=30)
    fig3.update_layout(plot_bgcolor='white', paper_bgcolor='white')
    
    fig4 = px.box(dff.dropna(subset=["ResolutionTimeHours"]), x="Product", y="ResolutionTimeHours",
                  title="Resolution Time (Hours) by Product", color="Product")
    fig4.update_layout(plot_bgcolor='white', paper_bgcolor='white')

    return fig1, fig2, fig3, fig4

if __name__ == "__main__":
    app.run(debug=True)