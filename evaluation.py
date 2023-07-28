'''
Evaluating all truck samples, and for each sample, calculate TCO by tech and energy use by tech

'''
import copy
from agent import Agent
from infrastructure import Infrastructure
from vehicle import Vehicle
from policy import Policy
import pandas as pd
import numpy as np
import os
from math import exp
import matplotlib.pyplot as plt

#pd.set_option('max_columns', None)
pd.options.display.max_columns = None

dirname = os.path.dirname(__file__)

class Evaluation:
    
    kWhperDGE = 37.95      #kWh per diesel gallon equivalent
    
    
    def __init__(self, start_year, end_year, df, scenario, method):
        
        print("    Initialzing...")
        self.start_year = start_year      #year of start of sale
        self.end_year = end_year          # year of end of sale
        self.all_years = list(range(2005, 2065))      #all years for results
        self.segments = list(df["Segment"].unique())   #segments: e.g., Day_cab, Sleeper, Bus
        self.scenario = scenario
        self.method = method

        self.infrastructure = Infrastructure(scenario)
        self.vehicle = Vehicle(scenario)
        self.policy = Policy(scenario)
        
        #for storing results
        self.BEV_sales = {key1 : {key2 : 0 for key2 in self.all_years} for key1 in self.segments} #done
        self.BEV_stocks = {key1 : {key2 : 0 for key2 in self.all_years} for key1 in self.segments} #done
        self.DV_sales = {key1 : {key2 : 0 for key2 in self.all_years} for key1 in self.segments} #done
        self.DV_stocks = {key1 : {key2 : 0 for key2 in self.all_years} for key1 in self.segments} #done
        self.FCHEV_sales = {key1 : {key2 : 0 for key2 in self.all_years} for key1 in self.segments} #done
        self.FCHEV_stocks = {key1 : {key2 : 0 for key2 in self.all_years} for key1 in self.segments} #done
        
        self.BEV_VMT = {key1 : {key2 : 0 for key2 in self.all_years} for key1 in self.segments} #done miles
        self.DV_VMT = {key1 : {key2 : 0 for key2 in self.all_years} for key1 in self.segments} #done miles
        self.FCHEV_VMT = {key1 : {key2 : 0 for key2 in self.all_years} for key1 in self.segments} #done miles

        self.BEV_incentive = {key1 : {key2 : 0 for key2 in self.all_years} for key1 in self.segments} #done $
        self.infrastructure_incentive = {key1 : {key2 : 0 for key2 in self.all_years} for key1 in self.segments} #$
        
        self.diesel = {key1 : {key2 : 0 for key2 in self.all_years} for key1 in self.segments}    #DGE
        self.electricity = {key1 : {key2 : 0 for key2 in self.all_years} for key1 in self.segments} #done #kwh
        self.hydrogen = {key1 : {key2 : 0 for key2 in self.all_years} for key1 in self.segments} 

        self.carbon_emissions = {key1 : {key2 : 0 for key2 in self.all_years} for key1 in self.segments} #done #kgs
        
        self.truck_agent_object_list = []
        temp_list = df.to_dict('records')
        
        
        print("    Creating truck agents...")
        for t in range(self.start_year, self.end_year + 1):
            #print(t)
            for i in range(0, len(temp_list)):
                agent = Agent(temp_list[i], t, self.infrastructure, self.vehicle, self.policy)
                self.truck_agent_object_list.append(agent)

        

    def calculate(self):
        print ("    Calculating evolutions of sales, stock, energy use, etc. ")
        for i in range(0, len(self.truck_agent_object_list)):
            
            if i % 999 == 0:
                print("        processing agent: " + str(self.truck_agent_object_list[i].tad["Segment"]) + " " + 
                      str(self.truck_agent_object_list[i].tad["ID"]) + " in year " + 
                      str(self.truck_agent_object_list[i].tad["year"]))
            
            self.truck_agent_object_list[i].calculate()
            model_year = self.truck_agent_object_list[i].tad["year"]
            lifetime = self.truck_agent_object_list[i].tad["Lifetime"]
            segment = self.truck_agent_object_list[i].tad["Segment"]
            sale = self.truck_agent_object_list[i].tad["Sale"]
            annual_mile_avg = self.truck_agent_object_list[i].tad["Annual_mile_avg"]

            BEV_utility = self.truck_agent_object_list[i].tad["TCO"]["BEV"]
            DV_utility = self.truck_agent_object_list[i].tad["TCO"]["DV"]
            FCHEV_utility = self.truck_agent_object_list[i].tad["TCO"]["FCHEV"]
            #print("*****", BEV_utility, DV_utility, FCHEV_utility)
            
            ############### Update Sales and others based on Logit Model #################
            '''
            Calibration: https://www.iea.org/reports/global-ev-outlook-2023/trends-in-electric-heavy-duty-vehicles
            2022 electric bus 4%, electric truck 1%

            low progress: div = 50000, rate_daycab = 0.2,rate_sleeper = 0.1, rate_bus = 0.2
            high_process: div = 35000, rate_daycab = 0.3,rate_sleeper = 0.1, rate_bus = 0.4
            '''
            rate_daycab = 0.3 # rate for day_cab and sleeper, parameter to be tuned
            rate_sleeper = 0.1
            rate_bus = 0.4 # rate for bus

            if segment == "Bus":
                BEV_utility = BEV_utility * (1+rate_bus)
            elif segment == "Day_cab":
                BEV_utility = BEV_utility * (1+rate_daycab)
            else:
                BEV_utility = BEV_utility * (1+rate_sleeper)

            if self.method == "logit":
                div = 35000
                exp_U_BEV = np.exp(-BEV_utility/div) if np.exp(-BEV_utility/div) !=np.inf else 0
                exp_U_DV = np.exp(-DV_utility/div) if np.exp(-DV_utility/div) !=np.inf else 0
                exp_U_FCHEV = np.exp(-FCHEV_utility/div) if np.exp(-FCHEV_utility/div) !=np.inf else 0
                #print(exp_U_BEV,exp_U_DV,exp_U_FCHEV)

                if exp_U_BEV + exp_U_DV + exp_U_FCHEV == 0:
                    p_BEV = int((BEV_utility<= DV_utility) and (BEV_utility <= FCHEV_utility))
                    p_DV = int((DV_utility<= BEV_utility) and (DV_utility<=FCHEV_utility))
                    p_FCHEV = int((FCHEV_utility<= BEV_utility) and (FCHEV_utility<=DV_utility))
                else:
                    p_BEV = exp_U_BEV / (exp_U_BEV + exp_U_DV + exp_U_FCHEV)
                    p_DV = exp_U_DV/ (exp_U_BEV + exp_U_DV + exp_U_FCHEV)
                    p_FCHEV =exp_U_FCHEV / (exp_U_BEV + exp_U_DV + exp_U_FCHEV)
                #print(p_BEV, p_DV, p_FCHEV)

                self.BEV_sales[segment][model_year] += sale * p_BEV
                self.BEV_incentive[segment][model_year] += sale * p_BEV * self.truck_agent_object_list[i].tad["BEV_incentive"]
                for t in range(0, lifetime):
                    self.BEV_stocks[segment][model_year + t] += sale * p_BEV
                    self.BEV_VMT[segment][model_year + t] += sale * annual_mile_avg * p_BEV
                    self.electricity[segment][model_year + t] += sale * self.truck_agent_object_list[i].tad["annual_average_energy"]["BEV"] * Evaluation.kWhperDGE * p_BEV

                self.DV_sales[segment][model_year] += sale * p_DV
                for t in range(0, lifetime):
                    self.DV_stocks[segment][model_year + t] += sale  * p_DV
                    self.DV_VMT[segment][model_year + t] += sale * annual_mile_avg * p_DV
                    self.diesel[segment][model_year + t] += sale * self.truck_agent_object_list[i].tad["annual_average_energy"]["DV"] * p_DV       

                self.FCHEV_sales[segment][model_year] += sale * p_FCHEV
                for t in range(0, lifetime):
                    self.FCHEV_stocks[segment][model_year + t] += sale * p_FCHEV
                    self.FCHEV_VMT[segment][model_year + t] += sale * annual_mile_avg * p_FCHEV
                    self.hydrogen[segment][model_year + t] += sale * self.truck_agent_object_list[i].tad["annual_average_energy"]["FCHEV"] * p_FCHEV

            ############### Update Sales and others based on Utility ###################### 
            elif self.method =='utility':
            

                #if_BEV = (self.truck_agent_object_list[i].tad["TCO"]["BEV"] <= self.truck_agent_object_list[i].tad["TCO"]["DV"])
                if_BEV = (BEV_utility<= DV_utility) and (BEV_utility <= FCHEV_utility)
                if_DV = (DV_utility<= BEV_utility) and (DV_utility<=FCHEV_utility)
                #print(if_BEV,if_DV,BEV_utility,DV_utility,FCHEV_utility)

                if if_BEV:
                    self.BEV_sales[segment][model_year] += sale
                    self.BEV_incentive[segment][model_year] += sale * self.truck_agent_object_list[i].tad["BEV_incentive"]
                    for t in range(0, lifetime):
                        self.BEV_stocks[segment][model_year + t] += sale 
                        self.BEV_VMT[segment][model_year + t] += sale * annual_mile_avg
                        self.electricity[segment][model_year + t] += sale * self.truck_agent_object_list[i].tad["annual_average_energy"]["BEV"] * Evaluation.kWhperDGE
                
                elif if_DV:
                
                    self.DV_sales[segment][model_year] += sale
                    for t in range(0, lifetime):
                        self.DV_stocks[segment][model_year + t] += sale
                        self.DV_VMT[segment][model_year + t] += sale * annual_mile_avg
                        self.diesel[segment][model_year + t] += sale * self.truck_agent_object_list[i].tad["annual_average_energy"]["DV"]

                else:
                    self.FCHEV_sales[segment][model_year] += sale
                    for t in range(0, lifetime):
                        self.FCHEV_stocks[segment][model_year + t] += sale
                        self.FCHEV_VMT[segment][model_year + t] += sale * annual_mile_avg
                        self.hydrogen[segment][model_year + t] += sale * self.truck_agent_object_list[i].tad["annual_average_energy"]["FCHEV"]
            
            elif self.method =='logit_other_cost': # 
                alpha = 0.5
                '''
                BEV_utility_new = alpha**(BEV_utility + other_costs) # other costs for BEV only, positive or negative
                '''
                BEV_cost_other = 10000 # parameter to be tuned
                BEV_utility = BEV_utility + BEV_cost_other

                exp_U_BEV = alpha**(np.exp(-BEV_utility/div) if np.exp(-BEV_utility/div) !=np.inf else 0)
                exp_U_DV = alpha**(np.exp(-DV_utility/div) if np.exp(-DV_utility/div) !=np.inf else 0)
                exp_U_FCHEV = alpha**(np.exp(-FCHEV_utility/div) if np.exp(-FCHEV_utility/div) !=np.inf else 0)
                #print(exp_U_BEV,exp_U_DV,exp_U_FCHEV)

                if exp_U_BEV + exp_U_DV + exp_U_FCHEV == 0:
                    p_BEV = int((BEV_utility<= DV_utility) and (BEV_utility <= FCHEV_utility))
                    p_DV = int((DV_utility<= BEV_utility) and (DV_utility<=FCHEV_utility))
                    p_FCHEV = int((FCHEV_utility<= BEV_utility) and (FCHEV_utility<=DV_utility))
                else:
                    p_BEV = exp_U_BEV / (exp_U_BEV + exp_U_DV + exp_U_FCHEV)
                    p_DV = exp_U_DV/ (exp_U_BEV + exp_U_DV + exp_U_FCHEV)
                    p_FCHEV =exp_U_FCHEV / (exp_U_BEV + exp_U_DV + exp_U_FCHEV)
                #print(p_BEV, p_DV, p_FCHEV)

                self.BEV_sales[segment][model_year] += sale * p_BEV
                self.BEV_incentive[segment][model_year] += sale * p_BEV * self.truck_agent_object_list[i].tad["BEV_incentive"]
                for t in range(0, lifetime):
                    self.BEV_stocks[segment][model_year + t] += sale * p_BEV
                    self.BEV_VMT[segment][model_year + t] += sale * annual_mile_avg * p_BEV
                    self.electricity[segment][model_year + t] += sale * self.truck_agent_object_list[i].tad["annual_average_energy"]["BEV"] * Evaluation.kWhperDGE * p_BEV

                self.DV_sales[segment][model_year] += sale * p_DV
                for t in range(0, lifetime):
                    self.DV_stocks[segment][model_year + t] += sale  * p_DV
                    self.DV_VMT[segment][model_year + t] += sale * annual_mile_avg * p_DV
                    self.diesel[segment][model_year + t] += sale * self.truck_agent_object_list[i].tad["annual_average_energy"]["DV"] * p_DV       

                self.FCHEV_sales[segment][model_year] += sale * p_FCHEV
                for t in range(0, lifetime):
                    self.FCHEV_stocks[segment][model_year + t] += sale * p_FCHEV
                    self.FCHEV_VMT[segment][model_year + t] += sale * annual_mile_avg * p_FCHEV
                    self.hydrogen[segment][model_year + t] += sale * self.truck_agent_object_list[i].tad["annual_average_energy"]["FCHEV"] * p_FCHEV


                ##########################################################################################
        
        print("    calculating infrastructure incentive")
        for s in self.segments:        
            for t in range(self.start_year, self.end_year + 1):
                self.infrastructure_incentive[s][t] = self.electricity[s][t] / Evaluation.kWhperDGE * self.infrastructure.capital[s][t] * self.policy.charging_incentive[s][t]
        print("    calculating GHG emissions")
        for s in self.segments:
            for t in range(self.start_year, self.end_year + 1):
                self.carbon_emissions[s][t] = self.electricity[s][t] * self.infrastructure.carbon_intensity["electricity"][t] + \
                self.diesel[s][t] * self.infrastructure.carbon_intensity["diesel"][t]
                
    def print_agent_results(self):
        temp_df_list = []
        for i in range(0, len(self.truck_agent_object_list)):
            temp_df_list.append(self.truck_agent_object_list[i].tad)
        temp_df = pd.DataFrame.from_dict(temp_df_list)[list (temp_df_list[0].keys())] 
        temp_df.to_csv(dirname + "/agent/"+ self.scenario + '_' + self.method + "_agent.csv", header = True, index = None)
            
        
    def generate_results(self):
        self.print_agent_results()
        ans_list = []
        for s in self.segments:
            for t in range(2020, self.end_year + 1):
                record = {"Segment" : s,
                          "Year" : t,
                          "BEV_sales" : self.BEV_sales[s][t],
                          "DV_sales" : self.DV_sales[s][t],
                          "FCHEV_sales" : self.FCHEV_sales[s][t],
                          "BEV_stock" : self.BEV_stocks[s][t],
                          "DV_stock" : self.DV_stocks[s][t],
                          "FCHEV_stock" : self.FCHEV_stocks[s][t],
                          "BEV_VMT" : self.BEV_VMT[s][t],
                          "DV_VMT" : self.DV_VMT[s][t],
                          "diesel" : self.diesel[s][t],
                          "electricity" : self.electricity[s][t],
                          "hydrogen" : self.hydrogen[s][t],
                          "BEV_incentive" : self.BEV_incentive[s][t],
                          "infrastructure_incentive" : self.infrastructure_incentive[s][t],
                          "carbon_emissions" : self.carbon_emissions[s][t]
                        }
                ans_list.append(record)
        ans_df = pd.DataFrame.from_dict(ans_list)[list (ans_list[0].keys())] 
        ans_df.to_csv(dirname + "/results/" + self.scenario + '_'+self.method + "_results.csv", header = True, index = None)
    
    

