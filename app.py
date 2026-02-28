import dash
from dash import dcc, html, Input, Output, callback
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
import dash_bootstrap_components as dbc
from datetime import datetime

# ── Data loading ───────────────────────────────────────────────────────────────
visits = pd.read_csv('data/patient_visits.csv')
referrals = pd.read_csv('data/referrals.csv')
hours = pd.read_csv('data/staff_hours.csv')

visits['date'] = pd.to_datetime(visits['date'])
visits['year_month'] = visits['date'].dt.to_period('M').astype(str)
available_months = sorted(visits['year_month'].unique())

month_mapping = {}
for month_str in available_months:
    year, month = month_str.split('-')
    month_names = ['January', 'February', 'March', 'April', 'May', 'June',
                   'July', 'August', 'September', 'October', 'November', 'December']
    month_mapping[month_str] = f"{month_names[int(month)-1]} {year}"

def get_days_in_month(year_month_str):
    year, month = map(int, year_month_str.split('-'))
    if month in [1, 3, 5, 7, 8, 10, 12]:
        return 31
    elif month in [4, 6, 9, 11]:
        return 30
    elif month == 2:
        return 29 if (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0) else 28

def filter_data_by_date(selected_month, day_range):
    month_data = visits[visits['year_month'] == selected_month].copy()
    if len(month_data) == 0:
        return visits.head(100), pd.DataFrame(), hours
    month_data['day'] = month_data['date'].dt.day
    filtered_data = month_data[
        (month_data['day'] >= day_range[0]) &
        (month_data['day'] <= day_range[1])
    ]
    filtered_visit_ids = filtered_data['visit_id'].tolist() if len(filtered_data) > 0 else []
    filtered_referrals = referrals[referrals['visit_id'].isin(filtered_visit_ids)]
    year, month = selected_month.split('-')
    year, month = int(year), int(month)
    start_week = ((month - 1) * 4) + 1
    end_week = start_week + 4
    filtered_hours = hours[
        (hours['year'] == year) &
        (hours['week'] >= start_week) &
        (hours['week'] <= end_week)
    ].copy()
    return filtered_data, filtered_referrals, filtered_hours

# ── Colour palette ─────────────────────────────────────────────────────────────
C = {
    'bg_page':       '#0d1b2a',   # deep navy page background
    'bg_card':       '#1a2742',   # card body
    'bg_header':     '#0d1b2a',   # card header strip
    'bg_kpi':        '#1a2742',   # KPI tile background
    'bg_filter':     '#162035',   # filter area
    'border':        '#2a3f5f',   # subtle border
    'accent':        '#00d4aa',   # teal-green primary (clinical)
    'accent2':       '#4f8ef7',   # blue secondary
    'accent3':       '#a78bfa',   # violet tertiary
    'success':       '#22c55e',   # green
    'warning':       '#f59e0b',   # amber
    'danger':        '#f43f5e',   # rose-red
    'text_primary':  '#e2e8f0',   # near-white body text
    'text_muted':    '#7f96b5',   # secondary text
    'text_label':    '#94a3b8',   # label text
    'grid':          'rgba(255,255,255,0.06)',
    'white':         '#ffffff',
}

# Performance targets
TARGETS = {
    'door_to_doctor': 40,    # minutes
    'lwbs_rate':       1.0,  # percent
    'los_target':      360,  # minutes
}

# ── App init ───────────────────────────────────────────────────────────────────
external_stylesheets = [
    dbc.themes.BOOTSTRAP,
    "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css",
    "https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap",
]
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
app.title = "Puurs Hospital — ED Analytics"

# ── Shared chart layout base ───────────────────────────────────────────────────
def chart_layout(**kwargs):
    base = dict(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color=C['text_primary'], size=11, family="Inter, sans-serif"),
        margin=dict(l=10, r=10, t=48, b=10),
        hoverlabel=dict(
            bgcolor=C['bg_card'],
            font_size=12,
            font_family="Inter, sans-serif",
            bordercolor=C['border']
        ),
        legend=dict(
            font=dict(size=11, color=C['text_muted']),
            bgcolor='rgba(0,0,0,0)',
        ),
    )
    base.update(kwargs)
    return base

def axis_style(**kwargs):
    base = dict(
        showgrid=True,
        gridcolor=C['grid'],
        gridwidth=1,
        zeroline=False,
        tickfont=dict(size=10, color=C['text_muted']),
        title_font=dict(size=10, color=C['text_muted']),
        linecolor=C['border'],
        showline=True,
    )
    base.update(kwargs)
    return base

# ── Style constants ────────────────────────────────────────────────────────────
FONT = "Inter, sans-serif"

page_style = {
    'background-color': C['bg_page'],
    'min-height': '100vh',
    'padding': '0',
    'font-family': FONT,
}

