# Activity Growth
We estimate activity growth using the macro data that is projected for each economy for our energy outlook. This contains data on GDP and population. Generally the method is to use gdp-per-capita and sometimes popualtion and gdp, and then run a few regressions using that to find the best fit based on what previous activity growth data we have for all economies. This keeps the model parsimonious and allows it to consider the fact that as people get richer they tend to travel more. 

However, being based on past activity trends, the line of best fit based on previous activity growth and projected macro data generally results in a constant positive trend for all but the most negative population and gdp growth rates. This being so, we do a few things to adapt the projection of activity growth to the specific circumstances of each economy:

- In road passenger transport we use vehicle ownership saturation as a way to limit the amount of vehicles that can be owned per capita, which limits the amount that people can travel. See {{link:https://transport-energy-modelling.com/content/vehicle_ownership:text:here}} for more information on vehicle ownership.
- In freight transport we only use the industrial sectors gdp data. This is on the assumption that besides the freight used for personal consumption and general goods, the majority of freight is used for industrial purposes, and significant changes in the industrial sector will have a significant effect on the amount of freight that is transported. So we calculate the freight activity growth based on the industrial sector gdp growth and add on a small amount to account for the general goods and personal consumption. This however is reliant on detailed projections of industrial activty by subsector, which is not always available.
- For passenger transport in non-road we use the gdp-per-capita method described above. However in some cases we use the road pasenger transport growth rate. 

# Economy groupings:
I find it useful to keep in mind the general groups of economies that we have. This helps with trying to work out what activity growth might suit certain economies. I've been using these groups:

{{graph:gdp_per_capita_avg.html}}

{{graph:vehicle_ownership_vs_population_density_vs_gdp_per_capita_avg.html}}

{{graph:vehicle_ownership_vs_population_density_avg.html}}

Of course there's a wide range of growth rates within those groups. You can see how I've also used these in the {{link:https://transport-energy-modelling.com/content/analytical_pieces:text:analytical pieces}} section.
