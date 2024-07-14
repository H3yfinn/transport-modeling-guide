# Fuel Mixing

Fuel mixing is meant to handle the use of fuels that can be mixed into others to help reduce the emissions intensity of the original fuel. For example biodiesel can be mixed with diesel to reduce the emissions of the diesel fueled vehicle using that diesel. 

Usually the way an economy might use these alternative fuels wouldn't be by replacing a percentage of all the origianl fuel with the new fuel (like making it so 10% of all diesel is biodiesel), but by replacing a percentage of the fuel used in a specific sector (like 10% of the diesel used in trucks is biodiesel), or even importing a certain quantity and substituting it for a certain quantity of the original fuel. However, this is difficult to model, so we have simplified it to be a percentage of the original fuel that is replaced by the new fuel. If the modeller needs to backcalculate what this ratio might be, then at least that is a relatively simple calculation to make.

The way it is implemented in the model is by the modeller deciding the % of the fuel that will be replaced by the new fuel at whatever dates they specify. The model will interpolate between the values specified to create the values you can see in the graph below: 

{{graph:fuel_mixing_Target.html}}

Then, after the total demand of the original fuel is calcualted within the model, the model will then reduce the demand by the percentage specified by the modellers fuel mixing series. The model will calculate the demand for the new fuel as the difference between the original demand and the reduced demand. Generally this will help to decrease emissions but the assumption is that there are no changes in efficiency.