# Guide to filling out the vehicle sales shares assumptions

{{link:https://transport-energy-modelling.com/content/vehicle_sales_shares:text:Vehicle sales shares}} is a way to reduce the emissions intensity of a fuel by mixing it with another fuel. For example, biodiesel can be mixed with diesel to reduce the emissions of the diesel-fueled vehicle using that diesel.

{{table:vehicle_sales_shares.csv}}
After downloading this workbook in the staging page, to fill in the fuel mixing form, you need to keep in mind the following:

- the sum of fuel mix shares should be 1 or less for each year and Fuel in the table above
- the fuel mix shares should be positive
- the economy, fuel, new_fuel and year columns are mandatory plus they must match the categories already in the sheet if you download it. See the page on {{link:https://transport-energy-modelling.com/content/concordances:text:concordances}} to see what is currently used in the model.

This workbook has many other pages but except for the simple to use regions, international_supply_side and demand_side pages, the others are really just mess that i dont want to clean up for fear of losing some notes.

# The result:
Below you can see a graph of sales and stock shares for the passenger sector. This is a good way to see how the sales of different vehicle types are changing over time, and how this is affecting the stock of vehicles in the economy (with the lag being caused by the {{link:https://transport-energy-modelling.com/content/turnover_rates:text:turnover rates}} of the vehicles).

{{graph:individual_graphs_sales_share_by_transport_type_passenger_Target.html}}

And a more detailed view of the sales and stock shares by vehicle type for non-ice vehicles:
    
{{graph:share_of_vehicle_type_by_transport_type_all_Target.html}}
