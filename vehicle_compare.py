#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Dec 20 20:10:13 2022

@author: richardbradshaw
"""

# Imports
# import time
import pandas as pd
import numpy as np
import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
import plotly.express as px

# Load Data

path = '/Users/richardbradshaw/Box/Python/01_Vehicles_Dash/'
# path = '/home/rbrad06/mysite/'

# vehicles database
cars = pd.read_csv(path + 'data/cars_database.csv', low_memory=(False))
# Drop cars with incomplete information
drop_index = cars[((cars['cylinders'].isnull()) & (cars['fuelType1'] != 'Electricity') 
      | (cars['trany'].isnull()) & (cars['fuelType1'] != 'Electricity') 
     | (cars['trany'].isnull()) & (cars['fuelType1'] != 'Electricity'))].index
cars = cars.drop(drop_index)
cars['trany_short'] = cars['trany'].replace({'Manual': 'Man', 
                                             'Automatic': 'Auto'}, regex=True)
cars['fuelType1_short'] = cars['fuelType1'].replace('Gasoline', 
                                                    'Gas', regex=True)

# separate vehicles into their separate types 
ev = cars[cars['fuelType1'] == 'Electricity']
ice = cars[(cars['fuelType1'] != 'Electricity') & 
           (cars['fuelType2'] != 'Electricity') & 
           (cars['atvType'] != 'Hybrid')]
phev = cars[cars['atvType'] == 'Plug-in Hybrid']
hybrids = cars[cars['atvType'] == 'Hybrid']

# gas and diesel prices
petrol_prices = pd.read_csv(path + 'data/petrol_prices.csv', index_col=0, parse_dates=['period'])
# petrol_prices['period'] = pd.to_datetime(petrol_prices['period'])
petrol_prices.rename(columns={'value': 'price'}, inplace=True)
# separate gas prices into their separate types
diesel = petrol_prices[petrol_prices['product-name'] == 'No 2 Diesel']
regular_gas = petrol_prices[petrol_prices['product-name'] == 
                            'Conventional Regular Gasoline']
premium_gas = petrol_prices[petrol_prices['product-name'] == 
                            'Conventional Premium Gasoline']
midgrade_gas = petrol_prices[petrol_prices['product-name'] == 
                             'Gasoline Conventional Midgrade']

# Electricity prices
electricity_prices = pd.read_csv(path + 'data/state_electricity.csv', index_col=0, 
                                 parse_dates=['period'])
us_elec = pd.read_csv(path + 'data/us_electricity.csv', index_col=0, 
                      parse_dates=['period'])


# Import state and US annual CO2 emissions
state_co2 = pd.read_csv(path + 'data/egrid_co2_all.csv', index_col=0)
us_co2_g_kwh = state_co2[state_co2['state'] == 'US']['co2_g/kWh'].iloc[0]


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

# Dictionary of EIA gasoline regions and the states that make up those regions
regions = {'PADD 1A': ['Connecticut', 'Maine', 'Massachusetts', 
                       'New Hampshire', 'Rhode Island', 'Vermont'], 
          'PADD 1B': ['Delaware', 'District of Columbia', 'Maryland', 
                      'New Jersey', 'Pennsylvania', 'New York'],
          'PADD 1C': ['Florida', 'Georgia', 'North Carolina', 'South Carolina', 
                      'Virginia', 'West Virginia'],
          'PADD 2': ['Illinois', 'Indiana', 'Iowa', 'Kansas', 'Kentucky', 
                     'Michigan', 'Missouri', 'Nebraska', 'North Dakota', 
                     'Oklahoma', 'South Dakota', 'Tennessee', 'Wisconsin', 
                     'Minnesota', 'Ohio'],
          'PADD 3': ['Alabama', 'Arkansas', 'Louisiana', 'Mississippi', 
                     'New Mexico', 'Texas'],
          'PADD 4': ['Colorado', 'Idaho', 'Montana', 'Utah', 'Wyoming'],
          'PADD 5': ['Alaska', 'Arizona', 'California', 'Hawaii', 
                     'Nevada', 'Oregon', 'Washington']}

# Add column of full state name to electricity_prices and state_co2
electricity_prices['state_name'] = electricity_prices['State'].map(states)
state_co2['state_name'] = state_co2['state'].map(states)

# Functions

def get_region(state):
    '''Function to return the PADD gasoline region that a state belongs to
    
    Args: 
        state(str): state name
        
    Returns:
        region name
    '''
    for region in regions.keys():
        if state in regions[region]:
            return region


def price_averages(electricity_price_df, gas_price_df, fuel_type):
    # average petroleum fuel prices and stds over the last 3 years
    electric_3_year_mean = round(electricity_price_df['price'].\
                                 iloc[-(52 * 3):].mean(), 2)

    electric_3_year_std = round(electricity_price_df['price'].\
                                iloc[-(52 * 3):].std(), 2)
    
    # average electricity fuel prices and stds over the last 3 years
    gas_3_year_mean = round(gas_price_df['price'].iloc[-(52 * 3):].mean(), 2)

    gas_3_year_std = round(gas_price_df['price'].iloc[-(52 * 3):].std(), 2)


    car_prices_averages = pd.DataFrame({'time_period': ['3year'], 
                                        'electricity_mean': electric_3_year_mean, 
                                        'electricity_std': electric_3_year_std,
                                        'gas_mean': gas_3_year_mean, 
                                        'gas_std': gas_3_year_std})

    return car_prices_averages


def fuel_costs(car_in, state_in, city_miles, highway_miles):
    
    car_name = str(car_in['year']) + ' ' + car_in['make'] + ' ' + car_in['model']
    
    fuel_type = car_in['fuelType1']
    
    # Get the region and US fuel prices based on fuelType1 of the vehicle
    if fuel_type == 'Regular Gasoline':
        region_car_fuel_prices = regular_gas[regular_gas['area-name'] == \
                                             get_region(state_in)]
        region_car_fuel_prices = region_car_fuel_prices.sort_values(by='period')
        us_car_fuel_prices = regular_gas[regular_gas['area-name'] == 'U.S.']
        us_car_fuel_prices = us_car_fuel_prices.sort_values(by='period')
    elif fuel_type == 'Premium Gasoline':
        region_car_fuel_prices = premium_gas[premium_gas['area-name'] == \
                                             get_region(state_in)]
        region_car_fuel_prices = region_car_fuel_prices.sort_values(by='period')
        us_car_fuel_prices = premium_gas[premium_gas['area-name'] == 'U.S.']
        us_car_fuel_prices = us_car_fuel_prices.sort_values(by='period')
    elif fuel_type == 'Midgrade Gasoline':
        region_car_fuel_prices = midgrade_gas[midgrade_gas['area-name'] == \
                                              get_region(state_in)]
        region_car_fuel_prices = region_car_fuel_prices.sort_values(by='period')
        us_car_fuel_prices = midgrade_gas[midgrade_gas['area-name'] == 'U.S.']
        us_car_fuel_prices = us_car_fuel_prices.sort_values(by='period')
    elif fuel_type == 'Diesel':
        region_car_fuel_prices = diesel[diesel['area-name'] == \
                                        get_region(state_in)]
        region_car_fuel_prices = region_car_fuel_prices.sort_values(by='period')
        us_car_fuel_prices = diesel[diesel['area-name'] == 'U.S.']
        us_car_fuel_prices = us_car_fuel_prices.sort_values(by='period')
    else:
        region_car_fuel_prices = electricity_prices[electricity_prices\
                                                    ['state_name'] == state_in]
        region_car_fuel_prices = region_car_fuel_prices.sort_values(by='period')
        us_car_fuel_prices = us_elec.sort_values(by='period')
        
    region_car_electric_prices = electricity_prices[electricity_prices\
                                                    ['state_name'] == state_in]
    region_car_electric_prices = region_car_electric_prices.\
        sort_values(by='period')
    us_car_electric_prices = us_elec.sort_values(by='period')
    

    # Average fuel prices for the last few years
    region_car_fuel_prices_averages = price_averages(region_car_electric_prices, 
                                                     region_car_fuel_prices, 
                                                     fuel_type)
    us_car_fuel_prices_averages = price_averages(us_car_electric_prices, 
                                                 us_car_fuel_prices, fuel_type)
    

    if car_in['fuelType1'] == 'Electricity':
        
        # electricity consumption in kWH/mile
        highway_E = car_in['highwayE'] / 100
        city_E = car_in['cityE'] / 100
        
        highway_electricity_consumption = highway_miles * highway_E
        city_electricity_consumption = city_miles * city_E
        
        # region fuel prices
        region_car_fuel_prices_averages['annual_cost'] = \
            round(((highway_miles * highway_E) + (city_miles * city_E)) 
                  * (region_car_fuel_prices_averages['electricity_mean'] 
                     / 100) * 365, 2)

        region_car_fuel_prices_averages['annual_cost_std'] = \
            round(((highway_miles * highway_E) + (city_miles * city_E)) 
                  * (region_car_fuel_prices_averages['electricity_std'] 
                     / 100) * 365, 2)
        
        # US fuel prices
        us_car_fuel_prices_averages['annual_cost'] = \
            round(((highway_miles * highway_E) + (city_miles * city_E)) 
                  * (us_car_fuel_prices_averages['electricity_mean'] / 100) 
                  * 365, 2)

        us_car_fuel_prices_averages['annual_cost_std'] = \
            round(((highway_miles * highway_E) + (city_miles * city_E)) 
                  * (us_car_fuel_prices_averages['electricity_std'] / 100) 
                  * 365, 2)
        
        # CO2 emissions in Kg
        car_co2_tailpipe = car_in['co2TailpipeGpm'] \
            * (city_miles + highway_miles)
        car_co2_state = round((highway_electricity_consumption 
                               + city_electricity_consumption) 
                              * state_co2[state_co2['state_name'] 
                                          == state_in]['co2_g/kWh'].iloc[0] 
                                  / 1000 * 365)
        car_co2_US = round(((highway_electricity_consumption 
                             + city_electricity_consumption) * us_co2_g_kwh) 
                           / 1000 * 365)
        
    elif car_in['atvType'] == 'Plug-in Hybrid':
        # electricity consumption in kWH / mile
        highway_E = car_in['highwayE'] / 100
        city_E = car_in['cityE'] / 100
        # gas fuel efficiency in MPG
        highway_mpg = car_in['highway08']
        city_mpg = car_in['city08']
        # Electric range
        range_highway = car_in['rangeHwyA']
        range_city = car_in['rangeCityA']
        
        # fraction of city driving vs highway driving
        city_drive_fraction = city_miles / (city_miles + highway_miles)
        highway_drive_fraction = 1 - city_drive_fraction
        
        # effective range (miles) based on the fraction of city vs 
        # highway driving
        effective_range = (city_drive_fraction * range_city) \
            + (highway_drive_fraction * range_highway)
        # effective electricity consumption in kWH/mile
        effective_efficiency = (city_drive_fraction * city_E) \
            + (highway_drive_fraction * highway_E)
        # electricity usage in kWH
        daily_electricity_usage = effective_range * effective_efficiency
        
        # Calculate gas range if total miles driven exceeds electric range
        if (city_miles + highway_miles) > effective_range:
            # gas range in miles after depleting batteries
            gas_range = (city_miles + highway_miles) - effective_range
            # effective fuel efficiency (MPG) based on fraction of city vs 
            # highway driving
            effective_mpg = (city_drive_fraction * city_mpg) \
                + (highway_drive_fraction * highway_mpg)
            # daily gas usage in gallons 
            daily_gas_usage = gas_range / effective_mpg
        else:
            # gas usage if batteries are never depleted
            daily_gas_usage = 0
        
        # region fuel prices and standard deviations
        region_car_fuel_prices_averages['annual_cost'] \
            = round(((daily_electricity_usage 
                    * region_car_fuel_prices_averages['electricity_mean'] 
                    / 100) + (daily_gas_usage 
                            * region_car_fuel_prices_averages['gas_mean'])) 
                            * 365, 2)
        
        region_car_fuel_prices_averages['annual_cost_std'] \
            = round(((daily_electricity_usage 
                    * region_car_fuel_prices_averages['electricity_std'] 
                    / 100) + (daily_gas_usage 
                            * region_car_fuel_prices_averages['gas_std'])) 
                            * 365, 2)
        
        # US fuel prices and standard deviations
        us_car_fuel_prices_averages['annual_cost'] \
            = round(((daily_electricity_usage 
                    * us_car_fuel_prices_averages['electricity_mean'] / 100) 
                   + (daily_gas_usage 
                    * us_car_fuel_prices_averages['gas_mean'])) * 365, 2)
        
        us_car_fuel_prices_averages['annual_cost_std'] \
            = round(((daily_electricity_usage 
                    * us_car_fuel_prices_averages['electricity_std'] / 100) 
                   + (daily_gas_usage 
                    * us_car_fuel_prices_averages['gas_std'])) * 365, 2)
        
        # CO2 emissions in grams
        if (city_miles + highway_miles) > effective_range:
            car_co2_tailpipe = round(car_in['co2TailpipeGpm'] * gas_range)
            car_co2_state = round(((car_in['co2TailpipeGpm'] * gas_range) 
                                   + (daily_electricity_usage 
                                    * state_co2[state_co2['state_name'] 
                                              == state_in]['co2_g/kWh'].iloc[0])) 
                                  / 1000 * 365)
            car_co2_US = round(((car_in['co2TailpipeGpm'] * gas_range) 
                                + (daily_electricity_usage * us_co2_g_kwh)) 
                               / 1000 * 365)
        else:
            car_co2_tailpipe = 0
            car_co2_state = round(((daily_electricity_usage 
                                    * state_co2[state_co2['state_name'] 
                                              == state_in]['co2_g/kWh'].iloc[0])) 
                                  / 1000 * 365)
            car_co2_US = round(((daily_electricity_usage * us_co2_g_kwh)) 
                               / 1000 * 365)
        
    else:
        # Fuel Efficiency
        highway_mpg = car_in['highway08']
        city_mpg = car_in['city08']
        
        # Region fuel prices
        region_car_fuel_prices_averages['annual_cost'] \
            = round(((highway_miles / highway_mpg) + (city_miles / city_mpg)) 
                    * 365 * region_car_fuel_prices_averages['gas_mean'], 2)
        

        region_car_fuel_prices_averages['annual_cost_std'] \
            = round(((highway_miles / highway_mpg) + (city_miles / city_mpg)) 
                    * 365 * region_car_fuel_prices_averages['gas_std'], 2)
        
        # US fuel prices
        us_car_fuel_prices_averages['annual_cost'] \
            = round(((highway_miles / highway_mpg) + (city_miles / city_mpg)) 
                    * 365 * us_car_fuel_prices_averages['gas_mean'], 2)

        us_car_fuel_prices_averages['annual_cost_std'] \
            = round(((highway_miles / highway_mpg) + (city_miles / city_mpg)) 
                    * 365 * us_car_fuel_prices_averages['gas_std'], 2)
        
        # CO2 emissions in Kg
        car_co2_tailpipe = round((car_in['co2TailpipeGpm'] 
                                  * (city_miles + highway_miles)) / 1000 * 365)
        car_co2_state = car_co2_tailpipe
        car_co2_US = car_co2_tailpipe

    region_car_fuel_prices_averages['area'] = state_in
    us_car_fuel_prices_averages['area'] = 'US'
    
    region_car_fuel_prices_averages['name'] = car_name
    us_car_fuel_prices_averages['name'] = car_name
    
    fuel_prices_averages = pd.concat([region_car_fuel_prices_averages, 
                                      us_car_fuel_prices_averages])
    fuel_prices_averages = fuel_prices_averages[['time_period', 'area', 
                                                 'annual_cost', 
                                                 'annual_cost_std', 'name']]
    
    return fuel_prices_averages, car_co2_state, car_co2_US, \
        car_co2_tailpipe, car_name

michael = cars[cars['id'] == 24008].iloc[0]
jim = cars[cars['id'] == 21018].iloc[0]

office1_costs, office1_co2_state, office1_co2_US, office1_co2_tailpipe, office1_name \
            = fuel_costs(michael, 'Pennsylvania', 15, 10)

office2_costs, office2_co2_state, office2_co2_US, office2_co2_tailpipe, office2_name \
            = fuel_costs(jim, 'Pennsylvania', 15, 10)



sources_text = '''## Sources 
[Gas prices](https://www.eia.gov/petroleum/)  
[Electricity prices](https://www.eia.gov/electricity/)  
[State CO2 emission rates](https://www.epa.gov/egrid/download-data)  
[Vehicles](https://www.fueleconomy.gov/)
[Source Code](https://github.com/richardbradshaw/cars_dash)'''

# Create Dash app
app = dash.Dash(external_stylesheets=[dbc.themes.BOOTSTRAP])

# Set up the app layout
app.layout = dbc.Container(
    [
          dbc.Row([
              dbc.Col([
                  html.H1('Vehicle Fuel Efficiency Comparison', 
                          style={'margin-top': 20}),
                  html.P('Richard Bradshaw'),
                  ], width=True, align='center'), 
              ]), 
          html.Hr(),
          dbc.Row([
              dbc.Col([
                  html.Div([
                      html.H6('State where you purchase fuel'),
                      dcc.Dropdown(id='state_dropdown', placeholder='Select State', 
                          options=[{'label': i, 'value': i}
                                  for i in sorted(states.values())]), 
                      html.H6('Daily city driving miles', style={'padding-top':10}),
                      dcc.Input(id='city_in', type='number', 
                                placeholder='City miles'),
                      html.H6('Daily highway driving miles', style={'padding-top':10}),
                      dcc.Input(id='highway_in', type='number', 
                      placeholder='Highway miles'),
                  ]),
                  html.Hr(),
                  html.Div([
                      html.H5('Vehicle 1'),
                      dcc.Dropdown(id='year_dropdown_1', 
                                  options=[{'label': n, 'value': n} 
                                            for n in sorted(cars['year'].unique(),
                                                      reverse=True)], 
                                  placeholder='Select Year'), 
                      dcc.Dropdown(id='make_dropdown_1', placeholder='Select Make'),
                      dcc.Dropdown(id='model_dropdown_1', placeholder='Select Model'),
                      dcc.Dropdown(id='options_dropdown_1', 
                                   placeholder='Select Options', 
                                   style={'font-size': '85%'}, optionHeight=50),
                      html.H5('Vehicle 2', style={'padding-top':10}),
                      dcc.Dropdown(id='year_dropdown_2', 
                                  options=[{'label': n, 'value': n} 
                                            for n in sorted(cars['year'].unique(),
                                                      reverse=True)], 
                                  placeholder='Select Year'), 
                      dcc.Dropdown(id='make_dropdown_2', placeholder='Select Make'),
                      dcc.Dropdown(id='model_dropdown_2', placeholder='Select Model'),
                      dcc.Dropdown(id='options_dropdown_2', 
                                   placeholder='Select Options', 
                                   style={'font-size': '85%'}, optionHeight=50),
                      dbc.Button(id='submit', children='Submit', n_clicks=0, 
                                 color='primary', size='lg', 
                                 style={'margin-top': 10}, 
                                 className="d-grid gap-2 col-6 mx-auto")
                      ]),
              ], width=4),
              dbc.Col([
                  dbc.Row([
                      dbc.Card([
                            dbc.CardBody([
                                html.H5('Summary'),
                                dcc.Markdown(id='summary_text'),
                            ]),
                        ]),
                      dbc.Col([
                          dcc.Graph(id='cost_plot', config={'autosizable': True}),
                      ],),
                      dbc.Col([
                          dcc.Markdown(id='car2_summary'),
                          dcc.Graph(id='co2_plot', config={'autosizable': True}), 
                      ]),
                      ]),
                  dbc.Row([
                      dbc.Card([
                          dbc.CardBody(
                              dcc.Markdown(id='summary_footnote', 
                                             style={'font-size': '90%'})
                              )]),
                      ]),
              ], width=True),
          ]),
          dbc.Row([
              dbc.Col([
                  html.Hr(),
                  dcc.Markdown(
                      sources_text
                  ),
              ])
          ]),
      ], 
    fluid=True
)



# Set up the callback functions

# Vehicle 1
# Callback to set the vehicle 1 make options based on the selected year
@app.callback(
    Output('make_dropdown_1', 'options'),
    Input('year_dropdown_1', 'value'))
def set_make_1_options(selected_year):
    if not selected_year:
        raise PreventUpdate
    return [{'label': i, 'value': i}
                for i in sorted(cars[cars['year'] == selected_year]['make'].unique())]


# Callback to get the value of the selected vehicle 1 make
@app.callback(
    Output('make_dropdown_1', 'value'),
    Input('make_dropdown_1', 'options'))
def set_make_1_value(available_options):
    if not available_options:
        raise PreventUpdate
    return available_options[0]['value']

# Callback to set the vehicle 1 model options based on the selected make
@app.callback(
    Output('model_dropdown_1', 'options'),
    Input('make_dropdown_1', 'value'),
    Input('year_dropdown_1', 'value')
    )
def set_model_1_options(selected_make, selected_year):
    if not selected_make:
        raise PreventUpdate
    return [{'label': i, 'value': i}
            for i in sorted(cars[(cars['year'] == selected_year) \
                                 & (cars['make'] == selected_make)]\
                            ['model'].unique())]

# Callback to get the value of the selected vehicle 1 model
@app.callback(
    Output('model_dropdown_1', 'value'),
    Input('model_dropdown_1', 'options'))
def set_model_1_value(available_options):
    if not available_options:
        raise PreventUpdate
    return available_options[0]['value']

# Callback to set the final vehicle 1 options based on the selected model
@app.callback(
    Output('options_dropdown_1', 'options'),
    Input('make_dropdown_1', 'value'),
    Input('year_dropdown_1', 'value'),
    Input('model_dropdown_1', 'value')
    )
def set_final_model_1_options(selected_make, selected_year, selected_model):
    if not selected_model:
        raise PreventUpdate
    temp = cars[(cars['year'] == selected_year) \
                & (cars['make'] == selected_make) \
                    & (cars['model'] == selected_model)]
    temp['startStop_flag'] = np.where(temp['startStop'] == 'Y', 
                                      ' start/stop', '')


    if (temp['fuelType1'] == 'Electricity').all():
        temp['label'] = temp['rangeCity'].astype('str') + '/' \
            + temp['rangeHwy'].astype('str') + ' mi city/hwy range'
    else:
        temp['label'] = temp['trany_short'] + ' ' + temp['displ'].astype('str') \
            + ' L ' + temp['cylinders'].astype('str') + ' cyl ' \
                + temp['fuelType1_short'] + ' ' + temp['startStop_flag']
                
    label = [i for i in temp['label']]
    value = [i for i in temp.index]

    return [{'label': i, 'value': j} for i, j in zip(label, value)]


# Callback to get the value of the selected vehicle 1 model
@app.callback(
    Output('options_dropdown_1', 'value'),
    Input('options_dropdown_1', 'options'))
def set_final_model_1_value(available_options):
    if not available_options:
        raise PreventUpdate
    return available_options[0]['value']


# Vehicle 2
# Callback to set the vehicle 2 make options based on the selected year
@app.callback(
    Output('make_dropdown_2', 'options'),
    Input('year_dropdown_2', 'value')
    )
def set_make_2_options(selected_year):
    if not selected_year:
        raise PreventUpdate
    return [{'label': i, 'value': i}
            for i in sorted(cars[cars['year'] \
                                 == selected_year]['make'].unique())]

# Callback to get the value of the selected vehicle 2 make
@app.callback(
    Output('make_dropdown_2', 'value'),
    Input('make_dropdown_2', 'options'))
def set_make_2_value(available_options):
    if not available_options:
        raise PreventUpdate
    return available_options[0]['value']

# Callback to set the vehicle 2 model options based on the selected make
@app.callback(
    Output('model_dropdown_2', 'options'),
    Input('make_dropdown_2', 'value'),
    Input('year_dropdown_2', 'value')
    )
def set_model_2_options(selected_make, selected_year):
    if not selected_make:
        raise PreventUpdate
    return [{'label': i, 'value': i}
            for i in sorted(cars[(cars['year'] == selected_year) & \
                                 (cars['make'] \
                                  == selected_make)]['model'].unique())]

# Callback to get the value of the selected vehicle 2 model
@app.callback(
    Output('model_dropdown_2', 'value'),
    Input('model_dropdown_2', 'options'))
def set_model_2_value(available_options):
    if not available_options:
        raise PreventUpdate
    return available_options[0]['value']

# Callback to set the final vehicle 2 options based on the selected model
@app.callback(
    Output('options_dropdown_2', 'options'),
    Input('make_dropdown_2', 'value'),
    Input('year_dropdown_2', 'value'),
    Input('model_dropdown_2', 'value')
    )
def set_final_model_2_options(selected_make, selected_year, selected_model):
    if not selected_model:
        raise PreventUpdate
    temp = cars[(cars['year'] == selected_year) & \
                                 (cars['make'] == selected_make) & \
                                 (cars['model'] == selected_model)]
    temp['startStop_flag'] = np.where(temp['startStop'] == 'Y', 
                                      ' start/stop', '')


    if (temp['fuelType1'] == 'Electricity').all():
        temp['label'] = temp['rangeCity'].astype('str') + '/' \
            + temp['rangeHwy'].astype('str') + ' mi city/hwy range'
    else:
        temp['label'] = temp['trany_short'] + ' ' + temp['displ'].astype('str') \
            + ' L ' + temp['cylinders'].astype('str') + ' cyl ' \
                + temp['fuelType1_short'] + ' ' + temp['startStop_flag']
    
    label = [i for i in temp['label']]
    value = [i for i in temp.index]

    return [{'label': i, 'value': j} for i, j in zip(label, value)]

# Callback to get the value of the selected vehicle 2 model
@app.callback(
    Output('options_dropdown_2', 'value'),
    Input('options_dropdown_2', 'options'))
def set_final_model_2_value(available_options):
    if not available_options:
        raise PreventUpdate
    return available_options[0]['value']


# Callback for the submit button
@app.callback(
    Output('cost_plot', 'figure'),
    Output('co2_plot', 'figure'),
    Output('summary_text', 'children'),
    Output('summary_footnote', 'children'),
    Input('submit', 'n_clicks'),
    State('options_dropdown_1', 'value'),
    State('options_dropdown_2', 'value'),
    State('state_dropdown', 'value'),
    State('city_in', 'value'),
    State('highway_in', 'value')
    )
def submit_calc(n_clicks, car_1_in, car_2_in, state_in, city_miles, 
                highway_miles):
    if n_clicks > 0:
        car1 = cars[cars.index == car_1_in].iloc[0]
        car2 = cars[cars.index == car_2_in].iloc[0]
        
        car1_costs, car1_co2_state, car1_co2_US, car1_co2_tailpipe, car1_name \
            = fuel_costs(car1, state_in, city_miles, highway_miles)
        car2_costs, car2_co2_state, car2_co2_US, car2_co2_tailpipe, car2_name \
            = fuel_costs(car2, state_in, city_miles, highway_miles)
            
        co2_all = pd.DataFrame({'tailpipe_co2': [car1_co2_tailpipe, 
                                                 car2_co2_tailpipe], 
                            'state_co2': [car1_co2_state, car2_co2_state], 
                            'US_co2': [car1_co2_US, car2_co2_US], 
                           'name': [car1_name, car2_name]})
        
        car_costs_all = pd.concat([car1_costs, car2_costs])
        
        fig_cost = px.bar(car_costs_all, y='annual_cost', x='name',
                          color='area', barmode='group', 
                          labels={'name': 'Vehicle', 
                                  'annual_cost': 'Annual Cost (USD)', 
                                  'area': ''}, 
                          color_discrete_map={state_in: '#636EFA', 'US': '#EF553B'}, 
                          template='plotly_white', 
                          hover_name=('name'), 
                          hover_data={'name': False, 
                                      'annual_cost': ':d'})
        fig_cost.update_layout(title_text='Annual Fuel Costs', title_x=0.5)
        
        
        fig_co2 = px.bar(co2_all, y='state_co2', x='name', 
                         labels={'name': 'Vehicle', 
                                 'state_co2': 'CO2 emissions in kg'}, 
                         template='plotly_white', 
                         hover_name=('name'), 
                         hover_data={'name': False})
        fig_co2.update_layout(title_text='Annual CO2 Emissions', title_x=0.5)
        fig_co2.update_traces(marker_color='#636EFA')
        
        car1_region_cost = round(car1_costs['annual_cost'].iloc[0])
        car2_region_cost = round(car2_costs['annual_cost'].iloc[0])
        
        car1_co2 = co2_all['tailpipe_co2'].iloc[0]
        car2_co2 = co2_all['tailpipe_co2'].iloc[1]
        car1_region_co2 = co2_all['state_co2'].iloc[0]
        car2_region_co2 = co2_all['state_co2'].iloc[1]
        
        if car1_region_cost > car2_region_cost:
            summary_name_1 = car1_name
            summary_name_2 = car2_name
            if (car1_region_cost / car2_region_cost) - 1 <= 1:
                percent_difference_cost = round(abs(100 * ((car1_region_cost 
                                                            / car2_region_cost) 
                                                           - 1)))
                percent_difference_co2 = round(abs(100 * ((car1_region_co2 
                                                           / car2_region_co2) 
                                                          - 1)))
                summary_text = '% more'
            else:
                percent_difference_cost = round(abs((car1_region_cost 
                                                     / car2_region_cost) 
                                                    - 1), 1)
                percent_difference_co2 = round(abs((car1_region_co2 
                                                    / car2_region_co2) 
                                                   - 1), 1)
                summary_text = ' times more'
        else:
            summary_name_1 = car2_name
            summary_name_2 = car1_name
            if (car2_region_cost / car1_region_cost) - 1 <= 1:
                percent_difference_cost = round(abs(100 * ((car2_region_cost 
                                                            / car1_region_cost) 
                                                           - 1)))
                percent_difference_co2 = round(abs(100 * ((car2_region_co2 
                                                           / car1_region_co2) 
                                                          - 1)))
                summary_text = '% more'
            else:
                percent_difference_cost = round(abs((car2_region_cost 
                                                     / car1_region_cost) 
                                                    - 1), 1)
                percent_difference_co2 = round(abs((car2_region_co2 
                                                    / car1_region_co2) 
                                                   - 1), 1)
                summary_text = ' times more'
            
        
        summary_text = f'''A {summary_name_1} costs **{percent_difference_cost} 
            {summary_text}** in fuel and emits **{percent_difference_co2} 
            {summary_text} CO2** than a {summary_name_2}.'''
        
        if ((car1['atvType'] == 'Plug-in Hybrid') \
            or (car2['atvType'] == 'Plug-in Hybrid')) \
            and ((car1['fuelType1'] == 'Electricity') \
            or (car2['fuelType1'] == 'Electricity')):
            summary_footnote = f'''Fuel costs are calculated using the 
            average fuel prices over the last 3 years in {state_in} and 
            the national average. Fuel costs for plug-in hybrids assume 
            that the battery is fully charged each day and that the battery
            is fully drained before switching to gas.
                Electric vehicles and Plug-in hybrids have no tailpipe CO2 
                emissions while running on electricity, the total 
                emissions in this analysis for a plug-in hybrid represent 
                the tailpipe CO2 emissions while running on gas plus the 
                electricity used to charge the battery multiplied by the 
                average CO2 emission rates from electricity generation in 
                {state_in}.  
                    The CO2 emissions for the electric vehicleis the 
                    electricity used to charge the vehicle multiplied by 
                    the average CO2 emission rates from electricity 
                    generation in {state_in}.'''
        
        elif (car1['fuelType1'] == 'Electricity') \
            or (car2['fuelType1'] == 'Electricity'):
            summary_footnote = f'''Fuel costs are calculated using the 
            average fuel prices over the last 3 years in {state_in} and 
            the national average.  
            Electric vehicles have no tailpipe CO2 
            emissions, the total emissions in this analysis represent the 
            electricity used to charge the vehicle 
            multiplied by the average CO2 emission rates from electricity 
            generation in {state_in}.'''
            
        elif (car1['atvType'] == 'Plug-in Hybrid') \
            or (car2['atvType'] == 'Plug-in Hybrid'):
            summary_footnote = f'''Fuel costs are calculated using the 
            average fuel prices over the last 3 years in {state_in} and 
            the national average. Fuel costs for plug-in hybrids assume 
            that the battery is fully charged each day and that the battery
            is fully drained before switching to gas.  
                Plug-in hybrids have no tailpipe CO2 emissions while 
                running on electricity, the total emissions in this analysis 
                for a plug-in hybrid represent the tailpipe CO2 
                emissions while running on gas plus the electricity used to 
                charge the battery multiplied by the average CO2 emission rates 
                from electricity generation in {state_in}.'''
        
        elif (car1['fuelType1'] == 'Electricity') \
            or (car2['fuelType1'] == 'Electricity'):
            summary_footnote = f'''Fuel costs are calculated using the 
            average fuel prices over the last 3 years in {state_in} and 
            the national average.  
            Electric vehicles have no tailpipe CO2 
            emissions, the total emissions in this analysis represent the 
            electricity used to charge the vehicle 
            multiplied by the average CO2 emission rates from electricity 
            generation in {state_in}.'''
            
        else:
            summary_footnote = f'''Fuel costs are calculated using the 
            average fuel prices over the last 3 years in {state_in} and 
            the national average.'''

    else:
        co2_all = pd.DataFrame({'tailpipe_co2': [office1_co2_tailpipe, 
                                                 office2_co2_tailpipe], 
                            'state_co2': [office1_co2_state, office2_co2_state], 
                            'US_co2': [office1_co2_US, office2_co2_US], 
                           'name': [office1_name, office2_name]})
        
        car_costs_all = pd.concat([office1_costs, office2_costs])
        
        fig_cost = px.bar(car_costs_all, y='annual_cost', x='name',
                          color='area', barmode='group', 
                          labels={'name': 'Vehicle', 
                                  'annual_cost': 'Annual Cost (USD)', 
                                  'area': ''}, 
                          color_discrete_map={'Pennsylvania': '#636EFA', 'US': '#EF553B'}, 
                          template='plotly_white', 
                          hover_name=('name'), 
                          hover_data={'name': False, 
                                      'annual_cost': ':d'})
        fig_cost.update_layout(title_text='Annual Fuel Costs', title_x=0.5)
        
        
        fig_co2 = px.bar(co2_all, y='state_co2', x='name', 
                         labels={'name': 'Vehicle', 
                                 'state_co2': 'CO2 emissions in kg'}, 
                         template='plotly_white', 
                         hover_name=('name'), 
                         hover_data={'name': False})
        fig_co2.update_layout(title_text='Annual CO2 Emissions', title_x=0.5)
        fig_co2.update_traces(marker_color='#636EFA')
        
        
        car1_region_cost = round(office1_costs['annual_cost'].iloc[0])
        car2_region_cost = round(office2_costs['annual_cost'].iloc[0])
        
        if car1_region_cost < car2_region_cost:
            difference_cost = 'less'
        else:
            difference_cost = 'more'
        
        car1_co2 = co2_all['tailpipe_co2'].iloc[0]
        car2_co2 = co2_all['tailpipe_co2'].iloc[1]
        car1_region_co2 = co2_all['state_co2'].iloc[0]
        car2_region_co2 = co2_all['state_co2'].iloc[1]
        
        
        if car1_co2 < car2_co2:
            difference_co2 = 'less'
        else:
            difference_co2 = 'more'
        
        percent_difference_cost = round(abs((car1_region_cost - car2_region_cost) / 
                                       ((car1_region_cost + car2_region_cost) / 2)) * 100)
        percent_difference_co2 = round(abs((car1_co2 - car2_co2) / 
                                       ((car1_co2 + car2_co2) / 2)) * 100)
        
        summary_text = f'''A {office1_name} costs **{percent_difference_cost}% 
        {difference_cost}** in fuel and emits **{percent_difference_co2}% 
        {difference_co2} CO2** than a {office2_name}, based on 
        driving 15 city miles and 10 highway miles per day in Scranton, 
        Pennsylvania.'''
        
        summary_footnote = '''Fuel costs are calculated using the 
            average fuel prices over the last 3 years in Pennsylvania and 
            the national average.'''
        
    return fig_cost, fig_co2, summary_text, summary_footnote
    

# Run on local server
if __name__ == '__main__':
    app.run_server(debug=True)