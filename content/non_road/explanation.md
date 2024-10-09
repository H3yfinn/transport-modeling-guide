# Non Road Explanation
Within transport modelling it is very hard to understand exactly how non-road transport such as trains, planes and air transport interact with road transport. This is because the data is not as readily available as it is for road transport. However, it is important to include non-road transport in the model as it can have a significant impact on the emissions of a country.

{{graph:energy_use_by_fuel_type_non_road_Target.html}}

# Using activity to represent stocks
It is much harder to use stocks since the data is not as readily available and the stocks of rail, ships and planes vary a lot in terms of their efficiency, mileage and load/occupancy. However stocks enable for better representation of the effects of turnover and new vehicles. To make up for this, we use the following process:

- set efficiency of non-road transport to be the same for all activity
- each year simulate X% turnover by simulating the replacement of Y% of the activity with new activity which has a different efficiency. Do this by using the following formula:
    - new efficiency = ((old activity * (1 - TURNOVER_RATE) / total activity) * (efficiency * NEW_VEHCILE_EFFICIENCY_GROWTH_RATE) + (old activity - (old activity * (1 - TURNOVER_RATE)) / total activity) * efficiency) / 2
    - simplified to a weighted mean: new efficiency = (((new_activity/old_activity) * new_efficiency) + ((remaining_old_activity/old_activity) * efficiency)) / 2 activity
    - where TURNOVER_RATE is the proportion of activity that is replaced each year and NEW_VEHCILE_EFFICIENCY_GROWTH_RATE is the growth in efficiency of the new activity compared to the old activity
- any new activity from growth is also added to the total activity and the new avg efficiency is calculated as above.

{{graph:non_road_activity_by_drive_all_Target_01_AUS.html}}

# Simulating switching between non-road and road transport:
It is expected that some activity will switch between non-road and road transport. Because the road and non-road models aren't connected, we can't simulate this directly. Instead we apply the switching post-hoc to the modelled data. This is done by applying a % change (decrease) to the medium that is being switched from, and then putting the numerical value of that change into the medium that is being switched to (i.e. shift 50 passenger km of road transport to trains by taking away from one and adding to the other). Then based on these new activity levels, recalculate energy use, and for road, we also recalculate vehicle stocks. This is a very simple way of doing it and is not very accurate (for example it doesnt consider the effect of recalculating the vehicle stocks on the average age of them), however, without stocks data for non road it seemed like the best alternative.

# Switching between non-road mediums:
We call the different means of non-road transport (rail, boat, plane) mediums. We assume that new activity will not always be allocated to each medium equally. Instead the proportion of growth in activity that is allocated to each medium can changes over time (e.g. trains may increase in activity fast while boats and airplanes dont). This is done by determining the % of new non road activity that is allocated to each medium (using the % allocations from year before). The allocations change over time as a result of what is set in the vehicle sales shares.xlsx file. A big issue is that it is only allocated between the non road mediums and not to road transport.

The vehicle sales share.xlsx file is most useful in determining the types of fuels with new activity use, within each medium. This is done just like the {{link:https://transport-energy-modelling.com/content/vehicle_sales_shares:text:vehicle sales shares}} for road, except the Drive type is just a representation of the input fuel type, and we ignore the different kinds of engines. This point is also important for understanding that because of the larger variance in efficiencies within non-road engine types, we just ignore them and instead have a single intensity value for each fuel type, which is seen as an average of all the different engine types that use that fuel.

{{graph:non_road_share_of_transport_type_Target.html}}

# Inaccuracies in the model
Since there's so much variation within the non road sector, in terms of mileage, occupancy, load, efficiency and kinds of vehicles, and there is not much data on any of this at all, we have tried to simplify things a lot. For this reason our intensity values are generally just calculated from the product of the ESTO energy data and manually gathered activity estimates by medium, transport type and sometimes fuel. So sometimes these values will be way off, and we might even have manually adjusted them to make the model work. This is a big issue and we hope to improve this in the future, along with the connection of road and non road transport activity growth allocations.  

See an example of the variation in energy intensity values for non-road transport below:

Japan:
{{graph:energy_intensity_strip_Target_08_JPN.html}} 
Indonesia:
{{graph:energy_intensity_strip_Reference_07_INA.html}}
