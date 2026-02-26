# Plotly 專業深色主題
PLOTLY_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(15,15,30,0.7)",
    font=dict(family="Inter, -apple-system, sans-serif", color="#c8c8e0", size=12),
    xaxis=dict(
        gridcolor="rgba(50,50,90,0.25)", zerolinecolor="rgba(50,50,90,0.3)",
        linecolor="rgba(50,50,90,0.5)", tickfont=dict(size=10, color="#9090b0"),
        showgrid=True, gridwidth=1,
    ),
    yaxis=dict(
        gridcolor="rgba(50,50,90,0.25)", zerolinecolor="rgba(50,50,90,0.3)",
        linecolor="rgba(50,50,90,0.5)", tickfont=dict(size=10, color="#9090b0"),
        showgrid=True, gridwidth=1, side="right",
    ),
    legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color="#b0b0c8", size=11),
                bordercolor="rgba(0,0,0,0)"),
    margin=dict(l=10, r=10, t=35, b=10),
    hoverlabel=dict(bgcolor="rgba(20,20,45,0.95)", bordercolor="rgba(80,80,140,0.5)",
                    font=dict(color="#e0e0f0", size=12)),
    hovermode="x unified",
)


def apply_dark_theme(fig):
    """套用專業深色主題"""
    fig.update_layout(**PLOTLY_LAYOUT)
    fig.update_xaxes(showspikes=True, spikecolor="rgba(100,100,200,0.3)",
                     spikethickness=1, spikedash="dot", spikemode="across")
    fig.update_yaxes(showspikes=True, spikecolor="rgba(100,100,200,0.3)",
                     spikethickness=1, spikedash="dot")
    return fig
