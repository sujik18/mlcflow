**MLCFlow: Simplifying MLPerf Automations**

[![License](https://img.shields.io/badge/License-Apache%202.0-green)](LICENSE.md)
[![Downloads](https://static.pepy.tech/badge/mlcflow)](https://pepy.tech/project/mlcflow)
[![MLC script automation features test](https://github.com/mlcommons/mlperf-automations/actions/workflows/test-mlc-script-features.yml/badge.svg?cache-bust=1)](https://github.com/mlcommons/mlperf-automations/actions/workflows/test-mlc-script-features.yml)


MLCFlow is a versatile CLI and Python interface developed by MLCommons in collaboration with a dedicated team of volunteers (see [Contributors](CONTRIBUTORS.md)). It serves as a streamlined replacement for the [CMind](https://github.com/mlcommons/ck/tree/master/cm) tool, designed to drive the automation workflows of MLPerf benchmarks more efficiently. 

The concept behind CMind originated from **Grigori Fursin**, while the **MLPerf Automations** project was created by **Grigori Fursin** and **Arjun Suresh**, whose collective contributions laid the foundation for modernizing MLPerf benchmarking tools.

### Key Features
Building upon the core idea of CMind—wrapping native scripts with Python wrappers and YAML metadata—MLCFlow focuses exclusively on key automation components: **Scripts**, along with its complementary modules: **Cache**, **Docker**, and **Experiments**. This targeted design simplifies both implementation and interface, enabling a more user-friendly experience.

### Status
MLCFlow is currently a **work in progress** and not yet ready for production use. If you are interested in contributing to its initial development, please email [arjun@mlcommons.org](mailto:arjun@mlcommons.org) to join the daily development meetings and see [Issues](https://github.com/mlcommons/mlcflow/issues) for seeing the development progress.

### Getting Started
For early contributors, please use the `mlc` branch of the [MLPerf Automations](https://github.com/mlcommons/mlperf-automations) repository while working with MLCFlow.


---

## MLC CLI Overview

The **MLC Command-Line Interface (CLI)** enables users to perform actions on specified targets using a simple syntax:

```bash
mlc <action> <target> [options]
```

### Key Components:
- **`<action>`**: The operation to be performed.
- **`<target>`**: The object on which the action is executed.
- **`[options]`**: Additional parameters passed to the action.

---

### Supported Targets and Actions

#### 1. **Repo**
- Actions related to repositories, such as cloning or updating.

#### 2. **Script**
- Manage or execute automation scripts.

#### 3. **Cache**
- Handle cached data, including cleanup or inspection.

Each target has its own set of specific actions to tailor automation workflows as specified below.



| Target | Action          |
|--------|-----------------|
| script    | run, search, rm, mv, cp, add, list, test, docker, show          |
| cache    | search, rm, list, show, find          |
| repo    | pull, search, rm, list, find          |


## CM compatibility layer

MLC has a compatibility layer where by it supports MLCommons CM automations - Script, Cache and Experiment. 

## Architectural Diagram

```mermaid
classDiagram
    class Action {
        +execute(args)
        +access(options)
        +find_target_folder(target)
        +load_repos_and_meta()
        +load_repos()
        +conflicting_repo(repo_meta)
        +register_repo(repo_meta)
        +unregister_repo(repo_path)
        +add(i)
        +rm(i)
        +save_new_meta(i, item_id, item_name, target_name, item_path, repo)
        +update(i)
        +is_uid(name)
        +cp(run_args)
        +copy_item(source_path, destination_path)
        +search(i)
    }
    class RepoAction {
        +find(run_args)
        +github_url_to_user_repo_format(url)
        +pull_repo(repo_url, branch, checkout)
        +pull(run_args)
        +list(run_args)
        +rm(run_args)
    }
    class ScriptAction {
        +search(i)
        +rm(i)
        +dynamic_import_module(script_path)
        +call_script_module_function(function_name, run_args)
        +docker(run_args)
        +run(run_args)
        +test(run_args)
        +list(args)
    }
    class CacheAction {
        +search(i)
        +find(i)
        +rm(i)
        +show(run_args)
        +list(args)
    }
    class ExperimentAction {
        +show(args)
        +list(args)
    }
    class CfgAction {
        +load(args)
    }
    class Index {
        +add(meta, folder_type, path, repo)
        +get_index(folder_type, uid)
        +update(meta, folder_type, path, repo)
        +rm(meta, folder_type, path)
        +build_index()
    }
    class Item {
        +meta
        +path
        +repo
        +_load_meta()
    }
    class Repo {
        +path
        +meta
        +_load_meta()
    }
    class Automation {
        +action_object
        +automation_type
        +meta
        +path
        +_load_meta()
        +search(i)
    }

    Action <|-- RepoAction
    Action <|-- ScriptAction
    Action <|-- CacheAction
    Action <|-- ExperimentAction
    Action <|-- CfgAction
    RepoAction o-- Repo
    ScriptAction o-- Automation
    CacheAction o-- Index
    ExperimentAction o-- Index
    CfgAction o-- Index
    Index o-- Repo
    Index o-- Item
    Item o-- Repo
    Automation o-- Action
```

