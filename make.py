#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Dec 20 20:10:13 2022

@author: richardbradshaw
"""

# Imports
import pandas as pd
import numpy as np
#import plotly.express as px
import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.figure_factory as ff


# Get vehicles database
# url_cars = 'https://www.fueleconomy.gov/feg/epadata/vehicles.csv'
# cars = pd.read_csv(url_cars, low_memory=False)
cars = pd.read_csv('cars_database.csv', low_memory=(False))

ev = cars[cars['fuelType1'] == 'Electricity']
ice = cars[(cars['fuelType1'] != 'Electricity') & (cars['fuelType2'] != 'Electricity') & (cars['atvType'] != 'Hybrid')]
phev = cars[cars['atvType'] == 'Plug-in Hybrid']
hybrids = cars[cars['atvType'] == 'Hybrid']

# Dictionary of state names from https://gist.github.com/JeffPaine/3083347
states = {
    'AK': 'Alaska', 'AL': 'Alabama', 'AR': 'Arkansas', 'AZ': 'Arizona',
    'CA': 'California', 'CO': 'Colorado', 'CT': 'Connecticut', 
    'DC': 'District of Columbia', 'DE': 'Delaware', 'FL': 'Florida',
    'GA': 'Georgia', 'HI': 'Hawaii', 'IA': 'Iowa', 'ID': 'Idaho',
    'IL': 'Illinois', 'IN': 'Indiana', 'KS': 'Kansas', 'KY': 'Kentucky',
    'LA': 'Louisiana', 'MA': 'Massachusetts', 'MD': 'Maryland',
    'ME': 'Maine', 'MI': 'Michigan', 'MN': 'Minnesota', 'MO': 'Missouri',
    'MS': 'Mississippi', 'MT': 'Montana', 'NC': 'North Carolina',
    'ND': 'North Dakota', 'NE': 'Nebraska', 'NH': 'New Hampshire',
    'NJ': 'New Jersey', 'NM': 'New Mexico', 'NV': 'Nevada',
    'NY': 'New York', 'OH': 'Ohio', 'OK': 'Oklahoma', 'OR': 'Oregon',
    'PA': 'Pennsylvania', 'RI': 'Rhode Island', 'SC': 'South Carolina',
    'SD': 'South Dakota', 'TN': 'Tennessee', 'TX': 'Texas', 'UT': 'Utah',
    'VA': 'Virginia', 'VT': 'Vermont', 'WA': 'Washington',
    'WI': 'Wisconsin', 'WV': 'West Virginia', 'WY': 'Wyoming'
}


# Create Dash app
app = dash.Dash()

# Set up the app layout
app.layout = html.Div(children=[
    html.Div(children=[
        html.H1(children='Fuel Efficiency Comparison')
        ], style={'textAlign': 'center'}),
    
    html.Div(children=[
        html.Label('State where you purchase fuel'),
        dcc.Dropdown(id='state_dropdown', placeholder='Select State', 
                     options=[{'label': i, 'value': i}
                              for i in sorted(states.values())]), 
        
        html.Br(),
        html.Label('Daily City Driving Miles '),
        dcc.Input(id='city_in', type='number', placeholder='City miles'), 
        
        html.Br(),
        html.Label('Daily Highway Driving Miles '),
        dcc.Input(id='highway_in', type='number', placeholder='Highway miles')], 
        className='driver_inputs', 
        style={'padding':'2rem', 'margin':'.3rem', 'boxShadow': '#e3e3e3 4px 4px 2px', 
               'border-radius': '5px', 'marginTop': '.1rem', 'width': '40%'}),
    
    html.Div(children=[
        html.H3('Vehicle 1', style={'textAlign': 'center', 'marginTop': '.1rem'}),
        dcc.Dropdown(id='year_dropdown_1',
                     options=[{'label': n, 'value': n}
                             for n in sorted(cars['year'].unique(),reverse=True)],
                     placeholder='Select Year'),
        
        dcc.Dropdown(id='make_dropdown_1', placeholder='Select Make'),
        
        dcc.Dropdown(id='model_dropdown_1', placeholder='Select Model'),
        
        dcc.Dropdown(id='options_dropdown_1', placeholder='Select Options')], 
        className='car1_inputs',
        style={'padding':'2rem', 'margin':'.3rem', 'boxShadow': '#e3e3e3 4px 4px 2px', 
               'border-radius': '5px', 'marginTop': '.1rem', 'width': '40%'} ),
    
    html.Div(children=[
        html.H3('Vehicle 2', style={'textAlign': 'center', 'marginTop': '.1rem'}),
        dcc.Dropdown(id='year_dropdown_2',
                     options=[{'label': n, 'value': n}
                             for n in sorted(cars['year'].unique(),reverse=True)],
                     placeholder='Select Year'),
        
        dcc.Dropdown(id='make_dropdown_2', placeholder='Select Make'),
        
        dcc.Dropdown(id='model_dropdown_2', placeholder='Select Model'),
        
        dcc.Dropdown(id='options_dropdown_2', placeholder='Select Options')], 
        className='car1_inputs',
        style={'padding':'2rem', 'margin':'.3rem', 'boxShadow': '#e3e3e3 4px 4px 2px', 
               'border-radius': '5px', 'marginTop': '.1rem', 'width': '40%'} ),
    
    html.Div(children=[
        dcc.Graph(id='test_plot')], 
        className='four columns', 
        style={'padding':'.3rem', 'marginTop':'.3rem', 'marginLeft':'1rem', 
               'boxShadow': '#e3e3e3 4px 4px 2px', 'border-radius': '1px', 
               'backgroundColor': 'white', 'display': 'flex'})
    ])

# Set up the callback function

# Vehicle 1
# Callback to set the vehicle 1 make options based on the selected year
@app.callback(
    Output('make_dropdown_1', 'options'),
    Input('year_dropdown_1', 'value')
    )
def set_make_1_options(selected_year):
    return [{'label': i, 'value': i}
            for i in sorted(cars[cars['year'] == selected_year]['make'].unique())]

# Callback to get the value of the selected vehicle 1 make
@app.callback(
    Output('make_dropdown_1', 'value'),
    Input('make_dropdown_1', 'options'))
def set_make_1_value(available_options):
    return available_options[0]['value']

# Callback to set the vehicle 1 model options based on the selected make
@app.callback(
    Output('model_dropdown_1', 'options'),
    Input('make_dropdown_1', 'value'),
    Input('year_dropdown_1', 'value')
    )
def set_model_1_options(selected_make, selected_year):
    return [{'label': i, 'value': i}
            for i in sorted(cars[(cars['year'] == selected_year) & \
                                 (cars['make'] == selected_make)]['model'].unique())]

# Callback to get the value of the selected vehicle 1 model
@app.callback(
    Output('model_dropdown_1', 'value'),
    Input('model_dropdown_1', 'options'))
def set_model_1_value(available_options):
    return available_options[0]['value']

# Callback to set the final vehicle 1 options based on the selected model
@app.callback(
    Output('options_dropdown_1', 'options'),
    Input('make_dropdown_1', 'value'),
    Input('year_dropdown_1', 'value'),
    Input('model_dropdown_1', 'value')
    )
def set_final_model_1_options(selected_make, selected_year, selected_model):
    temp = cars[(cars['year'] == selected_year) & \
                                 (cars['make'] == selected_make) & \
                                 (cars['model'] == selected_model)]
    temp['startStop_flag'] = np.where(temp['startStop'] == 'Y', ' start/stop', '')


    if (temp['fuelType1'] == 'Electricity').all():
        temp['label'] = temp['drive'] + ', ' + temp['rangeCity'].astype('str') + '/' + \
            temp['rangeHwy'].astype('str') + ' mile city/highway range'
    else:
        temp['label'] = temp['displ'].astype('str') + ' liter ' + temp['cylinders'].astype('str') + \
            ' cylinder' + temp['startStop_flag'] + ' ' + temp['eng_dscr'] + ' engine, ' + \
            temp['fuelType1'] + ', ' + temp['trany'] + ' transmission, ' + \
            temp['city08'].astype('str') + '/' + temp['highway08'].astype('str') + ' city/highway MPG'
    
    label = [i for i in temp['label']]
    value = [i for i in temp.index]

    return [{'label': i, 'value': j} for i, j in zip(label, value)]

# Callback to get the value of the selected vehicle 1 model
@app.callback(
    Output('options_dropdown_1', 'value'),
    Input('options_dropdown_1', 'options'))
def set_final_model_1_value(available_options):
    return available_options[0]['value']

# Vehicle 2
# Callback to set the vehicle 2 make options based on the selected year
@app.callback(
    Output('make_dropdown_2', 'options'),
    Input('year_dropdown_2', 'value')
    )
def set_make_2_options(selected_year):
    return [{'label': i, 'value': i}
            for i in sorted(cars[cars['year'] == selected_year]['make'].unique())]

# Callback to get the value of the selected vehicle 2 make
@app.callback(
    Output('make_dropdown_2', 'value'),
    Input('make_dropdown_2', 'options'))
def set_make_2_value(available_options):
    return available_options[0]['value']

# Callback to set the vehicle 2 model options based on the selected make
@app.callback(
    Output('model_dropdown_2', 'options'),
    Input('make_dropdown_2', 'value'),
    Input('year_dropdown_2', 'value')
    )
def set_model_2_options(selected_make, selected_year):
    return [{'label': i, 'value': i}
            for i in sorted(cars[(cars['year'] == selected_year) & \
                                 (cars['make'] == selected_make)]['model'].unique())]

# Callback to get the value of the selected vehicle 2 model
@app.callback(
    Output('model_dropdown_2', 'value'),
    Input('model_dropdown_2', 'options'))
def set_model_2_value(available_options):
    return available_options[0]['value']

# Callback to set the final vehicle 2 options based on the selected model
@app.callback(
    Output('options_dropdown_2', 'options'),
    Input('make_dropdown_2', 'value'),
    Input('year_dropdown_2', 'value'),
    Input('model_dropdown_2', 'value')
    )
def set_final_model_2_options(selected_make, selected_year, selected_model):
    temp = cars[(cars['year'] == selected_year) & \
                                 (cars['make'] == selected_make) & \
                                 (cars['model'] == selected_model)]
    temp['startStop_flag'] = np.where(temp['startStop'] == 'Y', ' start/stop', '')


    if (temp['fuelType1'] == 'Electricity').all():
        temp['label'] = temp['drive'] + ', ' + temp['rangeCity'].astype('str') + '/' + \
            temp['rangeHwy'].astype('str') + ' mile city/highway range'
    else:
        temp['label'] = temp['displ'].astype('str') + ' liter ' + temp['cylinders'].astype('str') + \
            ' cylinder' + temp['startStop_flag'] + ' ' + temp['eng_dscr'] + ' engine, ' + \
            temp['fuelType1'] + ', ' + temp['trany'] + ' transmission, ' + \
            temp['city08'].astype('str') + '/' + temp['highway08'].astype('str') + ' city/highway MPG'
    
    label = [i for i in temp['label']]
    value = [i for i in temp.index]

    return [{'label': i, 'value': j} for i, j in zip(label, value)]

# Callback to get the value of the selected vehicle 2 model
@app.callback(
    Output('options_dropdown_2', 'value'),
    Input('options_dropdown_2', 'options'))
def set_final_model_2_value(available_options):
    return available_options[0]['value']


# test plot
@app.callback(
    Output(component_id='test_plot', component_property='figure'),
    Input(component_id='options_dropdown_1', component_property='value'),
    Input(component_id='options_dropdown_2', component_property='value'),
    Input('year_dropdown_1', 'value'))
def update_graph(selected_car_1, selected_car_2, selected_year):
    car1 = cars[cars.index == selected_car_1]
    xpos1 = car1.iloc[0]['comb08']
    car2 = cars[cars.index == selected_car_2]
    xpos2 = car2.iloc[0]['comb08']
#    hist_data = [ice[ice['year'] == selected_year]['comb08'], 
#                 phev[phev['year'] == selected_year]['comb08'], 
#                 hybrids[hybrids['year'] == selected_year]['comb08'], 
#                 ev[ev['year'] == selected_year]['comb08']]
    hist_data = [ice['comb08'], phev['comb08'], hybrids['comb08'], ev['comb08']]
    group_labels = ['Gas-Powered', 'Plug-in Hybrid', 'Hybrid', 'Electric']
    mpg_fig = ff.create_distplot(hist_data, group_labels, show_hist=False, show_rug=False)
    mpg_fig.add_vline(x=xpos1, line_width=3, line_color='green')
    mpg_fig.add_vline(x=xpos2, line_width=3, line_color='red')
    return mpg_fig

# Run on local server
if __name__ == '__main__':
    app.run_server(debug=True)