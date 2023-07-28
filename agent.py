from infrastructure import Infrastructure
from vehicle import Vehicle
from policy import Policy
import copy

class Agent:
    
    kWhperDGE = 37.95      #kWh per diesel gallon equivalent
    
    def __init__(self, truck_agent_dict, year, infrastructure, vehicle, policy):
        
        self.tad = copy.copy(truck_agent_dict)
        self.tech_pool = ["DV", "BEV", "FCHEV"]
        self.tad["year"] = year
        self.tad["TCO"] = {tech : 0 for tech in self.tech_pool}
        self.tad["Vechicle_Cost"] = {tech : 0 for tech in self.tech_pool}
        self.tad["Fuel_Cost"] = {tech : 0 for tech in self.tech_pool}
        self.tad["Refuel_Cost"] = {tech : 0 for tech in self.tech_pool}

        self.tad["annual_average_energy"] = {tech: 0 for tech in self.tech_pool}
        self.tad["BEV_incentive"] = 0
        self.infrastructure = infrastructure #fuel_prices["diesel"][2020],capital["Sleeper"][2020]
        self.vehicle = vehicle #BEV_prices, DV_prices, BEV_consumption, DV_consumption["Sleeper"][2020]
        self.policy = policy #BEV_incentive["Day_cab"][2020]     charging_incentive["Bus"][2020]
        
        self.BEV_cost_adjust = self.tad["BEV_cost_adjust_2020"] + (1 - self.tad["BEV_cost_adjust_2020"]) / 30 * (year  - 2020)
        #print(self.tad["year"])
    '''
    tad components: 
        
    "Segment" : Segment,
    "ID" : i + 1,
    "Sale" : Sale,
    "Annual_mile" : self.get_random_value(Annual_mile_distribution, Annual_mile_avg, Annual_mile_STD),
    "Discount_rate" : self.get_random_value(Discount_rate_distribution, Discount_rate_avg, Discount_rate_STD)
    df["Annual_mile_avg"] = Annual_mile_avg
    df["Lifetime"] = d["Lifetime"]
    df['Maintainence_DV'] = d['Maintainence_DV']
    df['Maintainence_BEV'] = d['Maintainence_BEV']
    
    '''

    def calculate(self):
        for tech in self.tech_pool:
            self.tad["TCO"][tech] = self.get_tco_by_tech(tech)
            self.tad["Vechicle_Cost"][tech]  = self.get_vehicle_cost(tech)
            self.tad["Fuel_Cost"][tech]  = self.get_PV_fuel_cost(tech)
            self.tad["Refuel_Cost"][tech]  = self.get_PV_refueling_cost(tech)
            self.tad["annual_average_energy"][tech] = self.get_average_energy_use_by_tech(tech)
            self.tad["BEV_incentive"] = self.get_BEV_incentive()

    
    def get_results(self):
        return copy.copy(self.tad)
    
