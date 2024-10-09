# Matching official energy statistics using optimisation

Because we must match what an economy sends us as their energy use statistics, and we calculate energy use using a bottom up approach, we often have to balance out our input data to match the energy data. This is done using an optimisation process.

The equation for energy in road transport is:

    Mileage * (1/Efficiency) * Stock = Energy use

So we have to balance out the mileage, efficiency and stock factors to make their product equal the energy data.

The optimisation process is a simple one and it uses the scipy.optimize library to do so (basically if i wanted to impress you i would say it was 'machine learning'). We take the difference between the energy data and the energy data we calculate using our bottom up approach. We then adjust the factors so their product is equal to the energy use. This is complciated by the amount of different categories we have to match as well as the lack of those categories in the energy data. See {{link:https://transport-energy-modelling.com/content/concordances:text:here}} for the full list of categories we have to match.

We try to minimise the difference between the factors and their old values by setting ranges for each of them based on judgement. For example we try not to let Mileage and Efficiency change by more than 10%, and then let stocks take up the remaining change thats needed. In some cases where the energy data or input data is very wrong, stocks will change by a lot, which can introduce substantial inaccuracies into the model - although it might still be an improvement if the original data was wrong!