def plot_result(file, save = True, savename_suffix = ''):    
    '''
    # file: csv format file, with csv as suffix
    # show: whether to show plot in the notebook (either show all 3 or none of the three)
    # save: wether to save the plot(either save all 3 or none of the three)
    # savename_suffix: add suffix to each plot, so every round of plotting won't overwrite others
    '''
    
    data = pd.read_csv(file)
    Bus = data.loc[data["Segment"] == 'Bus',['Year','BEV_sales','DV_sales','FCHEV_sales']].reset_index(drop = True)
    Bus.columns = ['Year','BEV', 'DV', 'FCHEV']
    Sleeper = data.loc[data["Segment"] == 'Sleeper',['Year','BEV_sales','DV_sales','FCHEV_sales']].reset_index(drop = True)
    Sleeper.columns = ['Year','BEV', 'DV', 'FCHEV']
    Day_cab = data.loc[data["Segment"] == 'Day_cab',['Year','BEV_sales','DV_sales','FCHEV_sales']].reset_index(drop = True)
    Day_cab.columns = ['Year','BEV', 'DV', 'FCHEV']
    Bus['sum'] = Bus.iloc[:,1:].sum(axis=1)

    Bus.iloc[:, 1:-1] = Bus.iloc[:, 1:-1].div(Bus['sum'], axis=0)

    Sleeper['sum'] = Sleeper.iloc[:,1:].sum(axis=1)

    Sleeper.iloc[:, 1:-1] = Sleeper.iloc[:, 1:-1].div(Sleeper['sum'], axis=0)

    Day_cab['sum'] = Day_cab.iloc[:,1:].sum(axis=1)

    Day_cab.iloc[:, 1:-1] = Day_cab.iloc[:, 1:-1].div(Day_cab['sum'], axis=0)

    fontsize = 18

    fig = plt.figure(figsize=(10,6))
    plt.rcParams.update({'font.size': fontsize})
    plt.gca().set_yticks(plt.gca().get_yticks().tolist())
    plt.gca().set_yticklabels([f'{x:.0%}' for x in plt.gca().get_yticks()])
    plt.stackplot(Bus['Year'],Bus['BEV'],Bus['DV'],Bus['FCHEV'], labels=[ 'BEV', 'DV', 'FCHEV'])
    plt.legend(loc='lower right')
    plt.ylabel('Percentage', fontsize = fontsize)
    plt.xlabel('Year', fontsize = fontsize)
    title = 'Bus + Market Share' + savename_suffix
    plt.title(title, fontsize = fontsize)

    if save == True:
        plt.savefig(dirname + "/results/" + title + '.png')
    
    
    fig = plt.figure(figsize=(10,6))
    plt.gca().set_yticks(plt.gca().get_yticks().tolist())
    plt.gca().set_yticklabels([f'{x:.0%}' for x in plt.gca().get_yticks()])
    plt.rcParams.update({'font.size': fontsize})
    plt.stackplot(Sleeper['Year'],Sleeper['BEV'],Sleeper['DV'],Sleeper['FCHEV'], labels=[ 'BEV', 'DV', 'FCHEV'])
    plt.legend(loc='lower right')
    plt.ylabel('Percentage', fontsize = fontsize)
    plt.xlabel('Year', fontsize = fontsize)
    title = 'Sleeper + Market Share' + savename_suffix
    plt.title(title, fontsize = fontsize)

    if save == True:
        plt.savefig(dirname + "/results/" +title + '.png')

    fig = plt.figure(figsize=(10,6))
    plt.gca().set_yticks(plt.gca().get_yticks().tolist())
    plt.gca().set_yticklabels([f'{x:.0%}' for x in plt.gca().get_yticks()])
    plt.rcParams.update({'font.size': fontsize})
    plt.stackplot(Day_cab['Year'],Day_cab['BEV'],Day_cab['DV'],Day_cab['FCHEV'], labels=[ 'BEV', 'DV', 'FCHEV'])
    plt.legend(loc='lower right')
    plt.ylabel('Percentage', fontsize = fontsize)
    plt.xlabel('Year', fontsize = fontsize)
    title = 'Day Cab + Market Share' + savename_suffix
    plt.title(title, fontsize = fontsize)

    if save == True:
        plt.savefig(dirname + "/results/" + title + '.png')
        
