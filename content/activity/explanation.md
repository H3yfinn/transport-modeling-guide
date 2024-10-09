# Activity
Activity can be split into two units, passenger-km and freight-tonne-km. See the equations below (where occupancy is the amount of passengers in a vehicle and load is the weight of the freight in a vehicle):

- Passenger-km = Occupancy * Distance travelled
- Freight-tonne-km = Load * Distance travelled

These are key indicators for the transport sector, given that the 2 major factors in determining any economic sector's energy use is the activity, and the energy intensity of that activity.

The main factors that affect activity within the transport model are:

- Distance travelled (for all cars in the economy) = Mileage * Stocks
    - Stocks: the number of vehicles in the fleet
    - Mileage: the distance travelled by each vehicle
- Occupancy: the number of passengers in each vehicle
- Load: the weight of the freight in each vehicle

And for passenger transport we also have:

- Vehicle ownership: otherwise called stocks per capita and essentially is a measure for passenger vehicles which is heavily affected by the amount of road travel that each member of the population does. If this is low (for example in japan where trains are more popular) then the vehicle ownership (number of vehicles needed) is lower. In the USA this is high. See {{link:https://transport-energy-modelling.com/content/vehicle_ownership:text:here}} for more information on vehicle ownership.

There is also Activity Growth, for which you can read about {{link:https://transport-energy-modelling.com/content/activity_growth:text:here}}.

And below you can see a chart of passenger activity:
{{graph:passenger_km_by_drive_Target.html}}
Notice how there is a bump up in the first two years. This is because of the way we model the effects of COVID. You can read more about that {{link:https://transport-energy-modelling.com/content/covid:text:here}}.

And for freight activity:
{{graph:freight_tonne_km_by_drive_Target.html}}

These charts are also useful for understanding how the transition to new technologies is going. This is because activity is the best way of understanding how much a vehicle is being used and therefore how much that new technology is being used. However it doesn't take into account the energy intensity of the activity (basically the efficiency of the vehicle being used). This is why, at the end of the day, the best way to understand the effect of a new technology is to look at a breakdown of energy use (e.g. broken down by factor) which will take into account the activity and the intensity. See this page on {{link:https://transport-energy-modelling.com/content/lmdi:text:lmdi methods for breaking down changes in energy use}} for more information.
