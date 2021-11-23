import csv
import matplotlib.pyplot as plt
import matplotlib as mlp
import pandas as pd
import numpy as np
import seaborn as sns
import pycountry
from PIL import Image
sns.set_theme(style="darkgrid")
from pycountry_convert import country_alpha2_to_continent_code, country_name_to_country_alpha2, convert_continent_code_to_continent_name

volcanodf = pd.read_csv('volcano.csv')


eruptionsdf = pd.read_csv('eruptions.csv')
eventsdf = pd.read_csv('events.csv')
sulfurdf = pd.read_csv('sulfur.csv')
tree_ringsdf = pd.read_csv('tree_rings.csv')

print(volcanodf.dtypes)

print(volcanodf.shape)

volcanodf = volcanodf[(volcanodf['last_eruption_year'] != 'Unknown')]

volcanodf = volcanodf.astype({"last_eruption_year": int})
sorted_volcano = volcanodf.sort_values(by="last_eruption_year", ascending = True)[["volcano_number", "volcano_name", "country", "last_eruption_year",
                                                                                  "population_within_5_km", "population_within_10_km", "population_within_30_km", "population_within_100_km"]]

cut_labels = ['<-8000', '<-6000', '<-4000', '<-2000', '<0', '>0', '>2000']
cut_bins = [-12000, -8000, -6000, -4000, -2000, 0, 2000, 3000]

#print(sorted_volcano.shape)

#print(eruptionsdf.shape)
eruptionsdf = eruptionsdf[eruptionsdf['start_year'].notnull()][["volcano_number", "eruption_number", "vei", "start_year", "start_month", "end_year", "end_month", "latitude", "longitude"]]
#print(eruptionsdf.shape)
eruptionsdf = eruptionsdf.astype({"start_year": int})
#sorted_eruptions = eruptionsdf.sort_values(by="start_year", ascending = True)
merged_volcano_eruptions = pd.merge(sorted_volcano, eruptionsdf, on='volcano_number', how='inner')
merged_volcano_eruptions['cut_year'] = pd.cut(merged_volcano_eruptions['start_year'], bins=cut_bins, labels=cut_labels)
merged_volcano_eruptions = merged_volcano_eruptions.sort_values(by="start_year", ascending = True)
print(merged_volcano_eruptions.shape)

def get_continent(col):
    try:
        cn_a2_code =  country_name_to_country_alpha2(col)
    except:
        cn_a2_code = 'Unknown'
    try:
        cn_continent = country_alpha2_to_continent_code(cn_a2_code)
    except:
        cn_continent = 'Unknown'
    try:
        cn_continent_name = convert_continent_code_to_continent_name(cn_continent)
    except:
        cn_continent_name = 'Unknown'
    return cn_continent_name

merged_volcano_eruptions["continent"] =  merged_volcano_eruptions.country.apply(get_continent)
#print(merged_volcano_eruptions.head(20))

#dunyadaki volkanların genel görüntüsü
import plotly.express as px

px.set_mapbox_access_token("pk.eyJ1IjoiaGF6YWx1c3RhIiwiYSI6ImNram9jeng2bDZ2aGoyeWxnYWVlZm5pcXgifQ.Ygj0JgnLagkVCVfHqKrxUQ")

fig = px.scatter_mapbox(merged_volcano_eruptions,
                        lat=merged_volcano_eruptions.latitude,
                        lon=merged_volcano_eruptions.longitude,
                        hover_data=["volcano_name", "start_year"],
                        animation_frame="cut_year",
                        animation_group= "eruption_number",
                        color="continent",
                        color_discrete_sequence=px.colors.qualitative.Set1,
                        title="Dünyadaki Volkan Patlamaları",
                        zoom=1)
fig.layout.updatemenus[0].buttons[0].args[1]["frame"]["duration"] = 1500
fig.show()

grouped_df = merged_volcano_eruptions.groupby(['continent', 'cut_year']).size().reset_index(name='count')


fig = px.bar(grouped_df, x="continent",y="count", color="continent", animation_frame="cut_year", range_y=[0,"2600"], title="Kıta Bazında Volkan Patlama Sayıları Toplamı")
fig.show()