# ── KPI tile builder ───────────────────────────────────────────────────────────
def kpi_tile(icon, label, value_id, unit="", border_color=None, tooltip=""):
    border_color = border_color or C['accent']
    return html.Div([
        html.Div([
            html.Div([
                html.I(className=f"fas {icon}",
                       style={'font-size': '18px', 'color': border_color,
                              'margin-bottom': '8px'}),
                html.Div(label, style={
                    'font-size': '10px', 'color': C['text_muted'],
                    'text-transform': 'uppercase', 'letter-spacing': '0.08em',
                    'margin-bottom': '6px', 'font-weight': '500'
                }),
                html.Div(id=value_id, style={
                    'font-size': '24px', 'font-weight': '700',
                    'color': C['text_primary'], 'line-height': '1'
                }),
                html.Div(unit, style={
                    'font-size': '10px', 'color': C['text_muted'],
                    'margin-top': '4px'
                }),
            ], style={'text-align': 'center'}),
        ], style={
            'background': C['bg_kpi'],
            'border': f'1px solid {C["border"]}',
            'border-top': f'3px solid {border_color}',
            'border-radius': '8px',
            'padding': '18px 12px',
        })
    ])

# ── Card wrapper ───────────────────────────────────────────────────────────────
def dashboard_card(icon, title, subtitle, content, accent=None):
    accent = accent or C['accent']
    return html.Div([
        # Card header
        html.Div([
            html.Div([
                html.Div(style={
                    'width': '3px', 'background': accent,
                    'border-radius': '2px', 'margin-right': '12px',
                    'align-self': 'stretch',
                }),
                html.Div([
                    html.Div([
                        html.I(className=f"fas {icon}",
                               style={'font-size': '14px', 'color': accent,
                                      'margin-right': '8px'}),
                        html.Span(title, style={
                            'font-weight': '600', 'font-size': '14px',
                            'color': C['text_primary']
                        }),
                    ], style={'display': 'flex', 'align-items': 'center'}),
                    html.Div(subtitle, style={
                        'font-size': '11px', 'color': C['text_muted'],
                        'margin-top': '2px'
                    }),
                ]),
            ], style={'display': 'flex', 'align-items': 'center'}),
        ], style={
            'background': C['bg_header'],
            'padding': '14px 18px',
            'border-bottom': f'1px solid {C["border"]}',
            'border-radius': '10px 10px 0 0',
        }),
        # Card body
        html.Div(content, style={'padding': '16px'}),
    ], style={
        'background': C['bg_card'],
        'border': f'1px solid {C["border"]}',
        'border-radius': '10px',
        'margin-bottom': '20px',
        'box-shadow': '0 4px 24px rgba(0,0,0,0.35)',
        'overflow': 'hidden',
    })

