# fatebook-scripts

This repo is for my personal Python scripts for processing data from [Fatebook](https://fatebook.io/).

This project is managed with [uv](https://docs.astral.sh/uv/) because it's the best.
Run scripts with `uv run <script>`.

Currently there's only one script, `score_graph.py`. It creates a graph of how your Brier score
has changed over time when provided with a CSV export from Fatebook.

```
$ uv run score_graph.py path/to/fatebook-forecasts.csv
```

## License

This code is licensed under the MIT license.
