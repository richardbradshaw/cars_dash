#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Dec 20 20:10:13 2022

@author: richardbradshaw
"""

# Imports
import pandas as pd
import numpy as np
import plotly.express as px
import dash
from dash import dcc, html
from dash.dependencies import Input, Output


# Get vehicles database
# url_cars = 'https://www.fueleconomy.gov/feg/epadata/vehicles.csv'
# cars = pd.read_csv(url_cars, low_memory=False)
cars = pd.read_csv('cars_database.csv', low_memory=(False))


# Create Dash app
app = dash.Dash()

# Set up the app layout
app.layout = html.Div(children=[
    html.H1(children='Fuel Efficiency Comparison'),
    html.H2('Vehicle 1'),
    html.H4('Year'),
    dcc.Dropdown(id='year_dropdown_1',
                 options=[{'label': n, 'value': n}
                         for n in sorted(cars['year'].unique(),reverse=True)],
                 value='2022'),
    html.H4('Make'),
    dcc.Dropdown(id='make_dropdown_1'),
    html.H4('Model'),
    dcc.Dropdown(id='model_dropdown_1'),
    dcc.Dropdown(id='options_dropdown_1'),
    html.Div(id='test_output'),
    dcc.Graph(id='test_plot'),
    ])

# Set up the callback function

# Callback to set the make options based on the selected year
@app.callback(
    Output('make_dropdown_1', 'options'),
    Input('year_dropdown_1', 'value')
    )
def set_make_1_options(selected_year):
    return [{'label': i, 'value': i}
            for i in sorted(cars[cars['year'] == selected_year]['make'].unique())]

# Callback to get the value of the selected make
@app.callback(
    Output('make_dropdown_1', 'value'),
    Input('make_dropdown_1', 'options'))
def set_make_1_value(available_options):
    return available_options[0]['value']

# Callback to set the model options based on the selected make
@app.callback(
    Output('model_dropdown_1', 'options'),
    Input('make_dropdown_1', 'value'),
    Input('year_dropdown_1', 'value')
    )
def set_model_1_options(selected_make, selected_year):
    return [{'label': i, 'value': i}
            for i in sorted(cars[(cars['year'] == selected_year) & \
                                 (cars['make'] == selected_make)]['model'].unique())]

# Callback to get the value of the selected model
@app.callback(
    Output('model_dropdown_1', 'value'),
    Input('model_dropdown_1', 'options'))
def set_model_1_value(available_options):
    return available_options[0]['value']

# Callback to set the final vehicle options based on the selected model
@app.callback(
    Output('options_dropdown_1', 'options'),
    Input('make_dropdown_1', 'value'),
    Input('year_dropdown_1', 'value'),
    Input('model_dropdown_1', 'value')
    )
def set__final_model_1_options(selected_make, selected_year, selected_model):
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


#    return [{'label': i, 'value': i}
#            for [i,j] in sorted(temp['label', 'model'])]

#            for i in sorted(cars[(cars['year'] == selected_year) & \
 #                                (cars['make'] == selected_make) & \
  #                               (cars['model'] == selected_model)]['cylinders'].unique())]

# Callback to get the value of the selected model
@app.callback(
    Output('options_dropdown_1', 'value'),
    Input('options_dropdown_1', 'options'))
def set_final_model_1_value(available_options):
    return available_options[0]['value']

#@app.callback(
#    Output(component_id='test_plot', component_property='figure'),
#    Input(component_id='year_dropdown_1', component_property='value'),
#    Input(component_id='make_dropdown_1', component_property='value'))
#def update_graph(selected_year, selected_make):
#    filtered_year = cars[cars['year'] == selected_year]
#    filtered_make = filtered_year[filtered_year['make'] == selected_make]
#    mpg_fig = px.histogram(filtered_make,
#                         x='comb08', 
#                         title=f'MPG for {selected_year} {selected_make} vehicles')
#    return mpg_fig

@app.callback(
    Output('test_output', 'children'),
    Input('options_dropdown_1', 'value'))

@app.callback(
    Output(component_id='test_plot', component_property='figure'),
    Input(component_id='options_dropdown_1', component_property='value'))
def update_graph(selected_options):
    filtered_year = cars[cars['year'] == selected_year]
    filtered_make = filtered_year[filtered_year['make'] == selected_make]
    mpg_fig = px.histogram(filtered_make,
                         x='comb08', 
                         title=f'MPG for {selected_year} {selected_make} vehicles')
    return mpg_fig

# Run on local server
if __name__ == '__main__':
    app.run_server(debug=True)