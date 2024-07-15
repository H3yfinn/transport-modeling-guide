# Charging
In our modelling we have built a method to estimate the number of chargers that are required based on the stocks of vehicles. We have the following parameters:
    
{{table:parameters_combined.csv}}

Generally a good rule of thumb is 1 slow charger per 10 BEV's. However as you can see there are many factors. It is actually normally better to consider the kwh of the battery and count out the kw of chargers (fast/slow) per kwh of battery. This is because the battery size is a good proxy for the amount of energy that needs to be put into the vehicle. Then there are also the charging patterns of different vehicles, which could be quite different, although as of 2024, its still early days for EV's so we dont have a lot of data on this.

See a projection of chargers below:
    
{{graph:charging_Target.html}}
