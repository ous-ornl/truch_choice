'''
class containing all policies related parameters
-incentive on BEV purchase (% of BEV price)
-annual incentive on charging infrastructure (% of $/DGE)

'''

import pandas as pd
import os
#pd.set_option('max_columns', None)
pd.options.display.max_columns = None

dirname = os.path.dirname(__file__)

class Policy:

    def __init__(self, scenario):
        self.BEV_incentive = pd.read_csv(dirname + "/input/" + scenario + "/policy/BEV_incentive.csv").set_index("Year").to_dict('series')
        self.charging_incentive = pd.read_csv(dirname + "/input/" + scenario + "/policy/charging_incentive.csv").set_index("Year").to_dict('series')
        
 
    

