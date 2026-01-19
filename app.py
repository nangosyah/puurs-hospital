import dash
from dash import dcc, html, Input, Output, callback
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
import dash_bootstrap_components as dbc

# Load data
visits = pd.read_csv('data/patient_visits.csv')
referrals = pd.read_csv('data/referrals.csv')
hours = pd.read_csv('data/staff_hours.csv')

# Convert date columns
visits['date'] = pd.to_datetime(visits['date'])
visits['year_month'] = visits['date'].dt.to_period('M').astype(str)
available_months = sorted(visits['year_month'].unique())

# Create month display mapping
month_mapping = {}
for month_str in available_months:
    year, month = month_str.split('-')
    month_names = ['January', 'February', 'March', 'April', 'May', 'June',
                   'July', 'August', 'September', 'October', 'November', 'December']
    month_name = f"{month_names[int(month)-1]} {year}"
    month_mapping[month_str] = month_name

# Get days in month function
def get_days_in_month(year_month_str):
    year, month = map(int, year_month_str.split('-'))
    if month in [1, 3, 5, 7, 8, 10, 12]:
        return 31
    elif month in [4, 6, 9, 11]:
        return 30
    elif month == 2:
        if (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0):
            return 29
        return 28

# Initialize app with external stylesheets including Font Awesome and Google Fonts
external_stylesheets = [
    dbc.themes.BOOTSTRAP,
    "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css",
    "https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700&display=swap"
]

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

# Color scheme
colors = {
    'bg_dark': '#1a1a1a',
    'text_white': '#ffffff',
    'text_light': '#cccccc',
    'primary': '#00cc96',
    'secondary': '#636efa', 
    'success': '#28a745',
    'warning': '#ffc107',
    'danger': '#dc3545',
    'card_bg': '#2d3748'
}

def filter_data_by_date(selected_month, day_range):
    """Filter data based on month and day range"""
    month_data = visits[visits['year_month'] == selected_month].copy()
    
    if len(month_data) == 0:
        return visits.head(100), pd.DataFrame(), hours  # Return sample if no data
    
    month_data['day'] = month_data['date'].dt.day
    filtered_data = month_data[
        (month_data['day'] >= day_range[0]) & 
        (month_data['day'] <= day_range[1])
    ]
    
    filtered_visit_ids = filtered_data['visit_id'].tolist() if len(filtered_data) > 0 else []
    filtered_referrals = referrals[referrals['visit_id'].isin(filtered_visit_ids)]
    
    return filtered_data, filtered_referrals, hours

# Define inline styles with Roboto font and readable sizes
title_panel_style = {
    'background-color': '#1a1a1a',
    'padding': '20px',
    'border-radius': '10px',
    'margin-bottom': '20px',
    'font-family': 'Roboto, sans-serif'
}

card_style = {
    'background-color': '#2d3748',
    'border-radius': '10px',
    'height': '600px',
    'margin-bottom': '20px',
    'box-shadow': '0 4px 6px rgba(0, 0, 0, 0.1)',
    'font-family': 'Roboto, sans-serif'
}

card_header_style = {
    'background-color': '#4a5568',
    'color': 'white',
    'padding': '12px',
    'border-radius': '10px 10px 0 0',
    'font-weight': '500',
    'font-size': '16px',
    'font-family': 'Roboto, sans-serif'
}

metric_value_style = {
    'font-size': '20px',
    'font-weight': '700',
    'color': '#00cc96',
    'font-family': 'Roboto, sans-serif'
}

metric_label_style = {
    'font-size': '11px',
    'color': '#cccccc',
    'margin-bottom': '8px',
    'font-family': 'Roboto, sans-serif',
    'font-weight': '400'
}

