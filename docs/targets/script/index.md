# Script

Currently, the following actions are supported for script:

## Find

`find` action is used to list the path of partiicular scripts present in MLC repos registered in MLC.

**Syntax**

```bash
mlc find script --tags=<list_of_tags_matching_to_particular_script>
```

OR

```bash
mlc find script <script_alias>
```

OR

```bash
mlc find script <script_uid>
```

OR

```bash
mlc find script <script_alias>,<script_uid>
```

Examples of `find` action for `script` target could be found inside the GitHub action workflow [here](https://github.com/mlcommons/mlcflow/blob/d0269b47021d709e0ffa7fe0db8c79635bfd9dff/.github/workflows/test-mlc-core-actions.yaml).

## Show

`show` action is used to list the path and meta data of partiicular scripts present in MLC repos registered in MLC.

**Syntax**

```bash
mlc show script --tags=<list_of_tags_matching_to_particular_script>
```

OR

```bash
mlc show script <script_alias>
```

OR

```bash
mlc show script <script_uid>
```

OR

```bash
mlc show script <script_alias>,<script_uid>
```

Examples of `show` action for `script` target could be found inside the GitHub action workflow [here](https://github.com/mlcommons/mlcflow/blob/d0269b47021d709e0ffa7fe0db8c79635bfd9dff/.github/workflows/test-mlc-core-actions.yaml).

## Rm

`rm` action is used to remove one/more scripts present in repos which are registered in MLC.

**Syntax**

```bash
mlc rm script --tags=<list_of_tags_matching_to_particular_script>
```

OR

```bash
mlc rm script <script_alias>
```

OR

```bash
mlc rm script <script_uid>
```

`-f` could be used to force remove scripts. Without `-f`, user would be prompted for confirmation to delete a script.

Examples of `rm` action for `script` target could be found inside the GitHub action workflow [here](https://github.com/mlcommons/mlcflow/blob/d0269b47021d709e0ffa7fe0db8c79635bfd9dff/.github/workflows/test-mlc-core-actions.yaml).

## Add

`add` script is used to add a new script to any of the registered MLC repos.

**Syntax**

```bash
mlc add script <registered_mlc_repo_name>:<new_script_name> --tags=<set_of_tags> --template=<set_of_tags>
```

* `--tags` contains set of tags to identify the newly created script.
* `--template` contains set of tags of the template script from which we are creating the new script. If not specified, default [template](https://github.com/mlcommons/mlperf-automations/tree/main/script/template-script) would be considered.
* `registered_mlc_repo_name` is of the format `repo_owner`@`repo_name`.

Examples of `add` action for `script` target could be found inside the GitHub action workflow [here](https://github.com/mlcommons/mlcflow/blob/d0269b47021d709e0ffa7fe0db8c79635bfd9dff/.github/workflows/test-mlc-core-actions.yaml).

## Mv

`mv` script is used to move a script from source repo to destination repo.

**Syntax**

```bash
mlc mv script <registered_mlc_source_repo_name>:<source_script_name> <registered_mlc_target_repo_name>:<source_script_name> 
```

* `registered_mlc_source/target_repo_name` is of the format `repo_owner`@`repo_name`.

Examples of `mv` action for `script` target could be found inside the GitHub action workflow [here](https://github.com/mlcommons/mlcflow/blob/d0269b47021d709e0ffa7fe0db8c79635bfd9dff/.github/workflows/test-mlc-core-actions.yaml).

## Cp

`cp` script is used to copy a script from source repo to destination repo.

**Syntax**

```bash
mlc cp script <registered_mlc_source_repo_name>:<source_script_name> <registered_mlc_target_repo_name>:<source_script_name> 
```

* `registered_mlc_source/target_repo_name` is of the format `repo_owner`@`repo_name`.

Examples of `cp` action for `script` target could be found inside the GitHub action workflow [here](https://github.com/mlcommons/mlcflow/blob/d0269b47021d709e0ffa7fe0db8c79635bfd9dff/.github/workflows/test-mlc-core-actions.yaml).

## Run

`run` script is used to run scripts from any of the repos registered in MLC.

**Syntax**

```bash
mlc run script --tags=<list_of_tags_matching_to_particular_script> <input_flags>
```

OR

```bash
mlcr <list_of_tags_matching_to_particular_script> <input_flags>
```

* `input_flags` are the additional input that could be given to a particular script. They are specified in the format `--<name_of_input_flag>=<value>`. Some of the examples could be found in run commands from inference documentation [here](https://docs.mlcommons.org/inference/benchmarks/language/gpt-j/).

Examples of `run` action for `script` target could be found inside the GitHub action workflow [here](https://github.com/mlcommons/mlcflow/blob/d0269b47021d709e0ffa7fe0db8c79635bfd9dff/.github/workflows/test-mlc-core-actions.yaml).

## Docker

`docker` script is used to run scripts inside a container environment.

**Syntax**

```bash
mlc docker script --tags=<list_of_tags_matching_to_particular_script> <input_flags>
```

* `input_flags` are the additional input that could be given to a particular script. They are specified in the format `--<name_of_input_flag>=<value>`. Some of the examples could be found in run commands from inference documentation [here](https://docs.mlcommons.org/inference/benchmarks/language/gpt-j/).

## Test

`test` script is used to test run scripts. Note that `test` action could only be performed for scripts where `tests` section is configured in `meta.yaml`

**Syntax**

```bash
mlc test script --tags=<list_of_tags_matching_to_particular_script>
```

* Please click [here](https://github.com/mlcommons/mlperf-automations/blob/0e647d7126e610d010a21dbfccca097febe80af9/script/get-generic-sys-util/meta.yaml#L24) to find the example script where the tests are being defined.