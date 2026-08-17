"""

Project Timeline Figure

"""


# Author: Alex Wallage
# Version: 3
# Date: 17/08/2026

## Enhanced by AI


## Import modules


import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

df = pd.read_csv("static/dates.csv")
df["start_date"] = pd.to_datetime(df["start_date"], dayfirst=True)
df["end_date"] = pd.to_datetime(df["end_date"], dayfirst=True)

# Remove hotfix
df = df[df["Title"] != "HotFix Deployed"]

plt.rcParams.update({
    "font.family": "Times New Roman",
    "font.size": 11
})

fig, ax = plt.subplots(figsize=(10, 3))

# Activities with durations
activities = df[df["end_date"].notna()]

for i, row in enumerate(activities.itertuples()):
    duration = (row.end_date - row.start_date).days
    ax.barh(
        row.Title,
        duration,
        left=row.start_date,
        height=0.5,
        color="#4C78A8"
    )

# Milestones
milestones = df[df["end_date"].isna()]

for row in milestones.itertuples():
    colour = "#2A9D8F" if "Live" in row.Title else "#34495E"
    ax.scatter(
        row.start_date,
        row.Title,
        marker="D",
        s=80,
        color=colour,
        zorder=3,
    )

ax.invert_yaxis()

ax.xaxis.set_major_locator(mdates.MonthLocator())
ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))

ax.grid(axis="x", alpha=0.3)
ax.set_xlabel("Date")
ax.set_ylabel("")

for spine in ["top", "right"]:
    ax.spines[spine].set_visible(False)

plt.tight_layout()
plt.savefig("output/plots/timeline.png", dpi=600)