app.layout = html.Div([
    
    dbc.Container([
        # Title Panel
        html.Div([
            dbc.Row([
                # Left side - Hospital info
                dbc.Col([
                    html.H1("Puurs Hospital Emergency Department", 
                           style={'color': colors['text_white'], 'margin-bottom': '10px', 'font-weight': '700', 
                                 'font-family': 'Roboto, sans-serif', 'font-size': '24px'}),
                    html.H4("Emergency Services Report Overview", 
                           style={'color': colors['text_light'], 'font-weight': '300', 
                                 'font-family': 'Roboto, sans-serif', 'font-size': '16px'})
                ], md=6),
                
                # Right side - User info and controls
                dbc.Col([
                    # User info
                    html.Div([
                        html.I(className="fas fa-user-md", 
                              style={'color': colors['success'], 'margin-right': '8px', 'font-size': '18px'}),
                        html.Span("Welcome, Dr. Sarah Johnson", 
                                 style={'color': colors['text_white'], 'font-size': '14px', 'font-weight': '500',
                                       'font-family': 'Roboto, sans-serif'})
                    ], style={'margin-bottom': '5px'}),
                    
                    html.Div([
                        html.Span("Head of Emergency Department ", 
                                 style={'color': colors['text_light'], 'font-size': '12px',
                                       'font-family': 'Roboto, sans-serif', 'font-weight': '400'}),
                        html.I(className="fas fa-circle", 
                              style={'color': colors['success'], 'font-size': '8px', 'margin-left': '8px'})
                    ], style={'margin-bottom': '15px'}),
                    
                    # Date controls
                    html.Div([
                        html.Div([
                            html.Strong("Selected Month: ", style={'color': colors['text_white'], 'margin-right': '10px',
                                                                          'font-family': 'Roboto, sans-serif', 'font-size': '13px'}),
                            html.Strong(id='month-display', style={'color': colors['primary'], 'font-family': 'Roboto, sans-serif', 'font-size': '13px'})
                        ], style={'margin-bottom': '15px'}),
                        
                        # Month and Day controls on same line
                        dbc.Row([
                            dbc.Col([
                                html.Label("Month:", style={'color': colors['text_white'], 'margin-bottom': '5px',
                                                          'font-family': 'Roboto, sans-serif', 'font-size': '12px'}),
                                dcc.Dropdown(
                                    id='month-selector',
                                    options=[{'label': month_mapping[month], 'value': month} for month in available_months],
                                    value=available_months[-1],
                                    style={'color': '#000', 'margin-bottom': '10px'},
                                    clearable=False
                                )
                            ], md=5),
                            
                            dbc.Col([
                                html.Label("Day Range:", style={'color': colors['text_white'], 'margin-bottom': '5px',
                                                              'font-family': 'Roboto, sans-serif', 'font-size': '12px'}),
                                dcc.RangeSlider(
                                    id='day-slider',
                                    min=1, max=31, step=1,
                                    value=[1, 31],
                                    marks={i: {'label': str(i), 'style': {'color': colors['text_light'], 'fontSize': '10px'}} 
                                          for i in range(1, 32, 5)},
                                    tooltip={"placement": "bottom", "always_visible": True}
                                )
                            ], md=7),
                        ])
                    ])
                ], md=6, style={'text-align': 'right'})
            ])
        ], style=title_panel_style),
        
        # Main Dashboard Cards
        dbc.Row([
            # Card 1: Staff Metrics
            dbc.Col([
                html.Div([
                    html.Div([
                        html.I(className="fas fa-users", style={'margin-right': '8px'}),
                        "Department Input Metrics"
                    ], style=card_header_style),
                    
                    html.Div([
                        html.Div(id="staff-summary-content"),
                        dcc.Graph(id="staff-chart", style={'height': '400px'})
                    ], style={'padding': '15px'})
                ], style=card_style)
            ], md=3),
            
            # Card 2: Processing Metrics
            dbc.Col([
                html.Div([
                    html.Div([
                        html.I(className="fas fa-clock", style={'margin-right': '8px'}),
                        "Processing Time Metrics"
                    ], style=card_header_style),
                    
                    html.Div([
                        dcc.Graph(id="processing-chart", style={'height': '500px'})
                    ], style={'padding': '15px'})
                ], style=card_style)
            ], md=3),
            
            # Card 3: Output Metrics
            dbc.Col([
                html.Div([
                    html.Div([
                        html.I(className="fas fa-chart-line", style={'margin-right': '8px'}),
                        "Department Output Metrics"
                    ], style=card_header_style),
                    
                    html.Div([
                        dcc.Graph(id="output-chart", style={'height': '500px'})
                    ], style={'padding': '15px'})
                ], style=card_style)
            ], md=3),
            
            # Card 4: Resource Utilization
            dbc.Col([
                html.Div([
                    html.Div([
                        html.I(className="fas fa-chart-pie", style={'margin-right': '8px'}),
                        "Resource Utilisation"
                    ], style=card_header_style),
                    
                    html.Div([
                        dcc.Graph(id="resource-chart", style={'height': '500px'})
                    ], style={'padding': '15px'})
                ], style=card_style)
            ], md=3)
        ])
    ], fluid=True)
], style={'background-color': '#f8f9fa', 'min-height': '100vh', 'padding': '20px'})