# ── Layout ─────────────────────────────────────────────────────────────────────
app.layout = html.Div([

    # ── Top header bar ────────────────────────────────────────────────────────
    html.Div([
        html.Div([
            # Left: Branding
            html.Div([
                html.Div([
                    html.Div([
                        html.I(className="fas fa-hospital-alt",
                               style={'font-size': '22px', 'color': C['accent']}),
                    ], style={
                        'background': 'rgba(0,212,170,0.12)',
                        'border-radius': '8px', 'padding': '8px 10px',
                        'margin-right': '14px',
                    }),
                    html.Div([
                        html.Div("Puurs Hospital", style={
                            'font-size': '18px', 'font-weight': '700',
                            'color': C['text_primary'], 'letter-spacing': '-0.01em',
                        }),
                        html.Div("Emergency Department Analytics", style={
                            'font-size': '11px', 'color': C['text_muted'],
                            'font-weight': '400',
                        }),
                    ]),
                ], style={'display': 'flex', 'align-items': 'center'}),
            ]),

            # Centre: Nav pills
            html.Div([
                html.Div("Overview", style={
                    'background': 'rgba(0,212,170,0.15)',
                    'color': C['accent'], 'padding': '6px 16px',
                    'border-radius': '20px', 'font-size': '12px',
                    'font-weight': '600', 'border': f'1px solid {C["accent"]}',
                }),
            ], style={'display': 'flex', 'gap': '8px'}),

            # Right: User + timestamp
            html.Div([
                html.Div([
                    html.Div(
                        datetime.now().strftime("%-d %B %Y, %H:%M"),
                        style={'font-size': '11px', 'color': C['text_muted'],
                               'text-align': 'right', 'margin-bottom': '4px'}
                    ),
                    html.Div([
                        html.I(className="fas fa-circle",
                               style={'font-size': '7px', 'color': C['success'],
                                      'margin-right': '6px', 'vertical-align': 'middle'}),
                        html.Span("Dr. Sarah Johnson",
                                  style={'font-size': '13px', 'font-weight': '600',
                                         'color': C['text_primary']}),
                    ]),
                    html.Div("Head of Emergency Department",
                             style={'font-size': '10px', 'color': C['text_muted'],
                                    'text-align': 'right'}),
                ]),
            ]),
        ], style={
            'display': 'flex', 'align-items': 'center',
            'justify-content': 'space-between',
            'max-width': '1600px', 'margin': '0 auto',
            'padding': '0 24px',
        }),
    ], style={
        'background': C['bg_card'],
        'border-bottom': f'1px solid {C["border"]}',
        'padding': '14px 0',
        'position': 'sticky', 'top': '0', 'z-index': '100',
    }),

    # ── Page body ─────────────────────────────────────────────────────────────
    html.Div([

        # ── Filter bar ───────────────────────────────────────────────────────
        html.Div([
            html.Div([
                # Label
                html.Div([
                    html.I(className="fas fa-filter",
                           style={'font-size': '12px', 'color': C['accent'],
                                  'margin-right': '8px'}),
                    html.Span("Filters", style={
                        'font-size': '12px', 'font-weight': '600',
                        'color': C['text_primary'],
                    }),
                ], style={'display': 'flex', 'align-items': 'center',
                          'margin-right': '24px', 'white-space': 'nowrap'}),

                # Month
                html.Div([
                    html.Label("Month", style={
                        'font-size': '10px', 'color': C['text_muted'],
                        'text-transform': 'uppercase', 'letter-spacing': '0.06em',
                        'margin-bottom': '4px', 'font-weight': '500',
                        'display': 'block',
                    }),
                    dcc.Dropdown(
                        id='month-selector',
                        options=[{'label': month_mapping[m], 'value': m}
                                 for m in available_months],
                        value=available_months[-1],
                        clearable=False,
                        style={'min-width': '180px', 'font-size': '13px'},
                    ),
                ], style={'margin-right': '32px'}),

                # Day range
                html.Div([
                    html.Label([
                        html.Span("Day Range: ", style={
                            'font-size': '10px', 'color': C['text_muted'],
                            'text-transform': 'uppercase', 'letter-spacing': '0.06em',
                            'font-weight': '500',
                        }),
                        html.Span(id='month-display', style={
                            'font-size': '11px', 'color': C['accent'],
                            'font-weight': '600',
                        }),
                    ], style={'display': 'block', 'margin-bottom': '4px'}),
                    dcc.RangeSlider(
                        id='day-slider',
                        min=1, max=31, step=1,
                        value=[1, 31],
                        marks={i: {'label': str(i),
                                   'style': {'color': C['text_muted'],
                                             'fontSize': '9px'}}
                               for i in range(1, 32, 5)},
                        tooltip={"placement": "bottom", "always_visible": False},
                    ),
                ], style={'flex': '1', 'min-width': '300px'}),

            ], style={
                'display': 'flex', 'align-items': 'center', 'flex-wrap': 'wrap',
                'gap': '8px',
                'max-width': '1600px', 'margin': '0 auto', 'padding': '0 24px',
            }),
        ], style={
            'background': C['bg_filter'],
            'border-bottom': f'1px solid {C["border"]}',
            'padding': '14px 0',
        }),

        # ── KPI summary row ───────────────────────────────────────────────────
        html.Div([
            dbc.Row([
                dbc.Col(kpi_tile("fa-procedures", "Total Visits",
                                 "kpi-visits", "", C['accent']), xs=6, md=4, lg=2),
                dbc.Col(kpi_tile("fa-stopwatch", "Avg Door-to-Doctor",
                                 "kpi-d2d", "minutes", C['accent2']), xs=6, md=4, lg=2),
                dbc.Col(kpi_tile("fa-bed", "Admission Rate",
                                 "kpi-admission", "%", C['warning']), xs=6, md=4, lg=2),
                dbc.Col(kpi_tile("fa-sign-out-alt", "LWBS Rate",
                                 "kpi-lwbs", "%", C['danger']), xs=6, md=4, lg=2),
                dbc.Col(kpi_tile("fa-clock", "Avg Length of Stay",
                                 "kpi-los", "hours", C['accent3']), xs=6, md=4, lg=2),
                dbc.Col(kpi_tile("fa-star", "Avg Satisfaction",
                                 "kpi-satisfaction", "/ 10", C['success']), xs=6, md=4, lg=2),
            ], className="g-3"),
        ], style={'padding': '20px 24px 8px',
                  'max-width': '1600px', 'margin': '0 auto'}),

        # ── Main dashboard grid ───────────────────────────────────────────────
        html.Div([
            dbc.Row([
                # Card 1 — Department Input (Staffing)
                dbc.Col([
                    dashboard_card(
                        icon="fa-users",
                        title="Department Input Metrics",
                        subtitle="Staffing resources & capacity overview",
                        accent=C['accent'],
                        content=[
                            dcc.Loading(
                                type="circle",
                                color=C['accent'],
                                children=[
                                    html.Div(id="staff-summary-content"),
                                    dcc.Graph(id="staff-chart",
                                              style={'height': '340px'},
                                              config={'displayModeBar': False}),
                                ]
                            )
                        ]
                    )
                ], lg=6, md=12),

                # Card 2 — Processing Time
                dbc.Col([
                    dashboard_card(
                        icon="fa-clock",
                        title="Processing Time Metrics",
                        subtitle="Patient flow, wait times & service requirements",
                        accent=C['accent2'],
                        content=[
                            dcc.Loading(
                                type="circle",
                                color=C['accent2'],
                                children=[
                                    dcc.Graph(id="processing-chart",
                                              style={'height': '500px'},
                                              config={'displayModeBar': False}),
                                ]
                            )
                        ]
                    )
                ], lg=6, md=12),
            ], className="g-0 mb-0"),

            dbc.Row([
                # Card 3 — Department Output
                dbc.Col([
                    dashboard_card(
                        icon="fa-chart-bar",
                        title="Department Output Metrics",
                        subtitle="Patient outcomes, diagnoses & referral patterns",
                        accent=C['warning'],
                        content=[
                            dcc.Loading(
                                type="circle",
                                color=C['warning'],
                                children=[
                                    dcc.Graph(id="output-chart",
                                              style={'height': '500px'},
                                              config={'displayModeBar': False}),
                                ]
                            )
                        ]
                    )
                ], lg=6, md=12),

                # Card 4 — Resource Utilisation
                dbc.Col([
                    dashboard_card(
                        icon="fa-chart-pie",
                        title="Resource Utilisation",
                        subtitle="Efficiency, length of stay & insurance breakdown",
                        accent=C['accent3'],
                        content=[
                            dcc.Loading(
                                type="circle",
                                color=C['accent3'],
                                children=[
                                    dcc.Graph(id="resource-chart",
                                              style={'height': '500px'},
                                              config={'displayModeBar': False}),
                                ]
                            )
                        ]
                    )
                ], lg=6, md=12),
            ], className="g-0"),

        ], style={'padding': '12px 24px 8px',
                  'max-width': '1600px', 'margin': '0 auto'}),

        # ── Footer ───────────────────────────────────────────────────────────
        html.Div([
            html.Div([
                html.Span("Puurs Hospital ED Analytics  ·  ", style={'color': C['text_muted']}),
                html.Span("Synthetic data — for demonstration only",
                          style={'color': C['text_muted'], 'font-style': 'italic'}),
                html.Span("  ·  Targets: Door-to-Doctor ≤40 min  |  LWBS ≤1%  |  LoS ≤360 min",
                          style={'color': C['text_muted']}),
            ], style={'font-size': '10px', 'text-align': 'center', 'padding': '16px 0'}),
        ], style={'border-top': f'1px solid {C["border"]}',
                  'margin-top': '8px'}),

    ], style={'padding': '0'}),

], style=page_style)


