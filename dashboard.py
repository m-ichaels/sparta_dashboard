import dash
from dash import dcc, html, Input, Output
import pandas as pd
import plotly.express as px
from datetime import datetime

# Load data from CSV
def load_data():
    # Read the CSV
    df = pd.read_csv("Netflix User Data.csv")
    
    # Convert date columns to datetime format
    df['Join Date'] = pd.to_datetime(df['Join Date'], format='%d/%m/%Y')
    df['Last Payment Date'] = pd.to_datetime(df['Last Payment Date'], format='%d/%m/%Y')
    
    return df

# Load the data
df = load_data()

# Initialize app
app = dash.Dash(__name__)

# Create layout
app.layout = html.Div([
    html.H1("Subscription Dashboard", style={'textAlign': 'center', 'color': '#2c3e50', 'marginBottom': 30}),
    
    html.Div([
        html.Div([
            html.Label("Country", style={'fontWeight': 'bold'}),
            dcc.Dropdown(
                id='country-filter',
                options=[{'label': country, 'value': country} for country in sorted(df["Country"].unique())],
                multi=True,
                placeholder="Select Countries"
            ),
        ], className='filter-item', style={'width': '24%', 'display': 'inline-block', 'padding': '0 10px'}),
        
        html.Div([
            html.Label("Subscription Type", style={'fontWeight': 'bold'}),
            dcc.Dropdown(
                id='type-filter',
                options=[{'label': sub_type, 'value': sub_type} for sub_type in sorted(df["Subscription Type"].unique())],
                multi=True,
                placeholder="Select Subscription Types"
            ),
        ], className='filter-item', style={'width': '24%', 'display': 'inline-block', 'padding': '0 10px'}),
        
        html.Div([
            html.Label("Device", style={'fontWeight': 'bold'}),
            dcc.Dropdown(
                id='device-filter',
                options=[{'label': device, 'value': device} for device in sorted(df["Device"].unique())],
                multi=True,
                placeholder="Select Devices"
            ),
        ], className='filter-item', style={'width': '24%', 'display': 'inline-block', 'padding': '0 10px'}),
        
        html.Div([
            html.Label("Gender", style={'fontWeight': 'bold'}),
            dcc.Dropdown(
                id='gender-filter',
                options=[{'label': gender, 'value': gender} for gender in sorted(df["Gender"].unique())],
                multi=True,
                placeholder="Select Genders"
            ),
        ], className='filter-item', style={'width': '24%', 'display': 'inline-block', 'padding': '0 10px'}),
    ], style={'marginBottom': 30, 'padding': '10px 20px', 'backgroundColor': '#f8f9fa', 'borderRadius': '5px'}),
    
    html.Div([
        html.Div([
            dcc.Graph(id='revenue-bar')
        ], style={'width': '50%', 'display': 'inline-block'}),
        
        html.Div([
            dcc.Graph(id='country-user-bar')
        ], style={'width': '50%', 'display': 'inline-block'}),
    ]),
    
    html.Div([
        html.Div([
            dcc.Graph(id='device-pie')
        ], style={'width': '33%', 'display': 'inline-block'}),
        
        html.Div([
            dcc.Graph(id='age-boxplot')
        ], style={'width': '33%', 'display': 'inline-block'}),
        
        html.Div([
            dcc.Graph(id='join-trend')
        ], style={'width': '33%', 'display': 'inline-block'}),
    ]),
    

], style={'padding': '20px', 'fontFamily': 'Arial'})

