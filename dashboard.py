import dash
from dash import dcc, html, Input, Output, callback
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import dash_bootstrap_components as dbc

# Load data
visits = pd.read_csv('/Users/nangosyah/Documents/puurs-hospital/data/patient_visits.csv')
referrals = pd.read_csv('/Users/nangosyah/Documents/puurs-hospital/data/referrals.csv')
hours = pd.read_csv('/Users/nangosyah/Documents/puurs-hospital/data/staff_hours.csv')

# Convert date columns to datetime
visits['date'] = pd.to_datetime(visits['date'])
referrals['date'] = pd.to_datetime(referrals['date'])

# Get available months for the dropdown
visits['year_month'] = visits['date'].dt.to_period('M').astype(str)
available_months = sorted(visits['year_month'].unique())

# Initialize the Dash app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# Define colors
colors = {
    'background': '#111111',
    'text': '#FFFFFF',
    'card_bg': '#1e1e1e',
    'primary': '#00cc96',
    'secondary': '#636efa',
    'success': '#00d4aa',
    'warning': '#ffa500',
    'danger': '#ff6692'
}

def filter_data_by_date(selected_month, day_range):
    """Filter data based on selected month and day range"""
    # Filter by month
    month_data = visits[visits['year_month'] == selected_month].copy()
    
    if len(month_data) == 0:
        return month_data, pd.DataFrame(), pd.DataFrame()
    
    # Get the days in the selected range
    month_data['day'] = month_data['date'].dt.day
    filtered_data = month_data[
        (month_data['day'] >= day_range[0]) & 
        (month_data['day'] <= day_range[1])
    ]
    
    # Filter related data
    filtered_visit_ids = filtered_data['visit_id'].tolist()
    filtered_referrals = referrals[referrals['visit_id'].isin(filtered_visit_ids)]
    
    # For hours data, filter by the same month (assuming year-week structure)
    year = int(selected_month.split('-')[0])
    month = int(selected_month.split('-')[1])
    filtered_hours = hours[hours['year'] == year]
    
    return filtered_data, filtered_referrals, filtered_hours

