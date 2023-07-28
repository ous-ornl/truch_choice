import pandas as pd
import numpy.random as rand
#pd.set_option('max_columns', None)
pd.options.display.max_columns = None

import os

dirname = os.path.dirname(__file__)

class Truck_Segment_Generator:
    
    def __init__(self, seed, scenario):
        self.summary = pd.read_csv(dirname + "/input/" + scenario + "/segments.csv")
        self.list_of_segments = self.summary.to_dict('records')
        rand.seed(seed)
    
    def generate_samples_for_all_segments(self, *output_files):
        print("processing segment 0")
        ans = self.generate_samples_df_per_segment(self.list_of_segments[0])
        for i in range(1, len(self.list_of_segments)):
            print("processing segment " + str(i))
            ans = pd.concat([ans, self.generate_samples_df_per_segment(self.list_of_segments[i])], axis=0)
        
        for file in output_files:
            ans.to_csv(file, index = None, header=True)
        return ans
    
    def generate_samples_df_per_segment(self, d):
        list_of_samples = []
        Segment = d["Segment"]
        Sale = d["Sale"] / d["Sample_size"]
        Annual_mile_distribution = d["Annual_mile_distribution"] #miles
        Annual_mile_avg = d["Annual_mile_avg"] #miles
        Annual_mile_STD = d["Annual_mile_STD"] #miles
        Discount_rate_distribution = d["Discount_rate_distribution"]
        Discount_rate_avg = d["Discount_rate_avg"]
        Discount_rate_STD = d["Discount_rate_STD"]
        BEV_cost_adjust_2020_distribution = d["BEV_cost_adjust_2020_distribution"]
        BEV_cost_adjust_2020_avg = d["BEV_cost_adjust_2020_avg"]
        BEV_cost_adjust_2020_std = d["BEV_cost_adjust_2020_std"]
        refuel_time_avail_distribution = d["refuel_time_avail_distribution"]
        refuel_time_avail_avg = d["refuel_time_avail_avg"]      #hours
        refuel_time_avail_std = d["refuel_time_avail_std"]
        time_penalty_distribution = d["time_penalty_distribution"]
        time_penalty_avg = d["time_penalty_avg"]    #$/hour
        time_penalty_std = d["time_penalty_std"]
        
        
    
        for i in range(0, d["Sample_size"]):
            x = {"Segment" : Segment,
                 "ID" : i + 1,
                 "Sale" : Sale,
                 "Annual_mile" : self.get_random_value(Annual_mile_distribution, Annual_mile_avg, Annual_mile_STD),
                 "Discount_rate" : self.get_random_value(Discount_rate_distribution, Discount_rate_avg, Discount_rate_STD),
                 "BEV_cost_adjust_2020" : self.get_random_value(BEV_cost_adjust_2020_distribution, BEV_cost_adjust_2020_avg, BEV_cost_adjust_2020_std),
                 "refuel_time_avail" : self.get_random_value(refuel_time_avail_distribution, refuel_time_avail_avg, refuel_time_avail_std),
                 "time_penalty" : self.get_random_value(time_penalty_distribution, time_penalty_avg, time_penalty_std)
                 }

            list_of_samples.append(x)
        df = pd.DataFrame.from_dict(list_of_samples)[list (list_of_samples[0].keys())]
        df["Annual_mile_avg"] = Annual_mile_avg
        df["Lifetime"] = d["Lifetime"]
        df['Maintainence_DV'] = d['Maintainence_DV'] #$/veh
        df['Maintainence_BEV'] = d['Maintainence_BEV']
        df['Maintainence_FCHEV'] = d['Maintainence_BEV']
        
        df["Idling_hour"] = d["Idling_hour"] #hours
        df["Other_incentive_2020"] = d["Other_incentive_2020"]
        df["Other_incentive_yearly_change"] = (d["Other_incentive_2050"] - d["Other_incentive_2020"]) / 30
        return df
    
    
    #get random number based on distribution name "name", mean, and standard deviation
    def get_random_value(self, name, mean, std):
        if name == "normal":
            ans = rand.normal(mean, std)
            return ans if ans > 0 else 0
        elif name == "gamma": 
            scale = std * std / mean
            shape = mean / scale
            return rand.gamma(shape, scale)
        else:
            return -1