# Callbacks
@callback(
    [Output('month-display', 'children'),
     Output('day-slider', 'max'),
     Output('day-slider', 'marks'),
     Output('day-slider', 'value')],
    Input('month-selector', 'value')
)
def update_month_display(selected_month):
    if selected_month is None:
        return "No month selected", 31, {}, [1, 31]
    
    # Get month name
    month_name = month_mapping.get(selected_month, selected_month)
    
    # Get days in the selected month
    days_in_month = get_days_in_month(selected_month)
    
    # Create marks for the slider
    marks = {i: {'label': str(i), 'style': {'color': colors['text_light'], 'fontSize': '10px'}} 
             for i in range(1, days_in_month + 1, 5)}
    marks[1] = {'label': '1', 'style': {'color': colors['text_light'], 'fontSize': '10px'}}
    marks[days_in_month] = {'label': str(days_in_month), 'style': {'color': colors['text_light'], 'fontSize': '10px'}}
    
    return month_name, days_in_month, marks, [1, days_in_month]

@callback(
    [Output('staff-summary-content', 'children'),
     Output('staff-chart', 'figure')],
    [Input('month-selector', 'value'),
     Input('day-slider', 'value')]
)
def update_staff_card(selected_month, day_range):
    filtered_visits, _, filtered_hours = filter_data_by_date(selected_month, day_range)
    
    # Get staff counts by role
    staff_counts = filtered_hours.groupby('role').size()
    total_staff = filtered_hours['staff_name'].nunique()
    
    # Get individual doctor data for the bar chart
    doctor_roles = ['Consultant', 'Registrar', 'Medical Officer']
    doctor_hours = filtered_hours[filtered_hours['role'].isin(doctor_roles)]
    total_doctor_hours = doctor_hours['hours_worked'].sum()
    
    # Top 5 individual doctor hours (sorted in ascending order for better visualization)
    individual_doctors = doctor_hours.groupby('staff_name')['hours_worked'].sum().sort_values(ascending=False).head(5).sort_values(ascending=True)
    
    # Staff summary content
    summary = html.Div([
        html.Div([
            html.H5("Staffing", style={'color': colors['text_white'], 'margin-bottom': '10px',
                                          'font-family': 'Roboto, sans-serif', 'font-size': '16px', 'font-weight': '500'}),
            html.P([
                f"All Staff: {total_staff}",
                html.Br(),
                f"• Consultants: {staff_counts.get('Consultant', 0)}",
                html.Br(),
                f"• Registrars: {staff_counts.get('Registrar', 0)}",
                html.Br(),
                f"• Medical Officers: {staff_counts.get('Medical Officer', 0)}",
                html.Br(),
                f"• Nurses: {staff_counts.get('Nurse', 0)}"
            ], style={'color': colors['text_light'], 'font-size': '13px', 'margin-bottom': '15px',
                     'font-family': 'Roboto, sans-serif', 'font-weight': '400'}),
            
            html.H6(f"Total hours worked: {total_doctor_hours:,}", 
                   style={'color': colors['primary'], 'margin-bottom': '10px', 'font-size': '14px',
                         'font-family': 'Roboto, sans-serif', 'font-weight': '500'})
        ], style={'padding': '10px'})
    ])
    
    # Chart - Top 10 doctors by hours worked (ascending order for visualization)
    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=[f"Dr. {name.split()[-1]}" for name in individual_doctors.index],  # Use last name
        x=individual_doctors.values,
        orientation='h',
        marker_color=colors['primary'],
        text=[f"{int(hours)}h" for hours in individual_doctors.values],
        textposition='outside'
    ))
    
    fig.update_layout(
        title="Top 5 Doctors by Hours Worked",
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color=colors['text_white'], size=11, family="Roboto, sans-serif"),
        height=300,
        margin=dict(l=80, r=40, t=40, b=20),
        xaxis=dict(title="Hours Worked"),
        title_font=dict(size=14, family="Roboto, sans-serif")
    )
    
    return summary, fig

