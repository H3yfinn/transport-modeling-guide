# Other inputs and how to fill them out

There are many other inputs besides vehicle sales shares and fuel mixing assumptions that you can fill out in the model. I'll try to cover them all here. If you have any questions about any of the inputs, please let me know in the {{link:https://transport-energy-modelling.com/content/feedback_form:text:Feedback Form}}.

These are the vehicle ownership thresholds. Learn about them {{link:https://transport-energy-modelling.com/content/vehicle_ownership:text:here}}.
{{table:Gompertz_gamma.csv}}

The following tables are yearly growth rates for different parameters in the model. Generally they are left constant and as they are, but if there is a policy which might affect on of them, then they can be useful:
{{table:Mileage_growth.csv}}
As an example, if a country wanted to introduce a mandate for 100% HEV sales within ICE's then you can increase the new vehicle efficiency growth for a few years so that by the end of those, the efficiency of new ICE vehicles is the same as the efficiency of new HEV vehicles. 
{{table:New_vehicle_efficiency_growth.csv}}

{{table:Non_road_intensity_improvement.csv}}

{{table:Occupancy_or_load_growth.csv}}
Another example: This can be changed if the country is especailly focused on implementing policies that will improve the routing of vehicles. This is especailly useful for freight vehicles. 
{{table:activity_efficiency_improvement.csv}}

These are the results of regression analysis on past activity and macro data for projecting future activity growth. Learn more about them {{link:https://transport-energy-modelling.com/content/activity_growth:text:here}}.
{{table:growth_coefficients_by_region.csv}}

The Parameters.yml file is missing because it is a very large file. You can download it from the staging page, which comes up when you click 'run model' in the {{link:https://transport-energy-modelling.com/index:text:main page.}}
