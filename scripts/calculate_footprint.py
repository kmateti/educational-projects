import numpy as np
import yaml
import plotly.graph_objects as go

# Function to convert a list/tuple like [r, g, b] into an "rgb(r, g, b)" string
def color_to_plotly(color):
    return f"rgb({color[0]}, {color[1]}, {color[2]})"

load_config_path = "src/piano/config.yaml"

# Load sector configurations from YAML
with open(load_config_path, 'r') as file:
    config = yaml.safe_load(file)
sectors_list = config.get('sectors')
if not sectors_list:
    raise ValueError("No sectors found in configuration.")

# Make an html plot with the sectors
fig = go.Figure()
for sec in sectors_list:
    azimuth_center = sec['ray']['azimuth_center']
    azimuth_span = sec['ray']['azimuth_span']
    
    min_range = sec['note_mapper']['min_range']
    max_range = sec['note_mapper']['max_range']
    color = sec['color']

    # Create a meshgrid for the sector
    azimuth_deg = azimuth_center + np.array([-0.5*azimuth_span, -0.5*azimuth_span, 0.5*azimuth_span, 0.5*azimuth_span])
    range_values = np.array([min_range, max_range, max_range, min_range])

    # convert from range azimuth to cartesian coordinates
    azimuth_rad = np.radians(azimuth_deg)  # Convert degrees to radians
    x = range_values * np.cos(azimuth_rad)  # X coordinates
    y = range_values * np.sin(azimuth_rad)  # Y coordinates

    # Plot the sector as filled polygons in cartesian coordinates
    fig.add_trace(go.Scatter(x=x, y=y, fill='toself', mode='lines', name=sec['name'],
                             line=dict(color=color_to_plotly(sec['color'])),
                             fillcolor=color_to_plotly(sec['color'])))
    
    # Update the layout of the figure so that the x and y axes are equal
    fig.update_layout(
        title="Sectors",
        xaxis_title="X (m)",
        yaxis_title="Y (m)",
        showlegend=True,
        width=800,
        height=800,
        xaxis=dict(scaleanchor="y", scaleratio=1),
        yaxis=dict(constrain='domain')
    )

    # Save the figure as an HTML file
    fig.write_html("sectors_plot.html")

    #fig.write_image("sectors_plot.png", scale=2, width=800, height=800, engine="kaleido")
