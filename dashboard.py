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