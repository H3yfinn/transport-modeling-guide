# Vehicle sales shares

Vehicle sales shares are one of the key tools in the model to determine the trajectory of a projection. This is because of the sheer effect that switching to new drive/powertrain/engine types (hereby referred to as drive types) can have on energy efficiency and emissions. For example a battery electric vehicle (BEV) is ~2.5 times more efficient than a internal combustion engine (ICE) vehicle. See the relative efficiencies in our data in the {{link:https://transport-energy-modelling.com/content/energy_intensity:text:Energy intensity}} page.

Usually the way an economy might try to plan for the uptake of new drive types is by setting targets for the sales of them. This is what the vehicle sales shares are for - we can directly insert these targets into the model and the model will project all of the flow-on effects from that. 

The modeller can set the percentage of new vehicles sold in a year that will be of a certain drive type. For example, a common task is to set a target that 100% of all new cars sold in 2050 will be BEVs. See the table below for an example of how to fill out the vehicle sales shares table:

{{table:vehicle_sales_shares.csv}}

The model will interpolate between the values specified to create the values you can see in the graph below: 

{{graph:share_of_vehicle_type_by_transport_type_all_Target.html}}

Note that above you can also see the stock shares as dotted lines. These are calculated within the stock turnover process which you can read about more in the {{link:https://transport-energy-modelling.com/content/turnover_rates:text:turnover rates}} page.