# ── Callbacks ─────────────────────────────────────────────────────────────────

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
    month_name = month_mapping.get(selected_month, selected_month)
    days = get_days_in_month(selected_month)
    marks = {i: {'label': str(i), 'style': {'color': C['text_muted'], 'fontSize': '9px'}}
             for i in range(1, days + 1, 5)}
    marks[1] = {'label': '1', 'style': {'color': C['text_muted'], 'fontSize': '9px'}}
    marks[days] = {'label': str(days), 'style': {'color': C['text_muted'], 'fontSize': '9px'}}
    return month_name, days, marks, [1, days]


@callback(
    [Output('kpi-visits', 'children'),
     Output('kpi-d2d', 'children'),
     Output('kpi-admission', 'children'),
     Output('kpi-lwbs', 'children'),
     Output('kpi-los', 'children'),
     Output('kpi-satisfaction', 'children')],
    [Input('month-selector', 'value'),
     Input('day-slider', 'value')]
)
def update_kpis(selected_month, day_range):
    fv, _, _ = filter_data_by_date(selected_month, day_range)
    if len(fv) == 0:
        return ["—"] * 6

    total_visits  = f"{len(fv):,}"
    avg_d2d       = f"{fv['door_to_doctor_mins'].mean():.0f}"
    admission_pct = f"{(fv['outcome']=='Admitted').sum() / len(fv) * 100:.1f}"
    lwbs_pct      = f"{fv['lwbs'].sum() / len(fv) * 100:.1f}"
    avg_los       = f"{fv['length_of_stay_mins'].mean() / 60:.1f}"
    avg_sat       = f"{fv['satisfaction_score'].mean():.1f}"

    # Colour-code against targets
    def coloured(val_str, threshold, higher_is_bad=True):
        val = float(val_str)
        good  = val <= threshold if higher_is_bad else val >= threshold
        color = C['success'] if good else C['danger']
        return html.Span(val_str, style={'color': color})

    d2d_el  = coloured(avg_d2d, TARGETS['door_to_doctor'])
    lwbs_el = coloured(lwbs_pct, TARGETS['lwbs_rate'])
    sat_el  = html.Span(avg_sat, style={'color': C['success'] if float(avg_sat) >= 7 else C['warning']})

    return (
        html.Span(total_visits, style={'color': C['text_primary']}),
        d2d_el,
        html.Span(admission_pct, style={'color': C['warning']}),
        lwbs_el,
        html.Span(avg_los, style={'color': C['text_primary']}),
        sat_el,
    )