@callback(
    Output('processing-chart', 'figure'),
    [Input('month-selector', 'value'),
     Input('day-slider', 'value')]
)
def update_processing_card(selected_month, day_range):
    filtered_visits, _, _ = filter_data_by_date(selected_month, day_range)
    
    if len(filtered_visits) == 0:
        filtered_visits = visits.head(1000)
    
    # Create subplots
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=["Door to Doctor Time", "ESI Wait Times", "Service Needs", "Processing Trend"],
        specs=[[{"type": "indicator"}, {"type": "bar"}],
               [{"type": "domain"}, {"type": "scatter"}]]
    )
    
    # Door to doctor indicator
    avg_door_to_doctor = filtered_visits['door_to_doctor_mins'].mean()
    fig.add_trace(go.Indicator(
        mode="number",
        value=avg_door_to_doctor,
        number={"suffix": " min", "font": {"color": colors['primary']}},
        title={"text": "Average"}
    ), row=1, col=1)
    
    # ESI wait times
    esi_times = filtered_visits.groupby('esi_level')['door_to_doctor_mins'].mean()
    fig.add_trace(go.Bar(
        x=[f"ESI {i}" for i in esi_times.index],
        y=esi_times.values,
        marker_color=colors['secondary']
    ), row=1, col=2)
    
    # Service needs pie chart with proper labels
    total_patients = len(filtered_visits)
    services = {
        'Labs Required': (filtered_visits['needs_labs'].sum() / total_patients) * 100,
        'Imaging Required': (filtered_visits['needs_imaging'].sum() / total_patients) * 100,
        'Consultations Required': (filtered_visits['needs_consult'].sum() / total_patients) * 100
    }
    
    fig.add_trace(go.Pie(
        labels=list(services.keys()),
        values=list(services.values()),
        marker_colors=[colors['primary'], colors['secondary'], colors['success']],
        textinfo='label+percent',
        textposition='auto'
    ), row=2, col=1)
    
    # Daily trend
    daily_avg = filtered_visits.groupby(filtered_visits['date'].dt.day)['door_to_doctor_mins'].mean()
    fig.add_trace(go.Scatter(
        x=daily_avg.index,
        y=daily_avg.values,
        mode='lines+markers',
        marker_color=colors['warning'],
        line=dict(width=2)
    ), row=2, col=2)
    
    fig.update_layout(
        height=500,
        showlegend=False,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color=colors['text_white'], size=10, family="Roboto, sans-serif"),
        margin=dict(l=10, r=10, t=40, b=10)
    )
    
    return fig