# Layout
app.layout = dbc.Container([
    # Title Panel
    dbc.Row([
        dbc.Col([
            html.Div([
                # Left side - Hospital Title
                html.Div([
                    html.H1("Puurs Hospital Emergency Department", 
                           style={'color': colors['text'], 'margin': '0', 'font-weight': 'bold'}),
                    html.Br(),
                    html.H3("Emergency Services Report Overview", 
                           style={'color': colors['text'], 'margin': '0', 'font-weight': '300'})
                ], style={'display': 'inline-block', 'vertical-align': 'top'}),
                
                # Right side - User Info
                html.Div([
                    html.Div([
                        html.I(className="fas fa-user-md", 
                              style={'color': colors['success'], 'margin-right': '10px', 'font-size': '20px'}),
                        html.Span("Welcome, Dr. Sarah Johnson", 
                                 style={'color': colors['text'], 'font-size': '18px', 'font-weight': 'bold'})
                    ]),
                    html.Div([
                        html.Span("Head of Emergency Department", 
                                 style={'color': colors['text'], 'font-size': '14px'}),
                        html.I(className="fas fa-circle", 
                              style={'color': colors['success'], 'margin-left': '10px', 'font-size': '8px'})
                    ], style={'margin-top': '5px'}),
                    
                    # Date Controls
                    html.Div([
                        html.Div([
                            html.Strong("Selected Month: ", style={'color': colors['text']}),
                            html.Strong(id='selected-month-display', 
                                      style={'color': colors['primary']})
                        ], style={'margin-bottom': '10px'}),
                        
                        dcc.Dropdown(
                            id='month-dropdown',
                            options=[{'label': month, 'value': month} for month in available_months],
                            value=available_months[-1],
                            style={'margin-bottom': '10px', 'width': '200px'}
                        ),
                        
                        html.Div([
                            html.Label("Days Range:", style={'color': colors['text'], 'margin-right': '10px'}),
                            dcc.RangeSlider(
                                id='day-range-slider',
                                min=1, max=31, step=1,
                                value=[1, 31],
                                marks={i: str(i) for i in range(1, 32, 5)},
                                tooltip={"placement": "bottom", "always_visible": True}
                            )
                        ], style={'width': '300px'})
                    ], style={'margin-top': '20px'})
                ], style={'float': 'right', 'text-align': 'right'})
            ], style={
                'padding': '20px',
                'background-color': colors['background'],
                'border-radius': '10px',
                'margin-bottom': '20px'
            })
        ], width=12)
    ]),
    
    # Main Dashboard Cards
    dbc.Row([
        # Card 1: Department Input Metrics
        dbc.Col([
            dbc.Card([
                dbc.CardHeader([
                    html.H4("Department Input Metrics", className="card-title text-primary")
                ]),
                dbc.CardBody([
                    html.Div(id="staff-summary"),
                    dcc.Graph(id="doctor-hours-chart")
                ])
            ], style={'height': '500px', 'background-color': colors['card_bg']})
        ], width=3),
        
        # Card 2: Processing Time Metrics
        dbc.Col([
            dbc.Card([
                dbc.CardHeader([
                    html.H4("Processing Time Metrics", className="card-title text-info")
                ]),
                dbc.CardBody([
                    dcc.Graph(id="processing-time-chart")
                ])
            ], style={'height': '500px', 'background-color': colors['card_bg']})
        ], width=3),
        
        # Card 3: Department Output Metrics
        dbc.Col([
            dbc.Card([
                dbc.CardHeader([
                    html.H4("Department Output Metrics", className="card-title text-success")
                ]),
                dbc.CardBody([
                    dcc.Graph(id="output-metrics-chart")
                ])
            ], style={'height': '500px', 'background-color': colors['card_bg']})
        ], width=3),
        
        # Card 4: Resource Utilisation Metrics
        dbc.Col([
            dbc.Card([
                dbc.CardHeader([
                    html.H4("Resource Utilisation", className="card-title text-warning")
                ]),
                dbc.CardBody([
                    dcc.Graph(id="resource-utilization-chart")
                ])
            ], style={'height': '500px', 'background-color': colors['card_bg']})
        ], width=3)
    ])
], fluid=True, style={'background-color': '#f8f9fa'})

# Callbacks
@callback(
    Output('selected-month-display', 'children'),
    Input('month-dropdown', 'value')
)
def update_month_display(selected_month):
    return selected_month

@callback(
    [Output('staff-summary', 'children'),
     Output('doctor-hours-chart', 'figure')],
    [Input('month-dropdown', 'value'),
     Input('day-range-slider', 'value')]
)
def update_staff_metrics(selected_month, day_range):
    filtered_data, filtered_referrals, filtered_hours = filter_data_by_date(selected_month, day_range)
    
    if len(filtered_hours) == 0:
        # Use all hours data if no filtered data
        filtered_hours = hours
    
    # Staff summary
    total_staff = filtered_hours['staff_name'].nunique()
    doctor_roles = ['Consultant', 'Registrar', 'Medical Officer']
    total_doctors = filtered_hours[filtered_hours['role'].isin(doctor_roles)]['staff_name'].nunique()
    total_doctor_hours = filtered_hours[filtered_hours['role'].isin(doctor_roles)]['hours_worked'].sum()
    
    # Staff by department/specialty
    staff_by_specialty = filtered_hours.groupby('specialty')['staff_name'].nunique()
    
    summary_text = html.Div([
        html.P(f"Total Staff: {total_staff}", style={'color': colors['text'], 'font-size': '14px'}),
        html.P(f"Doctors: {total_doctors}", style={'color': colors['text'], 'font-size': '14px'}),
        html.P(f"Total Doctor Hours: {total_doctor_hours:,}", style={'color': colors['primary'], 'font-size': '16px', 'font-weight': 'bold'}),
        html.Hr(),
        html.P("Staff by Specialty:", style={'color': colors['text'], 'font-size': '12px', 'font-weight': 'bold'}),
        html.Div([
            html.P(f"{specialty}: {count}", style={'color': colors['text'], 'font-size': '10px'})
            for specialty, count in staff_by_specialty.items()
        ])
    ])
    
    # Doctor hours chart
    doctor_hours_by_role = filtered_hours[filtered_hours['role'].isin(doctor_roles)].groupby('role')['hours_worked'].sum().sort_values()
    
    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=doctor_hours_by_role.index,
        x=doctor_hours_by_role.values,
        orientation='h',
        marker_color=colors['primary']
    ))
    
    fig.update_layout(
        title="Doctor Hours by Role",
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color=colors['text'], size=10),
        height=200,
        margin=dict(l=80, r=10, t=30, b=10)
    )
    
    return summary_text, fig