@callback(
    [Output('staff-summary-content', 'children'),
     Output('staff-chart', 'figure')],
    [Input('month-selector', 'value'),
     Input('day-slider', 'value')]
)
def update_staff_card(selected_month, day_range):
    _, _, filtered_hours = filter_data_by_date(selected_month, day_range)

    empty_fig = go.Figure()
    empty_fig.update_layout(**chart_layout(height=320))

    if len(filtered_hours) == 0:
        msg = html.Div("No staff data available",
                       style={'color': C['text_muted'], 'padding': '20px',
                              'text-align': 'center', 'font-size': '13px'})
        return msg, empty_fig

    staff_counts    = filtered_hours.groupby('role').size()
    total_staff     = filtered_hours['staff_name'].nunique()
    doctor_roles    = ['Consultant', 'Registrar', 'Medical Officer']
    doctor_hours_df = filtered_hours[filtered_hours['role'].isin(doctor_roles)]
    total_hrs       = doctor_hours_df['hours_worked'].sum()
    total_nurse_hrs = filtered_hours[filtered_hours['role'] == 'Nurse']['hours_worked'].sum()

    individual = (doctor_hours_df.groupby('staff_name')['hours_worked']
                  .sum().sort_values(ascending=False).head(5).sort_values(ascending=True))
    if len(individual) == 0:
        individual = pd.Series([0], index=['No doctors'])

    # Role pills
    role_items = [
        ("fa-stethoscope", "Consultants",    staff_counts.get('Consultant',     0), C['accent']),
        ("fa-user-md",     "Registrars",     staff_counts.get('Registrar',      0), C['accent2']),
        ("fa-user",        "Medical Officers",staff_counts.get('Medical Officer',0), C['accent3']),
        ("fa-heartbeat",   "Nurses",         staff_counts.get('Nurse',          0), C['success']),
    ]

    role_pills = html.Div([
        html.Div([
            html.I(className=f"fas {ico}",
                   style={'color': col, 'margin-right': '6px', 'font-size': '11px'}),
            html.Span(lbl, style={'font-size': '11px', 'color': C['text_muted']}),
            html.Span(f"  {cnt}", style={'font-size': '13px', 'font-weight': '700',
                                         'color': col, 'margin-left': '4px'}),
        ], style={
            'display': 'flex', 'align-items': 'center',
            'background': 'rgba(255,255,255,0.04)',
            'border': f'1px solid {C["border"]}',
            'border-radius': '6px', 'padding': '8px 12px',
            'flex': '1', 'min-width': '120px',
        })
        for ico, lbl, cnt, col in role_items
    ], style={'display': 'flex', 'gap': '8px', 'flex-wrap': 'wrap',
              'margin-bottom': '12px'})

    # Summary stats row
    stats_row = html.Div([
        html.Div([
            html.Div(f"{total_staff}", style={
                'font-size': '28px', 'font-weight': '700', 'color': C['accent'],
                'line-height': '1',
            }),
            html.Div("Total Active Staff", style={
                'font-size': '10px', 'color': C['text_muted'],
                'text-transform': 'uppercase', 'letter-spacing': '0.06em',
                'margin-top': '4px',
            }),
        ], style={'text-align': 'center', 'padding': '12px 20px',
                  'background': 'rgba(0,212,170,0.08)',
                  'border-radius': '8px', 'border-left': f'3px solid {C["accent"]}',
                  'margin-right': '12px', 'flex': '1'}),

        html.Div([
            html.Div(f"{total_hrs:,.0f}", style={
                'font-size': '28px', 'font-weight': '700', 'color': C['warning'],
                'line-height': '1',
            }),
            html.Div("Doctor Hours", style={
                'font-size': '10px', 'color': C['text_muted'],
                'text-transform': 'uppercase', 'letter-spacing': '0.06em',
                'margin-top': '4px',
            }),
        ], style={'text-align': 'center', 'padding': '12px 20px',
                  'background': 'rgba(245,158,11,0.08)',
                  'border-radius': '8px', 'border-left': f'3px solid {C["warning"]}',
                  'flex': '1'}),
    ], style={'display': 'flex', 'margin-bottom': '12px'})

    summary = html.Div([role_pills, stats_row])

    # Chart
    bar_colors = [C['accent2'], C['accent3'], C['accent'], C['warning'], C['success']]
    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=[f"Dr. {n.split()[-1]}" for n in individual.index],
        x=individual.values,
        orientation='h',
        marker=dict(
            color=bar_colors[:len(individual)],
            line=dict(width=0),
        ),
        text=[f"  {int(h)}h" for h in individual.values],
        textposition='outside',
        textfont=dict(size=11, color=C['text_primary'], family=FONT),
        hovertemplate='<b>%{y}</b><br>Hours: %{x:.0f}<extra></extra>',
    ))
    fig.update_layout(
        **chart_layout(
            height=320,
            title=dict(text="Top 5 Physicians by Hours Worked",
                       font=dict(size=12, color=C['text_muted']), x=0, xanchor='left'),
        ),
        xaxis=axis_style(title_text="Hours"),
        yaxis=axis_style(showgrid=False, automargin=True,
                         tickfont=dict(size=11, color=C['text_primary'])),
    )
    return summary, fig


