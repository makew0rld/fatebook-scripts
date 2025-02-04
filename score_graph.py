import sys
import csv
from datetime import datetime, timedelta, timezone
from typing import List, NamedTuple, Tuple
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
    "Question tags",
]


def parse_time(ts: str) -> datetime:
    # https://github.com/Sage-Future/fatebook/issues/90
    ts = ts if len(ts.split(":")[-1]) == 2 else ts[:-1] + "0" + ts[-1]
    return datetime.strptime(ts, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)


class Question(NamedTuple):
    created_at: datetime
    resolved_at: datetime
    score: float


questions: List[Question] = []
# Keep track of questions that have been seen
seen_ids = set()

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
        if row[8] == "AMBIGUOUS":
            continue
        if row[0] + row[6] in seen_ids:
            # Question "ID" is combo of title and creation time
            continue
        seen_ids.add(row[0] + row[6])
        questions.append(
            Question(parse_time(row[6]), parse_time(row[9]), float(row[10]))
        )

# Sort the data by creation time
questions.sort(key=lambda q: q.created_at)

# for q in questions:
#     print(q.created_at.date(), q.score)

# Calculate the averages now that the data is sorted

# Average of scores for each question and all preceding ones
total_averages = []
for i in range(len(questions)):
    total_averages.append(sum([q.score for q in questions[: i + 1]]) / (i + 1))


def rolling_average(days: int) -> List[Tuple[datetime, float]]:
    rolling_averages: List[Tuple[datetime, float]] = []
    for end_creation_time in [q.created_at for q in questions]:
        start = end_creation_time - timedelta(days=days)
        tmp_scores = []
        for creation_time, _, score in questions:
            if creation_time <= start:
                continue
            if creation_time > end_creation_time:
                break
            tmp_scores.append(score)
        rolling_averages.append((end_creation_time, sum(tmp_scores) / len(tmp_scores)))
    return rolling_averages


three_month = rolling_average(91)

three_month_latest = three_month[-1][1]
avg_latest = total_averages[-1]

print("Resolved questions:", len(questions))
print("Three month average:", three_month_latest)
print("Total average:", avg_latest)

fig, ax = plt.subplots()
ax.set_ylim(0, 2)

line_kwargs = {"marker": None, "markersize": 3}
ax.plot(
    *zip(*three_month),
    label=f"3-month rolling average (latest: {three_month_latest:.2f})",
    color="tab:blue",
    **line_kwargs,
)
ax.plot(
    [q.created_at for q in questions],  # type: ignore
    total_averages,
    label=f"total average (latest: {avg_latest:.2f})",
    color="tab:orange",
    **line_kwargs,
)

# Sort the data by resolution time, to graph individual question scores
questions.sort(key=lambda q: q.resolved_at)

ax.scatter(
    [q.resolved_at for q in questions],  # type: ignore
    [q.score for q in questions],
    label=f"question scores (total: {len(questions)})",
    marker="o",
    s=5,
    c="tab:green",
)

plt.legend()
plt.show()
