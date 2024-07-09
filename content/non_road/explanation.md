# Explanation for Page 1
Within transport modelling it is very hard to understand exactly how non-road transport such as trains, planes and air transport interact with road transport. This is because the data is not as readily available as it is for road transport. However, it is important to include non-road transport in the model as it can have a significant impact on the emissions of a country.

# Using activity to represent stocks
It is much harder to use stocks since the data is not as readily available and the stocks of rail, ships and planes vary a lot in terms of their efficiency, mileage and load/occupancy. However stocks enable for better representation of the effects of turnover and new vehicles. To make up for this, we use the follwoing process:

- set efficiency of non-road transport to be the same for all activity
- each year simulate X% turnover by simulating the replacement of Y% of the activity with new activity which has a different efficiency. Do this by using the following formula:
    - new efficiency = ((old activity * (1 - TURNOVER_RATE) / total activity) * (efficiency * NEW_VEHCILE_EFFICIENCY_GROWTH_RATE) + (old activity - (old activity * (1 - TURNOVER_RATE)) / total activity) * efficiency) / 2
    - simplified to a weighted mean: new efficiency = (((new_activity/old_activity) * new_efficiency) + ((remaining_old_activity/old_activity) * efficiency)) / 2 activity
    - where TURNOVER_RATE is the proportion of activity that is replaced each year and NEW_VEHCILE_EFFICIENCY_GROWTH_RATE is the growth in efficiency of the new activity compared to the old activity
- any new activity from growth is also added to the total activity and the new avg efficiency is calculated as above.

# Simulating switching between non-road and road transport:
It is expected that some activity will switch between non-road and road transport. Because te road and non-road models aren't connected, we can't simulate this directly. Instead we apply the switching post-hoc to the modelled data. This is done by applying a % change to the mediums that is being switched from, and then putting the numerical value of that change into the medium that is being switched to. This is a very simple way of doing it and is not very accurate, however, without stocks data for non road it seemed like the best alternative.

# Switching between non-road mediums:
We call the different means of non-road transport (rail, boat, plane) mediums. We assume that some activity will switch between these mediums. This is done by determining the % of new non road activity that is allocated to each medium (using the % allocations from year before). The allocations change over time as a result of what is set in the vehicle sales shares.xlsx file. A big issue is that it is only switching between the mediums and not to road transport. As a result of not wanting to switch too mcuh between the non-road mediums, the vehicle sales share.xlsx file is most useful in determining the types of fuels with new activity use.