@callback(
    Output('processing-chart', 'figure'),
    [Input('month-selector', 'value'),
     Input('day-slider', 'value')]
)
def update_processing_card(selected_month, day_range):
    fv, _, _ = filter_data_by_date(selected_month, day_range)
    if len(fv) == 0:
        fv = visits.head(1000)

    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=("Door-to-Doctor Time", "Wait Time by ESI Level",
                        "Service Requirements", "Daily Wait Time Trend"),
        specs=[[{"type": "indicator"}, {"type": "bar"}],
               [{"type": "domain"},   {"type": "scatter"}]],
        vertical_spacing=0.16,
        horizontal_spacing=0.10,
    )

    avg_d2d = fv['door_to_doctor_mins'].mean()
    delta_color = "increasing" if avg_d2d > TARGETS['door_to_doctor'] else "decreasing"
    fig.add_trace(go.Indicator(
        mode="number+delta",
        value=avg_d2d,
        delta={'reference': TARGETS['door_to_doctor'],
               'increasing': {'color': C['danger']},
               'decreasing': {'color': C['success']},
               'font': {'size': 13}},
        number={'suffix': " min",
                'font': {'size': 36, 'color': C['accent2'], 'family': FONT}},
        title={'text': f"<b>Avg Wait</b><br><span style='font-size:11px;color:{C['text_muted']}'>Target: ≤{TARGETS['door_to_doctor']} min</span>",
               'font': {'size': 12, 'color': C['text_muted']}},
    ), row=1, col=1)

    esi_times = fv.groupby('esi_level')['door_to_doctor_mins'].mean().sort_index()
    esi_colors = [C['danger'], C['warning'], C['warning'], C['accent2'], C['success']]
    fig.add_trace(go.Bar(
        x=[f"ESI {i}" for i in esi_times.index],
        y=esi_times.values,
        marker=dict(color=[esi_colors[i-1] for i in esi_times.index], line=dict(width=0)),
        text=[f"{v:.0f}m" for v in esi_times.values],
        textposition='outside',
        textfont=dict(size=10, color=C['text_muted']),
        hovertemplate='<b>%{x}</b><br>Avg Wait: %{y:.1f} min<extra></extra>',
    ), row=1, col=2)
    # Target line on ESI chart — use add_shape to avoid Plotly indicator/hline bug
    fig.add_shape(type="line",
                  x0=0, x1=1, xref="x domain",
                  y0=TARGETS['door_to_doctor'], y1=TARGETS['door_to_doctor'], yref="y",
                  line=dict(dash="dash", color=C['danger'], width=1.5))
    fig.add_annotation(x=0.99, xref="x domain", xanchor="right",
                       y=TARGETS['door_to_doctor'], yref="y", yanchor="bottom",
                       text=f"Target {TARGETS['door_to_doctor']}m",
                       showarrow=False,
                       font=dict(color=C['danger'], size=9))

    total_pts = len(fv)
    services = {
        'Labs':    (fv['needs_labs'].sum() / total_pts) * 100,
        'Imaging': (fv['needs_imaging'].sum() / total_pts) * 100,
        'Consults':(fv['needs_consult'].sum() / total_pts) * 100,
    }
    fig.add_trace(go.Pie(
        labels=list(services.keys()),
        values=list(services.values()),
        marker=dict(colors=[C['accent'], C['accent2'], C['accent3']],
                    line=dict(color=C['bg_page'], width=2)),
        textinfo='label+percent',
        textposition='inside',
        textfont=dict(size=11, family=FONT),
        hovertemplate='<b>%{label}</b><br>%{value:.1f}%<extra></extra>',
        hole=0.45,
    ), row=2, col=1)

    daily_avg = fv.groupby(fv['date'].dt.day)['door_to_doctor_mins'].mean()
    fig.add_trace(go.Scatter(
        x=daily_avg.index,
        y=daily_avg.values,
        mode='lines+markers',
        marker=dict(color=C['accent2'], size=5, line=dict(color=C['bg_page'], width=1)),
        line=dict(color=C['accent2'], width=2),
        fill='tozeroy',
        fillcolor='rgba(79,142,247,0.1)',
        hovertemplate='Day %{x}: %{y:.1f} min<extra></extra>',
    ), row=2, col=2)
    fig.add_shape(type="line",
                  x0=0, x1=1, xref="x2 domain",
                  y0=TARGETS['door_to_doctor'], y1=TARGETS['door_to_doctor'], yref="y2",
                  line=dict(dash="dot", color=C['danger'], width=1))

    fig.update_layout(**chart_layout(height=480, showlegend=False,
                                     margin=dict(l=10, r=20, t=52, b=10)))
    for ann in fig['layout']['annotations']:
        ann['font'] = dict(size=12, color=C['text_muted'], family=FONT)
    fig.update_xaxes(**axis_style())
    fig.update_yaxes(**axis_style())
    fig.update_xaxes(title_text="Day of Month", row=2, col=2)
    fig.update_yaxes(title_text="Minutes", row=1, col=2)
    fig.update_yaxes(title_text="Minutes", row=2, col=2)
    return fig