count = merged_volcano_eruptions["vei"].isna().sum()
print(count)
print(merged_volcano_eruptions.shape)
filtered_merged = merged_volcano_eruptions[merged_volcano_eruptions['vei'].notnull()]
print(filtered_merged.shape)
after_0 = filtered_merged['start_year'] > 0
filtered_merged = filtered_merged[after_0]
filtered_merged["vei"] = filtered_merged["vei"] + 1
print(filtered_merged.shape)
filtered_merged.head()

fig = px.density_mapbox(filtered_merged, lat=filtered_merged.latitude, lon=filtered_merged.longitude, z='vei', radius=10,
                        center=dict(lat=0, lon=180), zoom=1, hover_data = ["volcano_name", "start_year"],
                        mapbox_style="stamen-terrain", title="Volkanların VEI Numaralarına göre Yoğunluğu")
fig.show()

import pycountry
def get_countryCode(col):
    try:
        cn_a2_code =  pycountry.countries.get(name=col).alpha_3
    except:
        cn_a2_code = 'NA'

    return cn_a2_code

grouped_eruptions = merged_volcano_eruptions.groupby(["country"]).size().reset_index(name='count')
grouped_eruptions["iso_country_code"] = grouped_eruptions.country.apply(get_countryCode)
grouped_eruptions = grouped_eruptions[grouped_eruptions['iso_country_code']  != 'NA']
#grouped_eruptions

import plotly.graph_objects as go
from plotly.graph_objs import *
fig = px.choropleth(grouped_eruptions, locations="iso_country_code",
                    color=np.log2(grouped_eruptions['count']), # lifeExp is a column of gapminder
                    hover_data = ["country", "count"],
                    labels={'count':'Number of eruptions'},
                    color_continuous_scale="Hot_r",
                   )
fig.update_layout(title_text='Ülke Bazında Yanardağ Patlama Sayıları Toplamı',
    geo = dict(
        showocean=True, # lakes
        oceancolor='rgb(127,205,255)'),
)

#fig.layout.coloraxis.colorbar.tickvals = [10,20,30,40,100]

fig.show()

import plotly.figure_factory as ff

japan = filtered_merged['country'] == "Japan"
asia = filtered_merged['continent'] == "Asia"

fig = ff.create_hexbin_mapbox(
    data_frame=filtered_merged[japan], lat="latitude", lon="longitude",
    nx_hexagon=10, opacity=0.7, labels={"count": "Point Count"}, color_continuous_scale="Inferno_r",
     min_count=1, title="Japonyadaki Yanardağlar ve Patlama Sayıları",
    show_original_data=True,
    original_data_marker=dict(size=4, opacity=0.6, color="Blue")
)
fig.layout.coloraxis.colorbar.title = '#Eruptions in Japan'
fig.update_layout(margin=dict(b=0, t=0, l=0, r=0))
fig.show()

import plotly.graph_objects as go
import math

colors = ['rgb(189,215,231)', 'rgb(107,174,214)', 'rgb(33,113,181)']
pops = {6: '5km', 7: '10km', 8: '30km'}

fig = go.Figure()

for i in range(6, 9)[::-1]:

    if i == 6:
        df_veis = filtered_merged.query('vei >= 3 and population_within_5_km != 0')
        df_pop = df_veis["population_within_5_km"]
    elif i == 7:
        df_veis = filtered_merged.query('vei >= 4 and population_within_10_km != 0')
        df_pop = df_veis["population_within_10_km"]
    else:
        df_veis = filtered_merged.query('vei >= 7 and population_within_30_km != 0')
        df_pop = df_veis["population_within_30_km"]

    fig.add_trace(go.Scattergeo(
        lon=df_veis['longitude'],
        lat=df_veis['latitude'],
        text=df_pop,
        name=pops[i],
        marker=dict(
            size=np.log10(df_pop),
            color=colors[i - 6],
            line_width=0
        )))

df_sept = filtered_merged.query('vei >= 3')
fig['data'][0].update(mode='markers+text', textposition='bottom center',
                      text=df_sept['population_within_5_km'].map('{:.0f}'.format).astype(str) + ' ' + \
                           df_sept['volcano_name'])
