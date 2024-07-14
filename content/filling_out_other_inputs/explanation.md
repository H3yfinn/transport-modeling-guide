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














Fuel mixing is meant to handle the use of fuels that can be mixed into others to help reduce the emissions intensity of the original fuel. For example biodiesel can be mixed with diesel to reduce the emissions of the diesel fueled vehicle using that diesel. 

Usually the way an economy might use these alternative fuels wouldn't be by replacing a percentage of all the origianl fuel with the new fuel (like making it so 10% of all diesel is biodiesel), but by replacing a percentage of the fuel used in a specific sector (like 10% of the diesel used in trucks is biodiesel), or even importing a certain quantity and substituting it for a certain quantity of the original fuel. However, this is difficult to model, so we have simplified it to be a percentage of the original fuel that is replaced by the new fuel. If the modeller needs to backcalculate what this ratio might be, then at least that is a relatively simple calculation to make.

The way it is implemented in the model is by the modeller deciding the % of the fuel that will be replaced by the new fuel at whatever dates they specify: 

{{table:01_AUS_Target_dashboard_assumptions.html}}

The model will interpolate between the values specified to create the values you can see in the graph below: 

{{graph:01_AUS_Target_dashboard_assumptions.html}}

Then, after the total demand of the original fuel is calcualted within the model, the model will then reduce the demand by the percentage specified by the modellers fuel mixing series. The model will calculate the demand for the new fuel as the difference between the original demand and the reduced demand. See an example of an economy with/without fuel mixing below:

{{graph:01_AUS_Target_dashboard_assumptions.html}}