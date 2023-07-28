'''
class containing all infrastruture related parameters
-fuel price

'''

import pandas as pd
#pd.set_option('max_columns', None)
pd.options.display.max_columns = None

import os

dirname = os.path.dirname(__file__)

class Infrastructure:
    
    def __init__(self, scenario):
        #$/DGE
        self.DV_fuel_prices = pd.read_csv(dirname + "/input/" + scenario + "/infrastructure/DV_fuel_prices.csv").set_index("Year").to_dict('series')
        self.BEV_fuel_prices = pd.read_csv(dirname + "/input/" + scenario + "/infrastructure/BEV_fuel_prices.csv").set_index("Year").to_dict('series')
        self.FCHEV_fuel_prices = pd.read_csv(dirname + "/input/" + scenario + "/infrastructure/FCHEV_fuel_prices.csv").set_index("Year").to_dict('series')
        self.FCHEV_station_availability = pd.read_csv(dirname + "/input/" + scenario + "/infrastructure/FCHEV_station_availability.csv").set_index("Year").to_dict('series')
        self.TCO_rate = pd.read_csv(dirname + "/input/" + scenario + "/infrastructure/TCO_rate.csv").set_index("Year").to_dict('series')

        self.capital = pd.read_csv(dirname + "/input/" + scenario + "/infrastructure/capital.csv").set_index("Year").to_dict('series')
        self.carbon_intensity = pd.read_csv(dirname + "/input/" + scenario + "/infrastructure/carbon_intensity.csv").set_index("Year").to_dict('series')
        self.BEV_charging_power = pd.read_csv(dirname + "/input/" + scenario + "/infrastructure/BEV_charging_power.csv").set_index("Year").to_dict('series')
        self.BEV_queue_time = pd.read_csv(dirname + "/input/" + scenario + "/infrastructure/BEV_queue_time.csv").set_index("Year").to_dict('series')
    
        '''
        units:
            fuel_prices
                diesel - $/DGE
                electricity - $/DGE
            capital
                $/DGE
            carbon_intensity
                diesel - kgs/DGE
                electricity - kgs/kWh
            BEV_charging_power
                KW
            BEV_queue_time
                hours
        '''