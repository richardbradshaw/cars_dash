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
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
import plotly.figure_factory as ff
import plotly.express as px


# Load Data
# url_cars = 'https://www.fueleconomy.gov/feg/epadata/vehicles.csv'
# cars = pd.read_csv(url_cars, low_memory=False)
# vehicles database
cars = pd.read_csv('cars_database.csv', low_memory=(False))
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
petrol_prices = pd.read_csv('petrol_prices.csv', index_col=0)
petrol_prices['period'] = pd.to_datetime(petrol_prices['period'])
petrol_prices.rename(columns={'value': 'price'}, inplace=True)
# separate gas prices into their separate types
diesel = petrol_prices[petrol_prices['product-name'] == 'No 2 Diesel']
regular_gas = petrol_prices[petrol_prices['product-name'] == 
                            'Conventional Regular Gasoline']
premium_gas = petrol_prices[petrol_prices['product-name'] == 
                            'Conventional Premium Gasoline']
midgrade_gas = petrol_prices[petrol_prices['product-name'] == 
                             'Gasoline Conventional Midgrade']

# Get monthly residential electricity data
electricity_prices = pd.read_excel('electricity_sales_revenue.xlsx', 
                                   sheet_name='Monthly-States', 
                                   usecols='A:D, H', 
                            skiprows=2, skipfooter=1, 
                            parse_dates= {"period" : ["Year","Month"]},)

us_elec = pd.read_excel('electricity_sales_revenue.xlsx', 
                        sheet_name='US-YTD', usecols='A:C, G', 
                            skiprows=2, skipfooter=1)#, parse_dates= {"Date" : ["Year","Month"]},)

# Price in Cents/kWh
electricity_prices = electricity_prices.rename(columns={'Cents/kWh': 'price'})
us_elec = us_elec.rename(columns={'Cents/kWh': 'price'})

# Remove yearly average
us_elec = us_elec[us_elec['MONTH'] != '.']

# Change date information into Datetime
us_elec['day'] = '1'
us_elec['period'] = pd.to_datetime(us_elec[['Year', 'MONTH', 'day']])
us_elec = us_elec.drop(['Year', 'MONTH', 'day'], axis=1)

# Import state annual CO2 emissions in lb/MWh
col = ['State abbreviation', 
       'State annual CO2 equivalent total output emission rate (lb/MWh)']
state_co2 = pd.read_excel('egrid2020_data.xlsx', sheet_name='ST20', 
                          usecols=col)
state_co2 = state_co2.drop(labels=0)
cols={'State abbreviation': 'state', 
      'State annual CO2 equivalent total output emission rate (lb/MWh)': 
          'co2_lb/MWh'}
state_co2 = state_co2.rename(columns=cols)
# Convert from emissions in lb/MWh to g/kWh
state_co2['co2_g/kWh'] = state_co2['co2_lb/MWh'] / 1000 * 453.59

# Import US annual CO2 emissions in lb/MWh
col = ['U.S. annual CO2 equivalent total output emission rate (lb/MWh)']
us_co2 = pd.read_excel('egrid2020_data.xlsx', sheet_name='US20', usecols=col)
us_co2 = us_co2[col].iloc[1]
# Convert from emissions in lb/MWh to g/kWh
us_co2_g_kwh = us_co2 / 1000 * 435.59




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
    # average petroleum fuel prices and stds over the last few years
    electric_3_year_mean = round(electricity_price_df['price'].\
                                 iloc[-(52 * 3):].mean(), 2)

    electric_3_year_std = round(electricity_price_df['price'].\
                                iloc[-(52 * 3):].std(), 2)
    
    # average electricity fuel prices and stds over the last few years
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
    
    
#     return region_car_fuel_prices_averages, us_car_fuel_prices_averages, 
#     car_co2_state, car_co2_US, car_co2_tailpipe
    return fuel_prices_averages, car_co2_state, car_co2_US, \
        car_co2_tailpipe, car_name

michael = cars[cars['id'] == 24008].iloc[0]
jim = cars[cars['id'] == 21018].iloc[0]

michael_costs, michael_co2_state, michael_co2_US, michael_co2_tailpipe, michael_name \
            = fuel_costs(michael, 'Pennsylvania', 15, 10)

jim_costs, jim_co2_state, jim_co2_US, jim_co2_tailpipe, jim_name \
            = fuel_costs(jim, 'Pennsylvania', 15, 10)


# Create Dash app
app = dash.Dash(external_stylesheets=[dbc.themes.BOOTSTRAP])



