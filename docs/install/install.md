---
hide:
  - toc
---

# Installation

MLCFlow needs `python>=3.7`, `python3-pip` installed on your system.

## Activate a Virtual ENV for MLCFlow (Optional)
This step is not mandatory. But the latest `pip` install requires this or else will need the `--break-system-packages` flag while installing.

```bash
python3 -m venv mlcflow
source mlcflow/bin/activate
```

## Install MLCFLow

If you are not using virtual ENV for installation, the latest `pip` install requires the `--break-system-packages` flag while installing.

=== "Use the latest stable release"
    ```bash
     pip install mlcflow
    ```
=== "To use mlcflow with latest changes"
    Fetches the latest changes developers are working on from the `dev` branch.
    ```bash
     pip install git+https://github.com/mlcommons/mlcflow.git@dev
    ```

Now, you are ready to use the `mlc` commands. Currently, `mlc` is being used to automating the benchmark runs for:

* [MLPerf Inference](https://docs.mlcommons.org/inference/)
* [MLPerf Automotive]()
* [MLPerf Training]()
