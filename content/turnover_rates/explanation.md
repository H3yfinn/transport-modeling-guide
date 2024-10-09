# Turnover rates

Turnover rates are the main factor in defining the difference between sales share and stock share. If turnvoer rates are high, the difference between sales share and stock share will be low. If turnover rates are low, the difference between sales share and stock share will be high.

The way we set turnover rates is based on the age of the vehicle. The older the vehicle, the higher the turnover rate. The younger the vehicle, the lower the turnover rate. Then using something called a survival function, we can calculate the turnover rate for each vehicle. Bascailly, if you look at the S curve below, the turnover rate can be calcaulted as the y value of the curve at a given x value, where x is the age. 

{{graph:turnover_rate_age_curve_Target_01_AUS.html}}

The reasoning for including this as a process is to make sure that the oldest vehicles are turned over first. This is important because if you are trying to increase the amount of EV's, you want to get rid of your older vehicles which are more likely to be ICE's, rather than your newer vehicles which are more likely to be EVs. 

There are additional complexities when considering how to structure the age distribution of vehicles. Initially, I modeled each vehicle/drive type with a single average age—for example, assuming BEV cars had an average age of 1 year and ICE cars had an average age of 10 years. This average age would then change over time, depending on the number of new cars being added, cars being retired, and existing cars aging each year. However, to accurately determine how the average age of vehicles changes with turnover, new purchases, and annual aging, I realized that a more detailed age representation was necessary.

We now use an age distribution of the vehicles, which allows us to see how many vehicles are at each age and how that distribution changes over time. Consequently, after each year, all vehicles in the distribution advance by one age group. When vehicles are retired, the oldest vehicles are removed from the distribution, and new vehicles are added to the youngest age group as needed.

An interesting case is Singapore where the country has very young cars relative to the rest of the world. this is because they have a scheme where you can only ?own a car for 10 years before you have to get rid of it?. To try replicate this dynamic within the model I created a new S curve like below. This can be done just by halving the parameters of the original S curve. 

{{graph:turnover_rate_age_curve_Target_17_SGP.html}}

Of course, we can never know if this is correct, but something needs to be done to represent Singapore's different turnover rates in the model. As with many things in modelling, its the best guess we can make with the information we have. And sometimes what is most important is to be able to show clear dynamics and trends that the viewer (e.g. policy advisor) might expect to see in the real world, and then show how they interact to create the results we see.

There are some assumptions i had to sneak in to simplify things, but i felt it wasn't a big deal:

- we still base the turnover rate off the average age of the vehicles but always the oldest vehicles are turned over first. this doesnt quite match reality as there is a chance that any vehicles regardless of its age will be turned over. But it is a simplification that makes the model easier to understand.
- Non road uses a S curve which allows their 'vehicles' to be turned over later than road vehicles. This is because the non road vehicles are more likely to be used for longer than road vehicles. However if you read the non road section {{link:https://transport-energy-modelling.com/content/non_road:text:here}} you will realise that we have simplified things by not using the histogram idea.

Below are two charts, one of the average age of vehicles by drive type and one of the turnover rate of them:
{{graph:turnover_rate_by_vtype_all_road_Target.html}}
{{graph:average_age_road_Target_01_AUS.html}}