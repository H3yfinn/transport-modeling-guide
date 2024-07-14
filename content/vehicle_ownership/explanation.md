# Vehicle Ownership

Otherwise called stocks per capita and essentially is a measure for passenger vehicles which heavily affected by the amount of road travel that each member of the population does. If this is low (for example in japan where trains are more popular) then the vehicle ownership (number of vehicles needed) is lower. In the USA this is high because it is a country where most people who can travel will use their own private car. 

In our model this is an important metric for guiding the trajectory of activity growth in the passenger transport sector. Without this, activity growth would either be constant and upwards, or much more difficult to model. See the page on {{link:https://transport-energy-modelling.com/content/activity_growth:text:activity growth}} for more information on how this is estimated and used in the model.

The way that vehicle ownership affects activity growth is by putting a limit on the amount of stocks per capita that are allowed in an economy, based on simple threshold values inserted in the input data. Then as vehicle ownership grows towards the threshold, a saturation effect is applied to the activity growth, which slows down the growth of activity. See the graph below for an example of how this works.

{{graph:stocks_per_capita_Target.html}}

We base these threshold values off pretty simplistic assumptions, such as how car oriented a culture is, or how much public transport is used. While we regret that these assumptions may seem unfounded, this is still an improvement on the more simplistic method of estimating activity growth from gdp per capita projections.
