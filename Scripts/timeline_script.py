"""
Script to create a project timeline figure for use in the methodology

Version = 0.4
Author = x
"""

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates


# -----------------------------------------------------------------------------
# Data
# -----------------------------------------------------------------------------

csv_path = "static/dates.csv"
output_path = "output/plots/project_timeline.png"

df = pd.read_csv(csv_path, na_values=["n/a", "", " "])

for col in ["start_date", "end_date"]:
    df[col] = pd.to_datetime(df[col], dayfirst=True, errors="coerce")

# Fix reversed ranges if any
reversed_mask = (
    df["start_date"].notna()
    & df["end_date"].notna()
    & (df["end_date"] < df["start_date"])
)
df.loc[reversed_mask, ["start_date", "end_date"]] = df.loc[
    reversed_mask, ["end_date", "start_date"]
].to_numpy()

# Classify
df["type"] = "Milestone"
df.loc[df["start_date"].notna() & df["end_date"].notna(), "type"] = "Sprint window"

# Sort + layout
plot_df = df.sort_values("start_date").reset_index(drop=True)
plot_df["y"] = list(range(len(plot_df), 0, -1))


# -----------------------------------------------------------------------------
# Style
# -----------------------------------------------------------------------------

PAL = {
    "milestone": "#34495E",
    "sprint": "#2A9D8F",
    "sprint_edge": "#176D64",
    "live": "#A5652A",
    "hotfix": "#7A5195",
    "grid": "#E6E6E6",
    "row": "#F8F8F8",
    "text": "#1A1A1A",
}

plt.rcParams.update(
    {
        "font.family": "DejaVu Sans",
        "font.size": 9,
        "axes.titlesize": 13,
        "axes.titleweight": "bold",
        "axes.labelsize": 9.5,
        "xtick.labelsize": 8.5,
        "ytick.labelsize": 9,
        "figure.dpi": 300,
        "savefig.dpi": 600,
        "axes.linewidth": 0.7,
    }
)

fig, ax = plt.subplots(figsize=(8.2, 4.6), constrained_layout=True)


# -----------------------------------------------------------------------------
# Plot
# -----------------------------------------------------------------------------

# Alternating rows
for _, r in plot_df.iterrows():
    if int(r["y"]) % 2 == 0:
        ax.axhspan(r["y"] - 0.38, r["y"] + 0.38, color=PAL["row"], zorder=0)

for _, r in plot_df.iterrows():
    y = r["y"]
    title = r["Title"]
    version = "" if pd.isna(r["version"]) else f" v{r['version']}"

    # --- Sprint windows ---
    if r["type"] == "Sprint window":
        ax.plot(
            [r["start_date"], r["end_date"]],
            [y, y],
            color=PAL["sprint"],
            lw=7.5,
            solid_capstyle="butt",
            zorder=3,
        )

        # edges
        ax.plot(
            [r["start_date"], r["start_date"]],
            [y - 0.17, y + 0.17],
            color=PAL["sprint_edge"],
            lw=1.3,
            zorder=4,
        )
        ax.plot(
            [r["end_date"], r["end_date"]],
            [y - 0.17, y + 0.17],
            color=PAL["sprint_edge"],
            lw=1.3,
            zorder=4,
        )

    # --- Milestones ---
    else:
        if "HotFix" in title:
            colour = PAL["hotfix"]
            marker = "D"
        elif "Live" in title:
            colour = PAL["live"]
            marker = "o"
        else:
            colour = PAL["milestone"]
            marker = "o"

        ax.scatter(
            [r["start_date"]],
            [y],
            s=52,
            marker=marker,
            color=colour,
            edgecolor="white",
            linewidth=0.8,
            zorder=5,
        )

        ax.annotate(
            f"{title}{version}",
            xy=(r["start_date"], y),
            xytext=(10, 0),
            textcoords="offset points",
            ha="left",
            va="center",
            fontsize=8.2,
            color=PAL["text"],
        )


# -----------------------------------------------------------------------------
# Axis
# -----------------------------------------------------------------------------

labels = []
for _, r in plot_df.iterrows():
    version = "" if pd.isna(r["version"]) else f" v{r['version']}"
    labels.append(f"{r['Title']}{version}")

ax.set_yticks(plot_df["y"])
ax.set_yticklabels(labels)
ax.tick_params(axis="y", length=0, pad=8)

start = plot_df["start_date"].min() - pd.Timedelta(days=25)
end = pd.concat([plot_df["start_date"], plot_df["end_date"]]).dropna().max() + pd.Timedelta(days=40)

ax.set_xlim(start, end)
ax.set_ylim(0.45, len(plot_df) + 0.65)

ax.xaxis.set_major_locator(mdates.MonthLocator(interval=1))
ax.xaxis.set_major_formatter(mdates.DateFormatter("%b\n%Y"))

ax.grid(axis="x", color=PAL["grid"], lw=0.7)
ax.grid(axis="y", visible=False)

for s in ["top", "right", "left"]:
    ax.spines[s].set_visible(False)
ax.spines["bottom"].set_color("#555555")

ax.set_xlabel("Project date")
ax.set_title("Gaps & Overlaps Project Timeline", loc="left", pad=10)


fig.savefig(output_path, bbox_inches="tight")
plt.close(fig)