@app.callback(
    [Output('revenue-bar', 'figure'),
     Output('country-user-bar', 'figure'),
     Output('device-pie', 'figure'),
     Output('age-boxplot', 'figure'),
     Output('join-trend', 'figure')],
    [Input('country-filter', 'value'),
     Input('type-filter', 'value'),
     Input('device-filter', 'value'),
     Input('gender-filter', 'value')]
)
def update_graphs(selected_countries, selected_types, selected_devices, selected_genders):
    filtered = df.copy()
    
    # Apply filters only if values are selected
    if selected_countries and len(selected_countries) > 0:
        filtered = filtered[filtered["Country"].isin(selected_countries)]
    if selected_types and len(selected_types) > 0:
        filtered = filtered[filtered["Subscription Type"].isin(selected_types)]
    if selected_devices and len(selected_devices) > 0:
        filtered = filtered[filtered["Device"].isin(selected_devices)]
    if selected_genders and len(selected_genders) > 0:
        filtered = filtered[filtered["Gender"].isin(selected_genders)]

    # Figure 1: Revenue by Subscription Type
    revenue_by_type = filtered.groupby("Subscription Type")["Monthly Revenue"].sum().reset_index()
    # Sort by revenue for better visualization
    revenue_by_type = revenue_by_type.sort_values("Monthly Revenue", ascending=False)
    fig1 = px.bar(
        revenue_by_type,
        x="Subscription Type", 
        y="Monthly Revenue", 
        title="Revenue by Subscription Type",
        color="Subscription Type",
        color_discrete_sequence=px.colors.qualitative.G10,
        text_auto='.2s'
    )
    fig1.update_layout(xaxis_title="Subscription Type", yaxis_title="Monthly Revenue ($)")

    # Figure 2: User Count by Country
    country_counts = filtered["Country"].value_counts().reset_index()
    country_counts.columns = ["Country", "Count"]
    country_counts = country_counts.sort_values("Count", ascending=False)
    fig2 = px.bar(
        country_counts,
        x="Country", 
        y="Count", 
        title="User Count by Country",
        color="Country",
        color_discrete_sequence=px.colors.qualitative.Bold,
        text_auto=True
    )
    fig2.update_layout(xaxis_title="Country", yaxis_title="Number of Users")

    # Figure 3: Device Distribution
    fig3 = px.pie(
        filtered, 
        names="Device", 
        title="Device Distribution",
        hole=0.4,
        color_discrete_sequence=px.colors.qualitative.Pastel
    )
    fig3.update_traces(textposition='inside', textinfo='percent+label')

    # Figure 4: Age Distribution by Subscription Type
    fig4 = px.box(
        filtered, 
        x="Subscription Type", 
        y="Age", 
        title="Age Distribution by Subscription Type",
        color="Subscription Type",
        color_discrete_sequence=px.colors.qualitative.Safe
    )
    fig4.update_layout(xaxis_title="Subscription Type", yaxis_title="Age")

    # Figure 5: User Join Trend Over Time (improve with month bins)
    filtered['Join Month'] = filtered['Join Date'].dt.to_period('M')
    join_trend = filtered.groupby('Join Month').size().reset_index(name='Count')
    join_trend['Join Month'] = join_trend['Join Month'].astype(str)
    fig5 = px.line(
        join_trend,
        x="Join Month", 
        y="Count", 
        title="User Join Trend Over Time",
        markers=True
    )
    fig5.update_layout(xaxis_title="Month", yaxis_title="New Users", xaxis_tickangle=45)
    
    # Figure 6: Plan Duration Distribution
    plan_duration_counts = filtered["Plan Duration"].value_counts().reset_index()
    plan_duration_counts.columns = ["Plan Duration", "Count"]
    plan_duration_counts = plan_duration_counts.sort_values("Count", ascending=False)
    fig6 = px.bar(
        plan_duration_counts,
        x="Plan Duration", 
        y="Count", 
        title="Plan Duration Distribution",
        color="Plan Duration",
        color_discrete_sequence=px.colors.qualitative.Vivid,
        text_auto=True
    )
    fig6.update_layout(xaxis_title="Plan Duration", yaxis_title="Number of Users")

    return fig1, fig2, fig3, fig4, fig5

# custom CSS
app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>Subscription Dashboard</title>
        {%favicon%}
        {%css%}
        <style>
            body {
                background-color: #f5f7fa;
                margin: 0;
                padding: 0;
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

if __name__ == '__main__':
    app.run(debug=True)