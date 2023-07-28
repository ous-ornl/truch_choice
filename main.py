from truck_segment_generator import Truck_Segment_Generator
from evaluation import *
import pandas as pd
pd.set_option('display.max_rows', None)


def truckChoice(seed, scenario, method):
    print("Generating truck segments using Monte Carlo Simulation...")
    
    generator = Truck_Segment_Generator(seed, scenario)
    monte_carlo_segments = generator.generate_samples_for_all_segments(scenario+str(seed)+'_samples.csv')
    
    print("Creating truck choice model...")
    truck_choice_model = Evaluation(2021, 2050, monte_carlo_segments, scenario, method)

    print("Simulation begins...")
    truck_choice_model.calculate()

    print("saving results.")
    truck_choice_model.generate_results()

    print("saving agent results.")
    truck_choice_model.print_agent_results()

    print("Results visualization.")
    plot_result("results/" + scenario + '_'+method + "_results.csv", save = True, savename_suffix = ' - '+scenario+' - '+method)


def main():
    scenarios = ["high_progress"]
    method = 'logit'# 'logit', 'utility'

    for scenario in scenarios:
        truckChoice(5, scenario, method)

main()