@callback(
    Output('processing-time-chart', 'figure'),
    [Input('month-dropdown', 'value'),
     Input('day-range-slider', 'value')]
)
def update_processing_metrics(selected_month, day_range):
    filtered_data, _, _ = filter_data_by_date(selected_month, day_range)
    
    if len(filtered_data) == 0:
        filtered_data = visits
    
    # Create subplots
    fig = make_subplots(
        rows=3, cols=1,
        subplot_titles=("Door to Doctor Time", "Wait Times by ESI Level", "Service Requirements %"),
        specs=[[{"secondary_y": False}],
               [{"secondary_y": False}],
               [{"type": "domain"}]],
        vertical_spacing=0.15
    )
    
    # Door to Doctor Time
    avg_door_to_doctor = filtered_data['door_to_doctor_mins'].mean()
    fig.add_trace(go.Indicator(
        mode="number+gauge",
        value=avg_door_to_doctor,
        title={"text": f"Avg: {avg_door_to_doctor:.1f} min"},
        gauge={'axis': {'range': [None, 300]},
               'bar': {'color': colors['secondary']},
               'bgcolor': "white",
               'borderwidth': 2,
               'bordercolor': "gray"},
        domain={'row': 0, 'column': 0}
    ), row=1, col=1)
    
    # Wait times by ESI
    esi_wait_times = filtered_data.groupby('esi_level')['door_to_doctor_mins'].mean()
    fig.add_trace(go.Bar(
        x=[f"ESI {level}" for level in esi_wait_times.index],
        y=esi_wait_times.values,
        marker_color=colors['warning'],
        name="Wait Time"
    ), row=2, col=1)
    
    # Service requirements
    total_patients = len(filtered_data)
    services = {
        'Labs': (filtered_data['needs_labs'].sum() / total_patients) * 100,
        'Imaging': (filtered_data['needs_imaging'].sum() / total_patients) * 100,
        'Consults': (filtered_data['needs_consult'].sum() / total_patients) * 100
    }
    
    fig.add_trace(go.Pie(
        labels=list(services.keys()),
        values=list(services.values()),
        hole=0.4,
        marker_colors=[colors['primary'], colors['secondary'], colors['success']]
    ), row=3, col=1)
    
    fig.update_layout(
        height=450,
        showlegend=False,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color=colors['text'], size=9),
        margin=dict(l=10, r=10, t=40, b=10)
    )
    
    return fig

