# Plotly 深色主題配置
PLOTLY_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(20,20,40,0.5)",
    font=dict(color="#d0d0e8"),
    xaxis=dict(gridcolor="rgba(60,60,100,0.3)", zerolinecolor="rgba(60,60,100,0.3)"),
    yaxis=dict(gridcolor="rgba(60,60,100,0.3)", zerolinecolor="rgba(60,60,100,0.3)"),
    legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color="#b0b0c8")),
)


def apply_dark_theme(fig):
    """套用深色主題到 Plotly 圖表"""
    fig.update_layout(**PLOTLY_LAYOUT)
    return fig