@callback(
    Output('output-chart', 'figure'),
    [Input('month-selector', 'value'),
     Input('day-slider', 'value')]
)
def update_output_card(selected_month, day_range):
    fv, _, _ = filter_data_by_date(selected_month, day_range)
    if len(fv) == 0:
        fv = visits.head(1000)

    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=("Patient Outcomes", "Top 5 Diagnoses",
                        "Top Referral Departments", "Admission Rate"),
        specs=[[{"type": "bar"}, {"type": "bar"}],
               [{"type": "bar"}, {"type": "indicator"}]],
        vertical_spacing=0.16,
        horizontal_spacing=0.10,
    )

    outcomes = fv['outcome'].value_counts()
    outcome_palette = {'Discharged': C['success'], 'Admitted': C['warning'], 'LWBS': C['danger']}
    fig.add_trace(go.Bar(
        x=outcomes.index,
        y=outcomes.values,
        marker=dict(
            color=[outcome_palette.get(o, C['accent']) for o in outcomes.index],
            line=dict(width=0),
        ),
        text=[f"{v:,}" for v in outcomes.values],
        textposition='outside',
        textfont=dict(size=11, color=C['text_muted']),
        hovertemplate='<b>%{x}</b><br>%{y:,} patients<extra></extra>',
    ), row=1, col=1)

    top_dx = fv['diagnosis'].value_counts().head(5).sort_values(ascending=True)
    labels_dx = [d[:22]+'…' if len(d) > 22 else d for d in top_dx.index]
    fig.add_trace(go.Bar(
        y=labels_dx,
        x=top_dx.values,
        orientation='h',
        marker=dict(
            color=C['accent2'],
            line=dict(width=0),
        ),
        text=[f"{v:,}" for v in top_dx.values],
        textposition='outside',
        textfont=dict(size=10, color=C['text_muted']),
        hovertemplate='<b>%{y}</b><br>%{x:,} cases<extra></extra>',
    ), row=1, col=2)

    dept_counts = fv['department'].value_counts().head(5).sort_values(ascending=True)
    labels_dept = [d[:20]+'…' if len(d) > 20 else d for d in dept_counts.index]
    fig.add_trace(go.Bar(
        y=labels_dept,
        x=dept_counts.values,
        orientation='h',
        marker=dict(color=C['accent3'], line=dict(width=0)),
        text=[f"{v:,}" for v in dept_counts.values],
        textposition='outside',
        textfont=dict(size=10, color=C['text_muted']),
        hovertemplate='<b>%{y}</b><br>%{x:,} visits<extra></extra>',
    ), row=2, col=1)

    admission_rate = (fv['outcome'] == 'Admitted').sum() / len(fv) * 100
    gauge_color = C['success'] if admission_rate < 20 else (C['warning'] if admission_rate < 40 else C['danger'])
    fig.add_trace(go.Indicator(
        mode="gauge+number",
        value=admission_rate,
        number={'suffix': "%",
                'font': {'size': 32, 'color': gauge_color, 'family': FONT}},
        gauge={
            'axis': {'range': [0, 60], 'tickfont': {'size': 9},
                     'tickcolor': C['text_muted']},
            'bar':  {'color': gauge_color, 'thickness': 0.25},
            'bgcolor': 'rgba(0,0,0,0)',
            'borderwidth': 0,
            'steps': [
                {'range': [0, 20],  'color': 'rgba(34,197,94,0.15)'},
                {'range': [20, 40], 'color': 'rgba(245,158,11,0.15)'},
                {'range': [40, 60], 'color': 'rgba(244,63,94,0.15)'},
            ],
        },
        title={'text': f"Admission Rate<br><span style='font-size:10px;color:{C['text_muted']}'>Good: &lt;20%</span>",
               'font': {'size': 12, 'color': C['text_muted'], 'family': FONT}},
    ), row=2, col=2)

    fig.update_layout(**chart_layout(height=480, showlegend=False,
                                     margin=dict(l=10, r=20, t=52, b=10)))
    for ann in fig['layout']['annotations']:
        ann['font'] = dict(size=12, color=C['text_muted'], family=FONT)
    fig.update_xaxes(**axis_style())
    fig.update_yaxes(**axis_style(automargin=True))
    fig.update_yaxes(title_text="Patients", row=1, col=1)
    fig.update_xaxes(title_text="Cases", row=1, col=2)
    fig.update_xaxes(title_text="Visits", row=2, col=1)
    return fig