@callback(
    Output('output-metrics-chart', 'figure'),
    [Input('month-dropdown', 'value'),
     Input('day-range-slider', 'value')]
)
def update_output_metrics(selected_month, day_range):
    filtered_data, _, _ = filter_data_by_date(selected_month, day_range)
    
    if len(filtered_data) == 0:
        filtered_data = visits
    
    # Create subplots
    fig = make_subplots(
        rows=3, cols=1,
        subplot_titles=("Patient Outcomes", "Top Diagnoses", "Casualty Rate"),
        vertical_spacing=0.2
    )
    
    # Patient outcomes
    outcomes = filtered_data['outcome'].value_counts()
    fig.add_trace(go.Bar(
        x=outcomes.index,
        y=outcomes.values,
        marker_color=[colors['success'], colors['warning'], colors['danger']],
        name="Outcomes"
    ), row=1, col=1)
    
    # Top diagnoses
    top_diagnoses = filtered_data['diagnosis'].value_counts().head(5)
    fig.add_trace(go.Bar(
        x=top_diagnoses.values,
        y=top_diagnoses.index,
        orientation='h',
        marker_color=colors['secondary'],
        name="Diagnoses"
    ), row=2, col=1)
    
    # Casualty rate (admitted + LWBS)
    casualty_rate = (filtered_data['outcome'].isin(['Admitted', 'LWBS']).sum() / len(filtered_data)) * 100
    fig.add_trace(go.Indicator(
        mode="gauge+number",
        value=casualty_rate,
        title={"text": "Casualty Rate %"},
        gauge={'axis': {'range': [None, 100]},
               'bar': {'color': colors['danger']},
               'bgcolor': "white",
               'borderwidth': 2,
               'bordercolor': "gray",
               'steps': [
                   {'range': [0, 30], 'color': "lightgray"},
                   {'range': [30, 70], 'color': "yellow"}],
               'threshold': {'line': {'color': "red", 'width': 4},
                           'thickness': 0.75, 'value': 90}},
        domain={'row': 2, 'column': 0}
    ), row=3, col=1)
    
    fig.update_layout(
        height=450,
        showlegend=False,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color=colors['text'], size=9),
        margin=dict(l=10, r=10, t=40, b=10)
    )
    
    return fig

@callback(
    Output('resource-utilization-chart', 'figure'),
    [Input('month-dropdown', 'value'),
     Input('day-range-slider', 'value')]
)
def update_resource_metrics(selected_month, day_range):
    filtered_data, _, _ = filter_data_by_date(selected_month, day_range)
    
    if len(filtered_data) == 0:
        filtered_data = visits
    
    # Create subplots
    fig = make_subplots(
        rows=3, cols=1,
        subplot_titles=("LWBS Rate", "Length of Stay (Hours)", "Insurance Types"),
        specs=[[{"secondary_y": False}],
               [{"secondary_y": False}],
               [{"type": "domain"}]],
        vertical_spacing=0.2
    )
    
    # LWBS Rate
    lwbs_rate = (filtered_data['lwbs'].sum() / len(filtered_data)) * 100
    fig.add_trace(go.Indicator(
        mode="number+gauge",
        value=lwbs_rate,
        title={"text": f"LWBS Rate: {lwbs_rate:.2f}%"},
        gauge={'axis': {'range': [None, 10]},
               'bar': {'color': colors['danger']},
               'bgcolor': "white",
               'borderwidth': 2,
               'bordercolor': "gray"},
        domain={'row': 0, 'column': 0}
    ), row=1, col=1)
    
    # Length of Stay
    avg_los_hours = filtered_data['length_of_stay_mins'].mean() / 60
    los_by_outcome = filtered_data.groupby('outcome')['length_of_stay_mins'].mean() / 60
    
    fig.add_trace(go.Bar(
        x=los_by_outcome.index,
        y=los_by_outcome.values,
        marker_color=colors['success'],
        name="Avg LOS (Hours)"
    ), row=2, col=1)
    
    # Insurance Types
    insurance_counts = filtered_data['insurance_type'].value_counts(dropna=False)
    insurance_labels = ['Private' if not pd.isna(label) and label == 'Private'
                       else 'Public' if not pd.isna(label) and label == 'Public'
                       else 'Self-Pay/Other' for label in insurance_counts.index]
    
    fig.add_trace(go.Pie(
        labels=insurance_labels,
        values=insurance_counts.values,
        hole=0.4,
        marker_colors=[colors['primary'], colors['secondary'], colors['warning']]
    ), row=3, col=1)
    
    fig.update_layout(
        height=450,
        showlegend=False,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color=colors['text'], size=9),
        margin=dict(l=10, r=10, t=40, b=10)
    )
    
    return fig

if __name__ == '__main__':
    app.run_server(debug=True, host='0.0.0.0', port=8050)