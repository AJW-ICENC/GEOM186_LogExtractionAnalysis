"""
Project Timeline Figure
Dissertation / Journal Version

Version = 0.9
"""

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates


# -----------------------------------------------------------------------------
# Inputs
# -----------------------------------------------------------------------------

csv_path = "static/dates.csv"
output_path = "output/plots/project_timeline.png"

df = pd.read_csv(csv_path, na_values=["n/a", "", " "])

for col in ["start_date", "end_date"]:
    df[col] = pd.to_datetime(
        df[col],
        dayfirst=True,
        errors="coerce"
    )

# -----------------------------------------------------------------------------
# Clean dates
# -----------------------------------------------------------------------------

mask = (
    df["start_date"].notna()
    & df["end_date"].notna()
    & (df["end_date"] < df["start_date"])
)

df.loc[mask, ["start_date", "end_date"]] = df.loc[
    mask,
    ["end_date", "start_date"]
].to_numpy()

# -----------------------------------------------------------------------------
# Classification
# -----------------------------------------------------------------------------

df["type"] = "Milestone"

df.loc[
    df["start_date"].notna()
    & df["end_date"].notna(),
    "type"
] = "Sprint"

plot_df = (
    df.sort_values("start_date")
    .reset_index(drop=True)
)

# -----------------------------------------------------------------------------
# Layout
# -----------------------------------------------------------------------------

levels = [0.00, 0.18, -0.18, 0.36, -0.36]

plot_df["y"] = [
    levels[i % len(levels)]
    for i in range(len(plot_df))
]

# -----------------------------------------------------------------------------
# Style
# -----------------------------------------------------------------------------

plt.rcParams.update(
    {
        "font.family": "Times New Roman",
        "font.size": 10,
        "axes.labelsize": 10,
        "xtick.labelsize": 9,
        "ytick.labelsize": 9,
        "figure.dpi": 300,
        "savefig.dpi": 600,
    }
)

fig, ax = plt.subplots(
    figsize=(8.2, 2.6),
    constrained_layout=True
)

# -----------------------------------------------------------------------------
# Colours
# -----------------------------------------------------------------------------

COLOURS = {
    "default": "#34495E",
    "live": "#2A9D8F",
    "hotfix": "#E76F51",
    "sprint": "#707070",
}

# -----------------------------------------------------------------------------
# Plot events
# -----------------------------------------------------------------------------

for _, row in plot_df.iterrows():

    label = row["Title"]

    if pd.notna(row["version"]):
        label += f" v{row['version']}"

    y = row["y"]

    # -------------------------------------------------------------------------
    # Sprint windows
    # -------------------------------------------------------------------------

    if row["type"] == "Sprint":

        ax.plot(
            [row["start_date"], row["end_date"]],
            [y, y],
            color=COLOURS["sprint"],
            linewidth=4,
            solid_capstyle="butt",
            zorder=2,
        )

        midpoint = row["start_date"] + (
            row["end_date"] - row["start_date"]
        ) / 2

        ax.annotate(
            label,
            xy=(midpoint, y),
            xytext=(0, 12),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=8.5,
        )

    # -------------------------------------------------------------------------
    # Milestones
    # -------------------------------------------------------------------------

    else:

        title = str(row["Title"])

        if "Live" in title:
            colour = COLOURS["live"]
            size = 95

        elif "HotFix" in title:
            colour = COLOURS["hotfix"]
            size = 95

        else:
            colour = COLOURS["default"]
            size = 80

        ax.scatter(
            row["start_date"],
            y,
            s=size,
            color=colour,
            edgecolor="white",
            linewidth=0.7,
            zorder=4,
        )

        label_y = 10 if y >= 0 else -10

        ax.annotate(
            label,
            xy=(row["start_date"], y),
            xytext=(8, label_y),
            textcoords="offset points",
            ha="left",
            va="center",
            fontsize=9,
        )

# -----------------------------------------------------------------------------
# Axis formatting
# -----------------------------------------------------------------------------

xmin = (
    plot_df["start_date"].min()
    - pd.Timedelta(days=20)
)

xmax = (
    pd.concat(
        [
            plot_df["start_date"],
            plot_df["end_date"]
        ]
    )
    .dropna()
    .max()
    + pd.Timedelta(days=20)
)

ax.set_xlim(xmin, xmax)
ax.set_ylim(-0.55, 0.55)

ax.set_yticks([])

ax.xaxis.set_major_locator(
    mdates.MonthLocator(interval=1)
)

ax.xaxis.set_major_formatter(
    mdates.DateFormatter("%b\n%Y")
)

ax.grid(
    axis="x",
    linestyle=":",
    linewidth=0.8,
    color="0.82"
)

# Clean axis appearance

for spine in ["top", "right", "left"]:
    ax.spines[spine].set_visible(False)

ax.spines["bottom"].set_linewidth(0.8)

ax.set_xlabel("Date")

# -----------------------------------------------------------------------------
# Save
# -----------------------------------------------------------------------------

fig.savefig(
    output_path,
    bbox_inches="tight"
)

plt.close()