@callback(
    Output('output-chart', 'figure'),
    [Input('month-selector', 'value'),
     Input('day-slider', 'value')]
)
def update_output_card(selected_month, day_range):
    filtered_visits, _, _ = filter_data_by_date(selected_month, day_range)
    
    if len(filtered_visits) == 0:
        filtered_visits = visits.head(1000)
    
    # Create subplots with better spacing
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=["Patient Outcomes", "Top Diagnoses", "Department Stats", "Casualty Trend"],
        specs=[[{"type": "bar"}, {"type": "bar"}],
               [{"type": "bar"}, {"type": "indicator"}]],
        vertical_spacing=0.12,
        horizontal_spacing=0.08
    )
    
    # Patient outcomes
    outcomes = filtered_visits['outcome'].value_counts()
    fig.add_trace(go.Bar(
        x=outcomes.index,
        y=outcomes.values,
        marker_color=[colors['success'], colors['warning'], colors['danger']],
    ), row=1, col=1)
    
    # Top diagnoses
    top_diagnoses = filtered_visits['diagnosis'].value_counts().head(4)
    fig.add_trace(go.Bar(
        y=[diag[:15] + "..." if len(diag) > 15 else diag for diag in top_diagnoses.index],
        x=top_diagnoses.values,
        orientation='h',
        marker_color=colors['secondary']
    ), row=1, col=2)
    
    # Department visits
    dept_counts = filtered_visits['department'].value_counts().head(5)
    fig.add_trace(go.Bar(
        y=[dept[:12] + "..." if len(dept) > 12 else dept for dept in dept_counts.index],
        x=dept_counts.values,
        orientation='h',
        marker_color=colors['primary']
    ), row=2, col=1)
    
    # Casualty rate indicator
    casualty_rate = (filtered_visits['outcome'].isin(['Admitted', 'LWBS']).sum() / len(filtered_visits)) * 100
    fig.add_trace(go.Indicator(
        mode="gauge+number",
        value=casualty_rate,
        number={"suffix": "%"},
        gauge={'axis': {'range': [None, 100]},
               'bar': {'color': colors['danger']},
               'steps': [{'range': [0, 50], 'color': "lightgray"},
                        {'range': [50, 80], 'color': "yellow"}]},
        title={"text": "Casualty Rate"}
    ), row=2, col=2)
    
    fig.update_layout(
        height=500,
        showlegend=False,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color=colors['text_white'], size=10, family="Roboto, sans-serif"),
        margin=dict(l=10, r=10, t=40, b=10)
    )
    
    return fig

@callback(
    Output('resource-chart', 'figure'),
    [Input('month-selector', 'value'),
     Input('day-slider', 'value')]
)
def update_resource_card(selected_month, day_range):
    filtered_visits, _, _ = filter_data_by_date(selected_month, day_range)
    
    if len(filtered_visits) == 0:
        filtered_visits = visits.head(1000)
    
    # Create subplots
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=["Left Without Being Seen Rate", "Length of Stay", "Insurance Types", "Resource Trend"],
        specs=[[{"type": "indicator"}, {"type": "bar"}],
               [{"type": "domain"}, {"type": "scatter"}]]
    )
    
    # Left Without Being Seen Rate
    lwbs_rate = (filtered_visits['lwbs'].sum() / len(filtered_visits)) * 100
    fig.add_trace(go.Indicator(
        mode="gauge+number",
        value=lwbs_rate,
        number={"suffix": "%"},
        gauge={'axis': {'range': [None, 10]},
               'bar': {'color': colors['danger']},
               'steps': [{'range': [0, 2], 'color': "lightgreen"},
                        {'range': [2, 5], 'color': "yellow"}]},
        # title={"text": "Left Without Being Seen Rate"}
    ), row=1, col=1)
    
    # Length of Stay
    los_by_outcome = filtered_visits.groupby('outcome')['length_of_stay_mins'].mean() / 60
    fig.add_trace(go.Bar(
        x=los_by_outcome.index,
        y=los_by_outcome.values,
        marker_color=colors['success']
    ), row=1, col=2)
    
    # Insurance Types with proper labels
    insurance_counts = filtered_visits['insurance_type'].value_counts(dropna=False)
    insurance_labels = []
    for label in insurance_counts.index:
        if pd.isna(label):
            insurance_labels.append('Self-Pay')
        else:
            insurance_labels.append(str(label))
    
    fig.add_trace(go.Pie(
        labels=insurance_labels,
        values=insurance_counts.values,
        marker_colors=[colors['primary'], colors['secondary'], colors['warning']],
        textinfo='label+percent',
        textposition='auto'
    ), row=2, col=1)
    
    # Resource utilization trend
    daily_los = filtered_visits.groupby(filtered_visits['date'].dt.day)['length_of_stay_mins'].mean() / 60
    fig.add_trace(go.Scatter(
        x=daily_los.index,
        y=daily_los.values,
        mode='lines+markers',
        marker_color=colors['success'],
        line=dict(width=2)
    ), row=2, col=2)
    
    fig.update_layout(
        height=500,
        showlegend=False,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color=colors['text_white'], size=10, family="Roboto, sans-serif"),
        margin=dict(l=10, r=10, t=40, b=10)
    )
    
    return fig

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=8051)