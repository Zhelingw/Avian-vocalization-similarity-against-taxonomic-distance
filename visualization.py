import matplotlib.pyplot as plt
import plotly.graph_objects as go

def draw_scatter_static(data: list) -> None:
    """
    Creates a static scatter plot from given data.

    Preconditions:
    - all([comparison["distance"] is not None for comparison in data])
    - all([comparison["similarity"] is not None for comparison in data])
    - all([comparison["item1"] is not None for comparison in data])
    - all([comparison["item2"] is not None for comparison in data])

    """
    x = []
    y = []
    labels = []

    for comparison in data:
        print(comparison)
        x.append(comparison["distance"])
        y.append(comparison["similarity"])
        labels.append(comparison["item1"] + " & " + comparison["item2"])

    plt.figure(figsize=(8, 6))
    plt.scatter(x, y, s=50)

    plt.xlabel('Taxonomic Distance')
    plt.ylabel('Vocalization Similarity')
    plt.title('Static 2D Scatter Plot')

    i = 0
    for label in labels:
        plt.annotate(label, xy=(x[i], y[i]), textcoords="offset points", xytext=(0,10), ha='center')
        i += 1

    plt.show()


def draw_scatter_interactive(data: list) -> None:
    """
    Creates an interactive scatter plot from given data.

    Preconditions:
    - all([comparison["distance"] is not None for comparison in data])
    - all([comparison["similarity"] is not None for comparison in data])
    - all([comparison["item1"] is not None for comparison in data])
    - all([comparison["item2"] is not None for comparison in data])
    """
    x = []
    y = []
    labels = []

    for comparison in data:
        x.append(comparison["distance"])
        y.append(comparison["similarity"])
        labels.append(comparison["item1"] + " & " + comparison["item2"])

    # Create the interactive scatter plot
    fig = go.Figure(data=go.Scatter(
        x=x,
        y=y,
        mode='markers+text',
        text=labels,
        textposition='top center',
        marker=dict(size=12, color='royalblue'),

        # Text to display when hovering over a point
        hovertemplate=(
                "<b>%{text}</b><br>" +
                "Distance: %{x}<br>" +
                "Similarity: %{y}" +
                "<extra></extra>"
        )
    ))

    # Update the plot with size, titles, and axis labels
    fig.update_layout(
        title='Interactive 2D Scatter Plot',
        xaxis_title='Taxonomic Distance',
        yaxis_title='Vocalization Similarity',
        width=800,
        height=600
    )

    fig.show()


example = {
    'item1': "AAA",
    'item2': "BBB",
    'distance': 5,
    'similarity': 5,
}

draw_scatter_interactive([example])