# Set up the app layout
app.layout = dbc.Container(
    [
          dbc.Row([
              dbc.Col([
                  html.H1('Vehicle Fuel Efficiency Comparison'),
                  html.H5('Richard Bradshaw'),
                  ], width=True, align='center'), 
              ], justify='center'), 
          html.Hr(),
          dbc.Row([
              dbc.Col([
                  html.Div([
                      html.H6('State where you purchase fuel'),
                      dcc.Dropdown(id='state_dropdown', placeholder='Select State', 
                          options=[{'label': i, 'value': i}
                                  for i in sorted(states.values())]), 
                      html.H6('Daily city driving miles'),
                      dcc.Input(id='city_in', type='number', 
                                placeholder='City miles'),
                      html.H6('Daily highway driving miles'),
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
                      html.H5('Vehicle 2'),
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
                      html.Button(id='submit', children='Submit', n_clicks=0),
                      ]),
              ], width=4),
              dbc.Col([
                  dbc.Row([
                      dbc.Col([
                          dcc.Markdown(id='cost_summary'),
                          dcc.Graph(id='cost_plot', config={'autosizable': True}),
                      ],),
                      
                      dbc.Col([
                          dcc.Markdown(id='co2_summary'),
                          dcc.Graph(id='co2_plot', config={'autosizable': True}), 
                      ]),
                      ]),
              ], width=True),
              # dbc.Col([
              #     dcc.Markdown(id='summary')]),
          ]),
          dbc.Row([
              dbc.Col([
                  html.Hr(),
                  html.P(
                      'Sources...'
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
    Input('year_dropdown_1', 'value')
    )
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
            for i in sorted(cars[(cars['year'] == selected_year) & (cars['make'] == selected_make)]['model'].unique())]

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
        
        # temp['label'] = temp['displ'].astype('str') + ' liter ' \
        #     + temp['cylinders'].astype('str') + ' cylinder' \
        #         + temp['startStop_flag'] + ' engine, ' + temp['fuelType1'] \
        #             + ', ' + temp['trany'] + ' transmission, ' \
        #                 + temp['city08'].astype('str') \
        #                     + '/' + temp['highway08'].astype('str') \
        #                         + ' city/highway MPG'
    
    
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
    # Output('co2_out', 'value'),
    # Output('costs_out', 'value'),
    Output('cost_plot', 'figure'),
    Output('co2_plot', 'figure'),
    Output('cost_summary', 'children'), 
    Output('co2_summary', 'children'), 
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
                          color_discrete_map={state_in: 'blue', 'US': 'red'}, 
                          template='plotly_white')
        fig_cost.update_layout(title_text='Annual Fuel Costs', title_x=0.5)
        
        
        fig_co2 = px.bar(co2_all, y='state_co2', x='name', 
                         color_discrete_map={'name': 'blue'}, 
                         labels={'name': 'Vehicle', 
                                 'state_co2': 'CO2 emissions in kg'}, 
                         template='plotly_white')
        fig_co2.update_layout(title_text='Annual CO2 Emissions', title_x=0.5)
        fig_co2.update_traces(marker_color='blue')
        
        cost_summary = f'''## Summary
        
        The {car1_name} would emit {co2_all['tailpipe_co2'][0]} 
        Kg of CO2 per year.
        '''
        
        co2_summary = 'co2_test'

        return fig_cost, fig_co2
        # return summary_text
    else:
        co2_all = pd.DataFrame({'tailpipe_co2': [michael_co2_tailpipe, 
                                                 jim_co2_tailpipe], 
                            'state_co2': [michael_co2_state, jim_co2_state], 
                            'US_co2': [michael_co2_US, jim_co2_US], 
                           'name': [michael_name, jim_name]})
        
        car_costs_all = pd.concat([michael_costs, jim_costs])
        
        fig_cost = px.bar(car_costs_all, y='annual_cost', x='name',
                          color='area', barmode='group', 
                          labels={'name': 'Vehicle', 
                                  'annual_cost': 'Annual Cost (USD)', 
                                  'area': ''}, 
                          color_discrete_map={'Pennsylvania': 'blue', 'US': 'red'}, 
                          template='plotly_white')
        fig_cost.update_layout(title_text='Annual Fuel Costs', title_x=0.5)
        
        
        fig_co2 = px.bar(co2_all, y='state_co2', x='name', 
                         color_discrete_map={'name': 'blue'}, 
                         labels={'name': 'Vehicle', 
                                 'state_co2': 'CO2 emissions in kg'}, 
                         template='plotly_white')
        fig_co2.update_layout(title_text='Annual CO2 Emissions', title_x=0.5)
        fig_co2.update_traces(marker_color='blue')
        
        cost_summary = 'The Office Costs test'
        co2_summary = 'The Office CO2 test'
        
        return fig_cost, fig_co2, cost_summary, co2_summary
    
    # return co2_all, car_costs_all


# # test plot
# @app.callback(
#     Output(component_id='cost_plot', component_property='figure'),
#     Input(component_id='costs_out', component_property='value'),
#     Input('state_dropdown', 'value'))
# def update_graph(car_costs_all, state_in):
#     fig = px.bar(car_costs_all, y='annual_cost', x='name',
#        color='area', barmode='group', 
#       labels={'name': 'Vehicle', 'annual_cost': 'Annual Cost (USD)', 'area': ''}, 
#       color_discrete_map={state_in: 'blue', 'US': 'red'}, template='plotly_white')
#     fig.update_layout(title_text='Annual Fuel Costs', title_x=0.5)

#     return fig

# # test plot
# @app.callback(
#     Output(component_id='cost_plot', component_property='figure'),
#     Input(component_id='options_dropdown_1', component_property='value'),
#     Input(component_id='options_dropdown_2', component_property='value'),
#     Input('year_dropdown_1', 'value'))
# def update_graph(car_1_in, car_2_in, selected_year):
#     car1 = cars[cars.index == car_1_in]
#     xpos1 = car1.iloc[0]['comb08']
#     car2 = cars[cars.index == car_2_in]
#     xpos2 = car2.iloc[0]['comb08']
# #    hist_data = [ice[ice['year'] == selected_year]['comb08'], 
# #                 phev[phev['year'] == selected_year]['comb08'], 
# #                 hybrids[hybrids['year'] == selected_year]['comb08'], 
# #                 ev[ev['year'] == selected_year]['comb08']]
#     hist_data = [ice['comb08'], phev['comb08'], hybrids['comb08'], 
#                  ev['comb08']]
#     group_labels = ['Gas-Powered', 'Plug-in Hybrid', 'Hybrid', 'Electric']
#     mpg_fig = ff.create_distplot(hist_data, group_labels, show_hist=False, 
#                                  show_rug=False)
#     mpg_fig.add_vline(x=xpos1, line_width=3, line_color='green')
#     mpg_fig.add_vline(x=xpos2, line_width=3, line_color='red')
#     return mpg_fig

# Run on local server
if __name__ == '__main__':
    app.run_server(debug=True)