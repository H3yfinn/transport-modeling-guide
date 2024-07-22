# Reading the results
The charts are built to be interacted with and provide more detail the more you look at them. However, they are also intimidating to look at for the first time. This page will help you understand what you are looking at and how to interpret the results.

## Using the charts:
Below is the results dashboard which contains the main results of the model and incidentally, some of the assumptions. 

- Notice how you can click on categories in the legend, and also double click to isolate a category. You can also click and drag to zoom in on a section of the chart, and click and drag the axis' to change the scale. 
- You can also hover over the chart to see the values of the data points. If you are confused about any of the information or cateogories you can read about them in the  {{link:https://transport-energy-modelling.com/content/glossary:text:glossary}} or the {{link:https://transport-energy-modelling.com:text:methodology}}.

{{graph:05_PRC_Target_dashboard_results.html}}

This dashboard is for the Target scenario which is more optimistic.

## What should I focus on?
The most important things to look at are the total energy use and emissions. However, information on stocks and activity is also important for understanding the speed of the transition, especially when viewing the sales/stock shares and how that translates into energy use, given the changes in activity.

{{graph:05_PRC_Reference_dashboard_results.html}}

This dashboard is for the Reference scenario which is similar to a business as usual scenario.

You can also see the historical data in the chart below. This is in the results dashboard and is useful for understanding the trends in the data and how the model is projecting the future compared to that. 

{{graph:compare_energy_all_8th_Target_05_PRC.html}}

## What ARE the assumptions?
Please note that I am intending to change the name of the dashboards from assumptions to something like 'secondary results'.
At the end of the day the majority of these charts don't actually show the assumptions but instead, very specifc results which directly communicate the assumptions. For example the {{link:https://transport-energy-modelling.com/content/vehicle_sales_shares:text:vehicle sales shares}} charts on both the results and assumptions dashboards take in a few assumptions for sale shares at different points in time, intepolate them and then run them through the model to calculate stock shares (dotted line). However the interpolation step and then calculation of stock shares (which involves assumptions about turnover rates, vehicle age, activity growth and so on) processes the sales share assumptions so much that these graphs have become detail heavy results in and of themselves.

You can also see my 'extra assumptions' dashboard below, which is something I personally use to check everything in the model is working as expected:
    
{{graph:20_USA_Target_dashboard_assumptions_extra.html}}
