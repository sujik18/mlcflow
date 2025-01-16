# MLC Automation

This repository provides the codebase for **MLC Automation**, a streamlined interface for creating workflow automations. It is created as a simplified version of [Collective Mind](https://github.com/mlcommons/ck/tree/master/cm) package to be used in MLPerf Automations.

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

Each target has its own set of specific actions to tailor automation workflows.

## CM compatibility layer

MLC has a compatibility layer where by it supports MLCommons CM automations.

## Architectural Diagram

This project is a work in progress and the below diagram is expected to change.

```mermaid
classDiagram
    class Action {
        -repos_path : str
        -cfg : dict
        -repos : list
        +execute(args)
        +access(options)
        +asearch(i)
        +find_target_folder(target)
        +load_repos_and_meta()
        +load_repos()
    }
    class RepoAction {
        +github_url_to_user_repo_format(url)
        +pull(args)
        +list(args)
    }
    class ScriptAction {
        +run(args)
        +list(args)
    }
    class CacheAction {
        +show(args)
        +list(args)
    }
    class ExperimentAction {
        +show(args)
        +list(args)
    }
    class CfgAction {
        +load(args)
        +unload(args)
    }
    class Repo {
        -path : str
        -meta : dict
    }
    class Automation {
        -cmind : Action
        +execute(args)
    }
    class Index {
        +find()
    }

    Action <|-- RepoAction
    Action <|-- ScriptAction
    Action <|-- CacheAction
    Action <|-- ExperimentAction
    Action <|-- CfgAction
    Repo "1" *-- Action
    Automation "1" *-- Action

    class get_action {
        +actions : dict
        +get_action(target)
    }

    main --> get_action
    get_action --> RepoAction
    get_action --> ScriptAction
    get_action --> CacheAction
    get_action --> ExperimentAction
    get_action --> CfgAction
```