#cost components
    #total TCO (present value, $), tech - Diesel, BEV, verified
    def get_tco_by_tech(self, tech):  
        
        #print(tech, self.get_vehicle_cost(tech), '    ', self.get_PV_fuel_cost(tech), '    ',self.get_PV_refueling_cost(tech), '    ', self.get_maintainence_cost(tech))      
        
        return self.get_vehicle_cost(tech) + self.get_PV_fuel_cost(tech) + self.get_PV_refueling_cost(tech) + self.get_maintainence_cost(tech) # + self.get_other_incentive_cost(tech)

    
    #ver2 - total fuel cost (present value, $), tech - Diesel, BEV, verified
    def get_vehicle_cost(self, tech):
        if tech == "DV":
            return round(self.vehicle.DV_prices[self.tad["Segment"]][self.tad["year"]])
        elif tech =="FCHEV":
            return round(self.vehicle.FCHEV_prices[self.tad["Segment"]][self.tad["year"]])
        else:
            return round(self.vehicle.BEV_prices[self.tad["Segment"]][self.tad["year"]]) # * self.BEV_cost_adjust * (1 - self.policy.BEV_incentive[self.tad["Segment"]][self.tad["year"]])
    
    #ver 3 - incentive to BEV cost ($), verified
    def get_BEV_incentive(self):
        return self.vehicle.BEV_prices[self.tad["Segment"]][self.tad["year"]] * self.BEV_cost_adjust * self.policy.BEV_incentive[self.tad["Segment"]][self.tad["year"]]
    
    #ver 2 - get present value of fuel cost ($, consumers take current year's fuel price as the basis for future years), verfied        
    def get_PV_fuel_cost(self, tech):
        temp_fuel_price = 0 #$/DGE
        if tech == "DV":
            temp_fuel_price = self.infrastructure.DV_fuel_prices["diesel"][self.tad["year"]]
        
        elif tech =="FCHEV":
            temp_fuel_price = self.infrastructure.FCHEV_fuel_prices[self.tad["Segment"]][self.tad["year"]]

        else:
            temp_fuel_price = self.infrastructure.BEV_fuel_prices[self.tad["Segment"]][self.tad["year"]]   #\
            #+ self.infrastructure.capital[self.tad["Segment"]][self.tad["year"]] * (1 - self.policy.charging_incentive[self.tad["Segment"]][self.tad["year"]])
        
        annual_fuel_cost = self.get_energy_use_by_tech(tech) * temp_fuel_price
        #print('ANUUAL FUEL COST: ',tech,  temp_fuel_price, '    ', tech, annual_fuel_cost, '    ', round(self.get_PV_with_annual(annual_fuel_cost)))
        return round(self.get_PV_with_annual(annual_fuel_cost))
    
    #ver 3 - get present value of annual refueling time cost ($, including refueling time and queue time, penalty on the portion exceeding the budget), verified
    def get_PV_refueling_cost(self, tech):
        if tech == "DV":
            return 0;
        
        if tech =="FCHEV" :
            FCHEV_station_availability = self.infrastructure.FCHEV_station_availability[self.tad["Segment"]][self.tad["year"]]/100   #hour
            FCHEV_station_availability =[FCHEV_station_availability, 1e-10][int(FCHEV_station_availability ==0)]
            FCHEV_refuel_time = 5.20076 * (FCHEV_station_availability) **(-0.584963) / 60 * 3.6 # search per refuel time, hassle factor, which is 3.6
            
            FCHEV_range = self.vehicle.FCHEV_range[self.tad["Segment"]][self.tad["year"]]      #miles
            FCHEV_refuel_annual = self.tad["Annual_mile"] / FCHEV_range * FCHEV_refuel_time   #annual hours
            
            #print("     FCHEV: ",  FCHEV_station_availability, FCHEV_refuel_time)
            #print("            ",  FCHEV_refuel_annual, round(self.get_PV_with_annual(self.tad["time_penalty"] * FCHEV_refuel_annual)))

            return round(self.get_PV_with_annual(self.tad["time_penalty"] * FCHEV_refuel_annual))

        if tech == "BEV":
            
            BEV_charging_power = self.infrastructure.BEV_charging_power[self.tad["Segment"]][self.tad["year"]] #KW
            time_refuel = self.get_energy_use_by_tech(tech) * Agent.kWhperDGE / BEV_charging_power      #annual hours

            BEV_range = self.vehicle.BEV_range[self.tad["Segment"]][self.tad["year"]]      #miles
            BEV_queue_time = self.infrastructure.BEV_queue_time[self.tad["Segment"]][self.tad["year"]]   #hour
            time_queue = self.tad["Annual_mile"] / BEV_range / 0.8 * BEV_queue_time
            time_exceed_budget = time_refuel + time_queue - self.tad["refuel_time_avail"]

            #print(BEV_charging_power,time_refuel,BEV_range,BEV_queue_time,time_queue,time_exceed_budget)
            #print("     BEV: ", time_refuel + time_queue, time_exceed_budget, round(self.get_PV_with_annual(self.tad["time_penalty"] *  (time_refuel + time_queue))))
            
            return 0 if time_exceed_budget <= 0 else round(self.get_PV_with_annual(self.tad["time_penalty"] *  time_exceed_budget))
    
    #total maintainance cost (present value), tech - Diesel, BEV, verfied, verfied
    def get_maintainence_cost(self, tech):
        return round(self.get_PV_with_annual(self.tad["Maintainence_" + tech]))
    
    #ver 3 - get other incentive cost (since it is a benefit, so it is negative cost), verfied
    def get_other_incentive_cost(self, tech):
        if tech == "DV":
            return 0
        elif tech =="FCHEV":
            return 0
        
        elif self.tad["year"] < 2020:
            return - self.tad["Other_incentive_2020"]
        else:
            return - (self.tad["Other_incentive_2020"] + self.tad["Other_incentive_yearly_change"] * (self.tad["year"] - 2020))


    #ver 2- energy use components (unit: DGE), verified
    def get_energy_use_by_tech(self, tech):
        if tech == "DV":
            annual_energy_use = self.tad["Annual_mile"] * self.vehicle.DV_consumption[self.tad["Segment"]][self.tad["year"]] + \
            self.get_energy_use_idling_DV()

        elif tech == "FCHEV":
            annual_energy_use = self.tad["Annual_mile"] * self.vehicle.FCHEV_consumption[self.tad["Segment"]][self.tad["year"]] 

        else:
            annual_energy_use = self.tad["Annual_mile"] * self.vehicle.BEV_consumption[self.tad["Segment"]][self.tad["year"]]
        return annual_energy_use
    
    # average energy use (unit: DGE), verified
    def get_average_energy_use_by_tech(self, tech):
        if tech == "DV":
            annual_energy_use = self.tad["Annual_mile_avg"] * self.vehicle.DV_consumption[self.tad["Segment"]][self.tad["year"]] + \
            self.get_energy_use_idling_DV()
        
        elif tech == "FCHEV":
            annual_energy_use = self.tad["Annual_mile_avg"] * self.vehicle.FCHEV_consumption[self.tad["Segment"]][self.tad["year"]] 

        else:
            annual_energy_use = self.tad["Annual_mile_avg"] * self.vehicle.BEV_consumption[self.tad["Segment"]][self.tad["year"]]
        return annual_energy_use
    
    # annual idling fuel use (DGE), verified
    def get_energy_use_idling_DV(self):
        return self.tad["Idling_hour"] * self.vehicle.DV_idling_consumption[self.tad["Segment"]][self.tad["year"]]

        
    #get present value with annual value ($)
    def get_PV_with_annual(self, value):
        
        discount_rate = self.tad["Discount_rate"]
        year = self.tad["Lifetime"]
        if discount_rate == 0:
            return value * year
        return value * ((1 + discount_rate) ** year - 1) / (discount_rate * (1 + discount_rate) ** year)