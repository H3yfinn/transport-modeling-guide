# Explanation for Page 1

Turnover rates are the main factor in defining the difference between sales share and stock share. If turnvoer rates are high, the difference between sales share and stock share will be low. If turnover rates are low, the difference between sales share and stock share will be high.

The way we set turnover rates is based on the age of the vehicle. The older the vehicle, the higher the turnover rate. The younger the vehicle, the lower the turnover rate. Then using something called a survival function, we can calculate the turnover rate for each vehicle. Bascailly, if you look at the S curve below, the turnover rate can be calcaulte as the y value of the curve at a given x value, where x is the age. 

# include the S curve image here

The reasoning for this complicated process is to make sure that the oldest vehicles are turned over first. This is important because if you are trying to increase the amount of EV's, you want to get rid of your older vehicles which are more likely to be ICE's, rather than your newer vehicles which are more likely to be EVs. 

Then there are extra complications when you start thinking about how you want to be structuring the ages of your vehicles. At first i started modelling by having an average age per vehicle/drive type. e.g. average age of bev cars was 1 and ice cars was 10. But then to properly determine how the vehicles average age changed when you turned them over, bought new ones and grew older each year, I realised we needed a more detailed representation of the ages. The method we use now is a histogram of the ages of the vehicles. This way we can see how many vehicles are at each age and how that changes over time. Therefore when vehicle become older, all vehicles in the histogram move one age group to the right. When vehicles are turned over, the oldest vehicles are removed from the histogram and new vehicles are added to the youngest age group.

There are some assumptions i had to sneak in to simplify things, but i felt it wasn't a big deal:
- we still base the turnover rate off the average age of the vehicles but always the oldest vehicles are turned over first. this doesnt quite match reality but it is a simplification that makes the model easier to understand.