@callback(
    Output('resource-chart', 'figure'),
    [Input('month-selector', 'value'),
     Input('day-slider', 'value')]
)
def update_resource_card(selected_month, day_range):
    fv, _, _ = filter_data_by_date(selected_month, day_range)
    if len(fv) == 0:
        fv = visits.head(1000)

    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=("LWBS Rate", "Length of Stay by Outcome",
                        "Insurance Type", "Daily Length of Stay Trend"),
        specs=[[{"type": "indicator"}, {"type": "bar"}],
               [{"type": "domain"},   {"type": "scatter"}]],
        vertical_spacing=0.16,
        horizontal_spacing=0.10,
    )

    lwbs_rate  = fv['lwbs'].sum() / len(fv) * 100
    lwbs_color = C['success'] if lwbs_rate <= TARGETS['lwbs_rate'] else C['danger']
    fig.add_trace(go.Indicator(
        mode="gauge+number",
        value=lwbs_rate,
        number={'suffix': "%",
                'font': {'size': 32, 'color': lwbs_color, 'family': FONT}},
        gauge={
            'axis': {'range': [0, 8], 'tickfont': {'size': 9},
                     'tickcolor': C['text_muted']},
            'bar':  {'color': lwbs_color, 'thickness': 0.25},
            'bgcolor': 'rgba(0,0,0,0)',
            'borderwidth': 0,
            'steps': [
                {'range': [0, 1], 'color': 'rgba(34,197,94,0.15)'},
                {'range': [1, 3], 'color': 'rgba(245,158,11,0.15)'},
                {'range': [3, 8], 'color': 'rgba(244,63,94,0.15)'},
            ],
            'threshold': {'line': {'color': C['danger'], 'width': 2},
                          'thickness': 0.8,
                          'value': TARGETS['lwbs_rate']},
        },
        title={'text': ("Left Without Being Seen<br>"
                        f"<span style='font-size:10px;color:{C['text_muted']}'>"
                        f"Target: \u2264{TARGETS['lwbs_rate']}%</span>"),
               'font': {'size': 12, 'color': C['text_muted'], 'family': FONT}},
    ), row=1, col=1)

    los = fv.groupby('outcome')['length_of_stay_mins'].mean() / 60
    los_palette = {'Discharged': C['success'], 'Admitted': C['warning'], 'LWBS': C['danger']}
    fig.add_trace(go.Bar(
        x=los.index,
        y=los.values,
        marker=dict(color=[los_palette.get(o, C['accent']) for o in los.index],
                    line=dict(width=0)),
        text=[f"{v:.1f}h" for v in los.values],
        textposition='outside',
        textfont=dict(size=11, color=C['text_muted']),
        hovertemplate='<b>%{x}</b><br>Avg Stay: %{y:.2f} h<extra></extra>',
    ), row=1, col=2)
    fig.add_shape(type="line",
                  x0=0, x1=1, xref="x domain",
                  y0=TARGETS['los_target'] / 60, y1=TARGETS['los_target'] / 60, yref="y",
                  line=dict(dash="dot", color=C['danger'], width=1))
    fig.add_annotation(x=0.99, xref="x domain", xanchor="right",
                       y=TARGETS['los_target'] / 60, yref="y", yanchor="bottom",
                       text=f"Target {TARGETS['los_target']//60}h",
                       showarrow=False,
                       font=dict(color=C['danger'], size=9))

    ins = fv['insurance_type'].value_counts(dropna=False)
    ins_labels = ['Self-Pay' if pd.isna(l) else str(l) for l in ins.index]
    fig.add_trace(go.Pie(
        labels=ins_labels,
        values=ins.values,
        marker=dict(colors=[C['accent'], C['accent2'], C['accent3']],
                    line=dict(color=C['bg_page'], width=2)),
        textinfo='label+percent',
        textposition='inside',
        textfont=dict(size=11, family=FONT),
        hovertemplate='<b>%{label}</b><br>%{value:,} patients (%{percent})<extra></extra>',
        hole=0.45,
    ), row=2, col=1)

    daily_los = fv.groupby(fv['date'].dt.day)['length_of_stay_mins'].mean() / 60
    fig.add_trace(go.Scatter(
        x=daily_los.index,
        y=daily_los.values,
        mode='lines+markers',
        marker=dict(color=C['accent3'], size=5, line=dict(color=C['bg_page'], width=1)),
        line=dict(color=C['accent3'], width=2),
        fill='tozeroy',
        fillcolor='rgba(167,139,250,0.1)',
        hovertemplate='Day %{x}: %{y:.2f} h<extra></extra>',
    ), row=2, col=2)
    fig.add_shape(type="line",
                  x0=0, x1=1, xref="x2 domain",
                  y0=TARGETS['los_target'] / 60, y1=TARGETS['los_target'] / 60, yref="y2",
                  line=dict(dash="dot", color=C['danger'], width=1))

    fig.update_layout(**chart_layout(height=480, showlegend=False,
                                     margin=dict(l=10, r=20, t=52, b=10)))
    for ann in fig['layout']['annotations']:
        ann['font'] = dict(size=12, color=C['text_muted'], family=FONT)
    fig.update_xaxes(**axis_style())
    fig.update_yaxes(**axis_style())
    fig.update_yaxes(title_text="Hours", row=1, col=2)
    fig.update_xaxes(title_text="Day of Month", row=2, col=2)
    fig.update_yaxes(title_text="Hours", row=2, col=2)
    return fig


if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=8051)
