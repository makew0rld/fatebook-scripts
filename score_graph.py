import sys
import csv
from datetime import datetime, timedelta, timezone
from typing import List, Tuple
import matplotlib.pyplot as plt

HEADERS = [
    "Question title",
    "Multiple choice option",
    "Forecast created by",
    "Forecast (scale = 0-1)",
    "Forecast created at",
    "Question created by",
    "Question created at",
    "Question resolve by",
    "Resolution",
    "Resolved at",
    "Your Brier score for this question",
    "Your relative Brier score for this question",
    "Question notes",
    "Question shared with",
    "Question shared publicly",
    "Question comments",
]


def parse_time(ts: str) -> datetime:
    # https://github.com/Sage-Future/fatebook/issues/90
    return datetime.strptime(ts, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)


# Keep track of questions that have been seen
seen_ids = set()
# For each question
scores: List[float] = []
resolution_times: List[datetime] = []

with open(sys.argv[1]) as f:
    reader = csv.reader(f)
    headers = next(reader)
    if headers != HEADERS:
        print(
            "warning: CSV headers have changed since this program was written, data may be parsed incorrectly"
        )
    for row in reader:
        # Skip questions not by me
        # if row[2] != "<name>" or row[5] != "<name>":
        #     continue
        if not row[8]:  # No resolution
            continue
        if row[0] + row[6] in seen_ids:
            # Question "ID" is combo of title and creation time
            continue
        seen_ids.add(row[0] + row[6])
        scores.append(float(row[10]))
        resolution_times.append(parse_time(row[9]))

# Sort the data by resolution time
resolution_times, scores = zip(*sorted(zip(resolution_times, scores)))

# Calculate the averages now that the data is sorted

# Average of scores for each question and all preceding ones
total_averages = []
for i in range(len(scores)):
    total_averages.append(sum(scores[: i + 1]) / (i + 1))


def rolling_average(days: int) -> List[Tuple[datetime, float]]:
    rolling_averages: List[Tuple[datetime, float]] = []
    # end = the beginning of the day after the first resolution
    # This means the first average window will only include predictions made in the first day
    end = (resolution_times[0] + timedelta(days=1)).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    start = end - timedelta(days=days)
    start_i = 0  # In resolution_times

    # Iterate over time until the last data point
    while end < resolution_times[-1] + timedelta(days=1):
        # Gather scores for this window
        tmp_scores = []
        for i, (resolution_time, score) in enumerate(
            zip(resolution_times[start_i:], scores[start_i:])
        ):
            if resolution_time < start:
                # For the next time the average is calculated (next when loop), skip over these resolutions that are too old
                start_i += i + 1
                continue
            if resolution_time > end:
                # Now outside the window
                break
            tmp_scores.append(score)

        if len(tmp_scores) == 0:
            # No data for this window
            continue
        # Calculate average for this window and move on
        rolling_averages.append((end, sum(tmp_scores) / len(tmp_scores)))
        start += timedelta(days=1)
        end += timedelta(days=1)

    return rolling_averages


# Second version of the function that updates only when a question is resolved, looking X days back at that point
def rolling_average2(days: int) -> List[Tuple[datetime, float]]:
    rolling_averages: List[Tuple[datetime, float]] = []
    for end_resolution_time in resolution_times:
        start = end_resolution_time - timedelta(days=days)
        tmp_scores = []
        for score, resolution_time in zip(scores, resolution_times):
            if resolution_time <= start:
                continue
            if resolution_time > end_resolution_time:
                break
            tmp_scores.append(score)
        rolling_averages.append(
            (end_resolution_time, sum(tmp_scores) / len(tmp_scores))
        )
    return rolling_averages


three_month = rolling_average2(91)
one_month = rolling_average2(30)

fig, ax = plt.subplots()
ax.set_ylim(0, 2)

# ax.plot(resolution_times, scores, label="question scores", marker="o", markersize=3)  # type: ignore
ax.scatter(resolution_times, scores, label="question scores", marker="o", s=5)  # type: ignore

line_kwargs = {"marker": None, "markersize": 3}
# ax.plot(
#     *zip(*one_month),
#     label=f"1-month rolling average ({one_month[-1][1]:.2f})",
#     **line_kwargs,
# )
ax.plot(
    *zip(*three_month),
    label=f"3-month rolling average ({three_month[-1][1]:.2f})",
    **line_kwargs,
)
ax.plot(
    resolution_times,  # type: ignore
    total_averages,
    label=f"total average ({total_averages[-1]:.2f})",
    **line_kwargs,
)
plt.legend()
plt.show()
