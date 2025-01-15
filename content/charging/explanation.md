# Charging
In our modelling we have built a method to estimate the number of publicly funded chargers that are required based on the stocks of vehicles. We have the following parameters:
    
{{table:parameters_combined.csv}}

Generally a good rule of thumb is 1 publicly available slow charger per 10 BEV's. However as you can see there are many factors. It is actually normally better to consider the kwh of the battery and count out the kw of chargers (fast/slow) per kwh of battery. This is because the battery size is a good proxy for the amount of energy that needs to be put into the vehicle. Then there are also the charging patterns of different vehicles, which could be quite different, although as of 2024, its still early days for EV's so we dont have a lot of data on this.

See a projection of chargers below:
    
{{graph:charging_dashboard_05_PRC_Target.html}}

Some other factors affecting the number of chargers required in an economy are:

- The amount of private chargers that are available.
- Urban density and population density.
- The size of vehicles and the size of the batteries.
- The amount of time that vehicles are parked.
- The amount of time that vehicles are parked in public spaces.
- The amount of driving people do.
- You can find more on the IEA website, e.g. [here](https://www.iea.org/reports/global-ev-outlook-2024/trends-in-electric-vehicle-charging).

## My code
The {{link:https://github.com/H3yfinn/transport_model_9th_edition/blob/public_master/model_code/calculation_functions/estimate_charging_requirements.py:text:script in my model}} can be explained using the following:
This code calculates the number of public chargers needed for EVs using three main inputs: EV numbers, average battery capacities by vehicle type, and the expected chargers per kWh of battery capacity. It adjusts for population density and urbanization, which scale the public charging needs (more dense means more public chargers needed). Based on these factors, it calculates the total battery capacity of the EV fleet.

Charger requirements are determined by applying the chargers-per-kWh parameter and adjusting for public charger utilization rates specific to vehicle types. The total charger demand is split into fast and slow chargers using predefined ratios and their respective power capacities. The outputs rely heavily on accurate inputs for EV numbers, battery capacities, and the chargers-per-kWh parameter.
