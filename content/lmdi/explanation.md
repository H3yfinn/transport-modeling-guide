# Quick intro to reading LMDI charts
The LMDI method is a way of breaking down changes in energy use. It stands for Logarithmic Mean Divisia Index. It is a way of breaking down changes in energy use into different factors. This is useful for understanding what is driving changes in energy use. 

In the chart below the drivers are:

- passenger_and_freight_km: this is the energy use caused by changes in activity of the transport sector. This is usually the main driver of increasing in energy use.
- Vehicle Type: this is the energy use caused by changes in the vehicle type. For example from cars to buses or motorcycles. This is usually associated with a drop in energy use if the economy is trying to increase bus use.
- Engine switching: this is the energy use caused by changing the drive/engine/powertrains of vehicles. For example moving from petrol to electric vehicles. This is usually the main driver of decreasing energy use.
- Vehicle efficiency: this is the remaining changes in energy use, and acts as a residual. In this particular chart it would be catching the effects of improvements to the efficiency of vehicles but not switching to different types (such as improvements to the efficiency of ICE cars, or even BEV cars).

{{graph:10_MAS_road_2_Energy use_Hierarchical_2070_combined.html}}

Some analysis of the chart above:

- You can see how the engine switching effect is more major in the Target scenario than Reference, and this is because of more optimistic assumptions about the uptake of electric vehicles. 
- The vehicle type effect is also quite large in the Target scenario. This is because we had some very optimistic assumptions for the uptake of buses for this particular economy. Normally this effect is quite small. Think of it this way: it is more difficult to replace all cars with buses than all cars with electric cars, as such the effect is usually smaller for vehicle type switching.
- The vehicle efficiency effect is significant in the Reference scenario. This is because with much less engine switching, the efficiency gains on new ICEs (which is assumed to be ~1.5% improvement per year in both scenarios) are more impactful, since there are more new ICE's being sold in the Reference scenario.
-The activity effect is large and almost the same in both scenarios. This is because we assume that both scenarios have the same activity growth and so it there is only a slight difference because of a slight improvement to activity efficiency (improvements to routing so that people need to drive less to achieve the same goals).

## Multiplicative LMDI
You can also break down the changes in energy use using a multiplicative LMDI, which shows the same information but in a different way. It has the advantage of being easier to read in a time series and it shows the changes as the product of the multipliers. 

{{graph:10_MAS_Target_passenger_road_2_Emissions_Hierarchical_2070_multiplicative_timeseries.html}}

## Analysing Emissions drivers using LMDI
The LMDI method can also be used to break down changes in emissions. The drivers are usually the same, with addition of anything that might be affecting emissions intensity independently of the energy use. For example, changes in the carbon intensity of fuels, measured using the **emissions intensity** driver below. This is usually the result of fuel mixing, as described in the {{link:https://transport-energy-modelling.com/content/fuel_mixing:text:fuel mixing}} section.

{{graph:07_INA_Target_freight_road_2_Emissions_Hierarchical_2050_additive_hierarchical.html}}

### NOTE
If you want to use this method, please take a look at my github code and guide {{link:https://github.com/asia-pacific-energy-research-centre/PyLMDI/tree/main:text:here}}. 