import argparse
import subprocess
import re
import os
import importlib.util
import platform
import json
import yaml
import sys
import logging
from types import SimpleNamespace
import mlc.utils as utils
from pathlib import Path
import shutil

# Set up logging configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Base class for CLI actions
class Action:
    repos_path = None
    cfg = None
    action_type = None
    logger = None
    local_repo = None
    #mlc = None
    repos = []
    def execute(self, args):
        raise NotImplementedError("Subclasses must implement the execute method")

    # Main access function to simulate a Python interface for CLI
    def access(self, options):
        """
        Access function to simulate CLI actions in Python.

        Args:
        options (dict): Dictionary containing action and relevant parameters.
        """
        #logger.info(f"options in access = {options}") 
        
        action_name = options.get('action')
        if not action_name:
            return {'return': 1, 'error': "'action' key is required in options"}
        #logger.info(f"options = {options}")

        #print(f"options = {options}")
        action_target = options.get('target')
        if not action_target:
            action_target = options.get('automation', 'script')  # Default to script if not provided
        action_target_split = action_target.split(",")
        action_target = action_target_split[0]

        #print(f"action_target = {action_target}")
        action = actions.get(action_target)
        #logger.info(f"action = {action}")

        if action:
            if hasattr(action, action_name):
                # Find the method and call it with the options
                method = getattr(action, action_name)
                #print(f"method = {method}, action = {action}, action_name  = {action_name}")
                result = method(self, options)
                #logger.info(f"result ={result}")
                return result
                #if result['return'] > 0:
                #    return result
            else:
                return {'return': 1, 'error': f"'{action_name}' action is not supported for {action_target}."}
        else:
            return {'return': 1, 'error': f"Action target '{action_target}' is not defined."}
        return {'return': 0}

    def find_target_folder(self, target):
        # Traverse through each folder in REPOS to find the first 'target' folder inside an 'automation' folder
        if not os.path.exists(self.repos_path):
            os.makedirs(self.repos_path, exist_ok=True)
        for repo_dir in os.listdir(self.repos_path):
            #if "mlc" not in repo_dir:
            #    continue
            repo_path = os.path.join(self.repos_path, repo_dir)
            if os.path.isdir(repo_path):
                automation_folder = os.path.join(repo_path, 'automation')
                
                if os.path.isdir(automation_folder):
                    # Check if there's a 'script' folder inside the 'automation' folder
                    target_folder = os.path.join(automation_folder, target)
                    if os.path.isdir(target_folder):
                        return target_folder
        return None

    def load_repos_and_meta(self):
        repos_list = []
        repos_file_path = os.path.join(self.repos_path, 'repos.json')

        # Read the JSON file line by line
        try:
            # Load and parse the JSON file containing the list of repository paths
            with open(repos_file_path, 'r') as file:
                repo_paths = json.load(file)  # Load the JSON file into a list
        except json.JSONDecodeError as e:
            logger.info(f"Error decoding JSON: {e}")
            return []
        except FileNotFoundError:
            logger.info(f"Error: File {repos_file_path} not found.")
            return []
        except Exception as e:
            logger.info(f"Error reading file: {e}")
            return []
        # Iterate through the list of repository paths
        for repo_path in repo_paths:
            repo_path = repo_path.strip()  # Remove any extra whitespace or newlines

           # Skip empty lines
            if not repo_path:
                continue

            meta_yaml_path = os.path.join(repo_path, "meta.yaml")

            # Check if meta.yaml exists
            if not os.path.isfile(meta_yaml_path):
                logger.info(f"Warning: {meta_yaml_path} not found. Skipping...")
                continue

            # Load the YAML file
            try:
                with open(meta_yaml_path, 'r') as yaml_file:
                    meta = yaml.safe_load(yaml_file)
            except yaml.YAMLError as e:
                logger.info(f"Error loading YAML in {meta_yaml_path}: {e}")
                continue

            if meta['alias'] == "local":
                self.local_repo = (meta['alias'], meta['uid'])
            # Create a Repo object and add it to the list
            repos_list.append(Repo(path=repo_path, meta=meta))

        #print(repos_list)
        return repos_list

    def load_repos(self):
        # todo: what if the repo is already found in the repos folder but not registered and we pull the same repo
        # Get the path to the repos.json file in $HOME/MLC
        repos_file_path = os.path.join(self.repos_path, 'repos.json')

        # Check if the file exists
        if not os.path.exists(repos_file_path):
            logger.info(f"Error: File not found at {repos_file_path}")
            return None

        # Load and parse the JSON file
        try:
            with open(repos_file_path, 'r') as file:
                repos = json.load(file)
                return repos
        except json.JSONDecodeError as e:
            logger.info(f"Error decoding JSON: {e}")
            return None
        except Exception as e:
            logger.info(f"Error reading file: {e}")
            return None
    
    def conflicting_repo(self, repo_meta):
        for repo_object in self.repos:
            if repo_object.meta.get('uid', '') == '':
                return {"return": 1, "error": f"UID is not present in file 'meta.yaml' in the repo path {repo_object.path}"}
            if repo_meta["uid"] == repo_object.meta.get('uid', ''):
                #print(f"{repo_meta['path']} {repo_object.path}")
                if repo_meta['path'] == repo_object.path:
                    return {"return": 1, "error": f"Same repo is already registered"}
                else:
                    return {"return": 1, "error": f"Conflicting with repo in the path {repo_object.path}", "conflicting_path": repo_object.path}
        return {"return": 0}
    
    def register_repo(self, repo_meta):
        # Get the path to the repos.json file in $HOME/MLC
        repos_file_path = os.path.join(self.repos_path, 'repos.json')

        with open(repos_file_path, 'r') as f:
            repos_list = json.load(f)
        
        new_repo_path = repo_meta.get('path')
        if new_repo_path and new_repo_path not in repos_list:
            repos_list.append(new_repo_path)
            logger.info(f"Added new repo path: {new_repo_path}")

        with open(repos_file_path, 'w') as f:
            json.dump(repos_list, f, indent=2)
            logger.info(f"Updated repos.json at {repos_file_path}")

    def unregister_repo(self, repo_path):
        logger.info(f"Unregistering the repo in path {repo_path}")
        repos_file_path = os.path.join(self.repos_path, 'repos.json')

        with open(repos_file_path, 'r') as f:
            repos_list = json.load(f)
        
        if repo_path in repos_list:
            repos_list.remove(repo_path)
            with open(repos_file_path, 'w') as f:
                json.dump(repos_list, f, indent=2)  
            logger.info(f"Path: {repo_path} has been removed.")
        else:
            logger.info(f"Path: {repo_path} not found in {repos_file_path}. Nothing to be unregistered!")


    def __init__(self):        
        self.logger = logging.getLogger()
        self.repos_path = os.environ.get('MLC_REPOS', os.path.expanduser('~/MLC/repos'))
        '''
        res = self.access({'action': 'load',
                            'automation': 'cfg,88dce9c160324c5d',
                            'item': 'default'})
        
        #if res['return'] > 0:
        #    return res
        if self.cfg:
            mlc_local_repo_path = os.path.join(self.repos_path, self.cfg.get('MLC_LOCAL_REPO_FOLDER', 'local'))
        else:
        '''
        mlc_local_repo_path = os.path.join(self.repos_path, 'local')
        
        mlc_local_repo_path_expanded = Path(mlc_local_repo_path).expanduser().resolve()

        if not os.path.exists(mlc_local_repo_path):
            os.makedirs(mlc_local_repo_path, exist_ok=True)
        
        if not os.path.isfile(os.path.join(mlc_local_repo_path, "meta.yaml")):
            local_repo_meta = {"alias": "local", "name": "MLC local repository", "uid": utils.get_new_uid()['uid']}
            with open(os.path.join(mlc_local_repo_path, "meta.yaml"), "w") as json_file:
                json.dump(local_repo_meta, json_file, indent=4)
        
        # TODO: what if user changes the mlc local repo path in between
        repo_json_path = os.path.join(self.repos_path, "repos.json")
        if not os.path.exists(repo_json_path):
            with open(repo_json_path, 'w') as f:
                json.dump([str(mlc_local_repo_path_expanded)], f, indent=2)
                logger.info(f"Created repos.json in {os.path.dirname(self.repos_path)} and initialised with local cache folder path: {mlc_local_repo_path}")

        self.local_cache_path = os.path.join(mlc_local_repo_path, "cache")
        if not os.path.exists(self.local_cache_path):
            os.makedirs(self.local_cache_path, exist_ok=True)

        self.repos = self.load_repos_and_meta()
        #logger.info(f"In Action class: {self.repos_path}")
        self.index = Index(self.repos_path, self.repos)


        #self.repos = {
        #'lst': repo_paths
        #}

    def add(self, i):
        """
        Adds a new item to the repository.

        Args:
            i (dict): Input dictionary with the following keys:
                - item_repo (tuple): Repository alias and UID (default: local repo).
                - item (str): Item alias and optional UID in "alias,uid" format.
                - tags (str): Comma-separated tags.
                - new_tags (str): Additional comma-separated tags to add.
                - yaml (bool): Whether to save metadata in YAML format. Defaults to JSON.

        Returns:
            dict: Result of the operation with 'return' code and error/message if applicable.
        """
        # Determine repository
        item_repo = i.get("item_repo")
        if not item_repo:
            item_repo = self.local_repo

        # Parse item details
        item = i.get("item")
        item_name, item_id = (None, None)
        #print(f"i = {i}")
        #return {'return': 1}
        if item:
            item_parts = item.split(",")
            item_name = item_parts[0]
            if len(item_parts) > 1:
                item_id = item_parts[1]

        # Generate a new UID if not provided
        if not item_id:
            res = utils.get_new_uid()
            if res['return'] > 0:
                return res
            item_id = res['uid']

        # Locate repository
        res = self.access(
            {
                "automation": "repo",
                "action": "find",
                "item": f"{item_repo[0]},{item_repo[1]}",
            }
        )
        if res["return"] > 0:
            return res

        # Determine paths and metadata format
        repo_path = res["list"][0].path
        repo_meta = {
                'alias': item_repo[0],
                'uid' : item_repo[1],
                }
        target_name = i.get('target_name', self.action_type)
        target_path = os.path.join(repo_path, target_name)
        if target_name == "cache":
            folder_name = f"""{i["script_alias"]}_{item_name or item_id[:8]}""" if i.get("script_alias") else item_name or item_id
        else:
            folder_name = item_name or item_id

        item_path = os.path.join(target_path, folder_name)
        meta_format = "yaml" if i.get("yaml") else "json"
        item_meta_path = os.path.join(item_path, f"_cm.{meta_format}")

        # Create item directory if it does not exist
        if not os.path.exists(item_path):
            os.makedirs(item_path)

        # Prepare metadata
        item_meta = i.get('meta')
        item_meta.update({
            "alias": item_name,
            "uid": item_id,
        })

        # Process tags
        tags = i.get("tags", "").split(",") if i.get("tags") else []
        new_tags = i.get("new_tags", "").split(",") if i.get("new_tags") else []
        item_meta["tags"] = list(set(tags + new_tags))  # Ensure unique tags

        # Save metadata
        if meta_format == "yaml":
            save_result = utils.save_yaml(item_meta_path, meta=item_meta)
        else:
            save_result = utils.save_json(item_meta_path, meta=item_meta)

        if save_result["return"] > 0:
            return save_result
    
        self.index.add(item_meta, target_name, item_path, repo_meta, repo_path)

        return {
            "return": 0,
            "message": f"Item successfully added at {item_path}",
            "path": item_path,
            "meta": item_meta,
            "repo": {"uid": repo_meta['uid'], "alias": repo_meta['alias'], "path": repo_path}
        }

    def update(self, i):
        """
        Update the tags of found items based on the input.

        Args:
            i (dict): Input dictionary with:
                - tags (str): Comma-separated tags to search for.
                - search_tags (str): Tags to add/update in the found items' meta.

        Returns:
            dict: Return code and message.
        """
        # Step 1: Search for items based on input tags
        target_name = i.get('target_name',"cache")
        i['target_name'] = target_name
        ii = i.copy()

        if i.get('search_tags'):
            ii['tags'] = ",".join(i['search_tags'])
        search_result = self.search(ii)
        if search_result['return'] > 0:
            return search_result

        found_items = search_result['list']
        if not found_items:
            res = self.add(i)
            if res['return'] > 0 :
                return res
            found_items.append(Item(res['path'], res['repo']))
            #return {'return': 0, 'message': 'No items found for the given tags.'}

        # Step 2: Prepare to update tags
        search_tags = i.get("search_tags", [])

        new_tags = set(search_tags)
        if len(found_items) > 1:
            # Step 3: Ask user for confirmation if multiple items are found
            user_input = input(f"{len(found_items)} items found. Do you want to update all? (yes/no): ").strip().lower()
            if user_input not in ['yes', 'y']:
                return {'return': 0, 'message': 'Update operation canceled by the user.'}

        new_meta = i.get('meta')
        if new_meta.get('tags'):
            new_meta['tags'] = i.get('tags').split(",")

        # Step 4: Update tags in each found item
        for item in found_items:
            meta = {}
            # Load the current meta of the item
            item_meta_path = os.path.join(item.path, "_cm.json")
            if os.path.exists(item_meta_path):
                res = utils.load_json(item_meta_path)
                if res['return']> 0:
                    return res
                meta = res['meta']
            if i.get('replace_lists') and i.get("tags"):
                meta["tags"] = i["tags"].split(",")
            else:
                current_tags = set(meta.get("tags", []))
                updated_tags = current_tags.union(new_tags)
                meta["tags"] = list(updated_tags)
            #print(f"meta = {meta}")
            utils.merge_dicts({"dict1": meta, "dict2": new_meta, "append_lists": True, "append_unique":True})
        
            # Save the updated meta back to the item
            item.meta = meta
            #print(f"item.meta = {item.meta}, saved_meta = {saved_meta}")
            save_result = utils.save_json(item_meta_path, meta=meta)
            #print(f"item_meta = {item.meta}, path = {item.path}")
            #print(item.repo_path)
            #return {'return': 1}
            self.index.update(meta, target_name, item.path, item.repo_meta, item.repo_path)

        return {'return': 0, 'message': f"Tags updated successfully for {len(found_items)} item(s).", 'list': found_items }



    def search(self, i):
        indices = self.index.indices
        #print(f"search input = {i}")
        target = i.get('target_name', self.action_type)
        #logger.debug(f"Search target = {target}")
        target_index = indices.get(target)
        result = []
        uid = i.get("uid")
        if target_index:
            if uid:
                for res in target_index:
                    if res["uid"] == uid:
                        it = Item(res['path'], res['repo'])
                        result.append(it)
            else:
                tags= i.get("tags")
                tags_split = tags.split(",")
                n_tags_ = [p for p in tags_split if p.startswith("-")]
                n_tags = [p[1:] for p in n_tags_]
                p_tags = list(set(tags_split) - set(n_tags_))
                for res in target_index:
                    c_tags = res["tags"]
                    if set(p_tags).issubset(set(c_tags)) and set(n_tags).isdisjoint(set(c_tags)):
                        it = Item(res['path'], res['repo'])
                        result.append(it)
        #print(f"Search result for target {target} = {result}")
        return {'return': 0, 'list': result}


class Index:
    def __init__(self, repos_path, repos):
        """
        Initialize the Index class.
        
        Args:
            repos_path (str): Path to the base folder containing repositories.
        """
        self.repos_path = repos_path
        self.repos = repos
        #logger.info(repos)

        logger.info(f"Repos path for Index: {self.repos_path}")
        self.index_files = {
            "script": os.path.join(repos_path, "index_script.json"),
            "cache": os.path.join(repos_path, "index_cache.json"),
            "experiment": os.path.join(repos_path, "index_experiment.json")
        }
        self.indices = {key: [] for key in self.index_files.keys()}
        self.build_index()

    def add(self, meta, folder_type, path, repo_meta, repo_path):
        unique_id = meta['uid']
        alias = meta['alias']
        tags = meta['tags']
        self.indices[folder_type].append({
                    "uid": unique_id,
                    "tags": tags,
                    "alias": alias,
                    "path": path,
                    "repo": {"uid": repo_meta['uid'], "alias": repo_meta['alias'], "path": repo_path}
                })

    def get_index(self, folder_type, uid):
        for index in range(len(self.indices[folder_type])):
            if self.indices[folder_type][index]["uid"] == uid:
                return index
        return -1

    def update(self, meta, folder_type, path, repo_meta, repo_path):
        uid = meta['uid']
        alias = meta['alias']
        tags = meta['tags']
        index = self.get_index(folder_type, uid)
        if index == -1: #add it
            self.add(meta, folder_type, path, repo_meta, repo_path)
            logger.debug(f"Index update failed, new index created for {uid}")
        else:
            self.indices[folder_type][index] = {
                    "uid": uid,
                    "tags": tags,
                    "alias": alias,
                    "path": path,
                    "repo": {"uid": repo_meta['uid'], "alias": repo_meta['alias'], "path": repo_path}
                }

    def build_index(self):
        """
        Build shared indices for script, cache, and experiment folders across all repositories.
        
        Returns:
            None
        """

        #for repo in os.listdir(self.repos_path):
        for repo in self.repos:
            repo_path = repo.path#os.path.join(self.repos_path, repo)
            if not os.path.isdir(repo_path):
                continue

            # Filter for relevant directories in the repo
            for folder_type in ["script", "cache", "experiment"]:
                folder_path = os.path.join(repo_path, folder_type)
                #print(f"folder_path = {folder_path}")
                if not os.path.isdir(folder_path):
                    continue

                # Process each automation directory
                for automation_dir in os.listdir(folder_path):
                    automation_path = os.path.join(folder_path, automation_dir)
                    if not os.path.isdir(automation_path):
                        continue

                    # Check for configuration files (_cm.yaml or _cm.json)
                    for config_file in ["_cm.yaml", "_cm.json"]:
                        config_path = os.path.join(automation_path, config_file)
                        if os.path.isfile(config_path):
                            self._process_config_file(config_path, folder_type, automation_path, repo.path, repo.meta)
                            break  # Only process one config file per automation_dir
        self._save_indices()

    def _process_config_file(self, config_file, folder_type, folder_path, repo_path, repo_meta):
        """
        Process a single configuration file (_cm.json or _cm.yaml) and add its data to the corresponding index.

        Args:
            config_file (str): Path to the configuration file.
            folder_type (str): Type of folder (script, cache, or experiment).
            folder_path (str): Path to the folder containing the configuration file.

        Returns:
            None
        """
        try:
            # Determine the file type based on the extension
            if config_file.endswith(".yaml") or config_file.endswith(".yml"):
                with open(config_file, "r") as f:
                    data = yaml.safe_load(f)
            elif config_file.endswith(".json"):
                with open(config_file, "r") as f:
                    data = json.load(f)
            else:
                logger.info(f"Skipping {config_file}: Unsupported file format.")
                return

            # Extract necessary fields
            unique_id = data.get("uid")
            tags = data.get("tags", [])
            alias = data.get("alias", None)

            # Validate and add to indices
            if unique_id:
                self.indices[folder_type].append({
                    "uid": unique_id,
                    "tags": tags,
                    "alias": alias,
                    "path": folder_path,
                    "repo": {"uid": repo_meta['uid'], "alias": repo_meta['alias'], "path": repo_path}
                })
            else:
                logger.info(f"Skipping {config_file}: Missing 'uid' field.")
        except Exception as e:
            logger.info(f"Error processing {config_file}: {e}")

    '''
    def _process_yaml_file(self, yaml_file, folder_type, folder_path):
        """
        Process a single _cm.yaml file and add its data to the corresponding index.
        
        Args:
            yaml_file (str): Path to the YAML file.
            folder_type (str): Type of folder (script, cache, or experiment).
            folder_path (str): Path to the folder containing the YAML file.
        
        Returns:
            None
        """
        try:
            #logger.info(f"yaml file = {yaml_file}")
            with open(yaml_file, "r") as f:
                data = yaml.safe_load(f)

            unique_id = data.get("uid")
            tags = data.get("tags", [])
            alias = data.get("alias", None)

            if unique_id:
                self.indices[folder_type].append({
                    "uid": unique_id,
                    "tags": tags,
                    "alias": alias,
                    "path": folder_path
                })
            else:
                logger.info(f"Skipping {yaml_file}: Missing 'id' field.")
        except Exception as e:
            logger.info(f"Error processing {yaml_file}: {e}")
    '''

    def _save_indices(self):
        """
        Save the indices to JSON files.
        
        Returns:
            None
        """
        #logger.info(self.indices)
        for folder_type, index_data in self.indices.items():
            output_file = self.index_files[folder_type]
            try:
                with open(output_file, "w") as f:
                    json.dump(index_data, f, indent=4)
                logger.info(f"Shared index for {folder_type} saved to {output_file}.")
            except Exception as e:
                logger.info(f"Error saving shared index for {folder_type}: {e}")


class Item:
    def __init__(self, path, repo):
        self.meta = None
        self.path = path
        self.repo_meta = None
        self.repo_path = repo['path']
        self._load_repo_meta()
        self._load_meta()

    def _load_repo_meta(self):
        yaml_file = os.path.join(self.repo_path, "meta.yaml")

        json_file = os.path.join(self.repo_path, "meta.json")

        if os.path.exists(yaml_file):
            self.repo_meta = utils.read_yaml(yaml_file)
        elif os.path.exists(json_file):
            self.repo_meta = utils.read_json(json_file)
        else:
            logger.info(f"No meta file found in {self.repo_path}")

    def _load_meta(self):
        yaml_file = os.path.join(self.path, "_cm.yaml")
        json_file = os.path.join(self.path, "_cm.json")

        if os.path.exists(yaml_file):
            self.meta = utils.read_yaml(yaml_file)
        elif os.path.exists(json_file):
            self.meta = utils.read_json(json_file)
        else:
            logger.info(f"No meta file found in {self.path} for {self.meta}")


class Repo:
    def __init__(self, path, meta):
        self.path = path
        self.meta = meta

class Automation:
    action_object = None
    automation_type = None
    meta = None
    path = None

    def __init__(self, action, automation_type, automation_file):
        #logger.info(f"action = {action}")
        self.action_object = action
        self.automation_type = automation_type
        self.path = os.path.dirname(automation_file)
        self._load_meta()

    def _load_meta(self):
        yaml_file = os.path.join(self.path, "_cm.yaml")
        json_file = os.path.join(self.path, "_cm.json")

        if os.path.exists(yaml_file):
            self.meta = utils.read_yaml(yaml_file)
        elif os.path.exists(json_file):
            self.meta = utils.read_json(json_file)
        else:
            logger.info(f"No meta file found in {self.path}")

    def search(self, i):
        #logger.info(i)
        #logger.info(self)
        indices = self.action_object.index.indices
        target_index = indices.get(self.automation_type)
        result = []
        if target_index:
            tags= i.get("tags")
            tags_split = tags.split(",")
            n_tags = [p for p in tags_split if p.startswith("-")]
            p_tags = list(set(tags_split) - set(n_tags))
            for res in target_index:
                c_tags = res["tags"]
                if set(p_tags).issubset(set(c_tags)) and set(n_tags).isdisjoint(set(c_tags)):
                    it = Item(res['path'], res['repo'])
                    result.append(it)
            #logger.info(f"p_tags={p_tags}")
            #logger.info(f"n_tags={n_tags}")
            #for key in indices:
        #logger.info(result)
        return {'return': 0, 'list': result}
        #indices
        

# Child classes for specific entities (Repo, Script, Cache)
# Extends Action class
class RepoAction(Action):

    def find(self, args):
        if isinstance(args, dict):
            repo = args.get('item', args.get('artifact'))
        else:
            repo = args.details
        repo_split = repo.split(",")
        if len(repo_split) > 1:
            repo_uid = repo_split[1]
        repo_name = repo_split[0]

        lst = []
        #print(f"args = {args}")
        for i in self.repos:
            if repo_uid and i.meta['uid'] == repo_uid:
                lst.append(i)
            elif repo_name == i.meta['alias']:
                lst.append(i)
                
        return {'return': 0, 'list': lst}

    def github_url_to_user_repo_format(self, url):
        """
        Converts a GitHub repo URL to user@repo_name format.

        :param url: str, GitHub repository URL (e.g., https://github.com/user/repo_name.git)
        :return: str, formatted as user@repo_name
        """
        import re

        # Regex to match GitHub URLs
        pattern = r"(?:https?://)?(?:www\.)?github\.com/([^/]+)/([^/.]+)(?:\.git)?"

        match = re.match(pattern, url)
        if match:
            user, repo_name = match.groups()
            return f"{user}@{repo_name}"
        else:
            raise ValueError("Invalid GitHub URL format")

    def pull_repo(self, repo_url, branch=None, checkout = None):
        
        # Determine the checkout path from environment or default
        repo_base_path = self.repos_path # either the value will be from 'MLC_REPOS'
        os.makedirs(repo_base_path, exist_ok=True)  # Ensure the directory exists

        # Handle user@repo format (convert to standard GitHub URL)
        if re.match(r'^[\w-]+@[\w-]+$', repo_url):
            user, repo = repo_url.split('@')
            repo_url = f"https://github.com/{user}/{repo}.git"

        # Extract the repo name from URL
        repo_name = repo_url.split('/')[-1].replace('.git', '')
        repo_download_name = self.github_url_to_user_repo_format(repo_url)
        repo_path = os.path.join(repo_base_path, repo_download_name)

        try:
            # If the directory doesn't exist, clone it
            if not os.path.exists(repo_path):
                logger.info(f"Cloning repository {repo_url} to {repo_path}...")
                
                # Build clone command without branch if not provided
                clone_command = ['git', 'clone', repo_url, repo_path]
                if branch:
                    clone_command = ['git', 'clone', '--branch', branch, repo_url, repo_path]
                
                subprocess.run(clone_command, check=True)

            else:
                logger.info(f"Repository {repo_name} already exists at {repo_path}. Pulling latest changes...")
                subprocess.run(['git', '-C', repo_path, 'pull'], check=True)
            
            # Checkout to a specific branch or commit if --checkout is provided
            if checkout:
                logger.info(f"Checking out to {checkout} in {repo_path}...")
                subprocess.run(['git', '-C', repo_path, 'checkout', checkout], check=True)
            
            logger.info("Repository successfully pulled.")
            logger.info("Registering the repo in repos.json")

            # check the meta file to obtain uids
            meta_file_path = os.path.join(repo_path, 'meta.yaml')
            if not os.path.exists(meta_file_path):
                logger.warning(f"meta.yaml not found in {repo_path}. Repo pulled but not register in mlc repos. Skipping...")
                return
            
            with open(meta_file_path, 'r') as meta_file:
                meta_data = yaml.safe_load(meta_file)
                meta_data["path"] = repo_path

            # Check UID conflicts
            is_conflict = self.conflicting_repo(meta_data)
            if is_conflict['return'] > 0:
                if "UID not present" in is_conflict['error']:
                    logger.warning(f"UID not found in meta.yaml at {repo_path}. Repo pulled but can not register in mlc repos. Skipping...")
                    return
                elif "already registered" in is_conflict["error"]:
                    #logger.warning(is_conflict["error"])
                    logger.info("No changes made to repos.json.")
                else:
                    logger.warning(f"The repo to be cloned has conflict with the repo already in the path: {is_conflict['conflicting_path']}")
                    logger.warning(f"The repo currently being pulled will be registered in repos.json and already existing one would be unregistered.")
                    self.unregister_repo(is_conflict['conflicting_path'])
                    self.register_repo(meta_data)
            else:         
                self.register_repo(meta_data)

        except subprocess.CalledProcessError as e:
            logger.info(f"Git command failed: {e}")
        except Exception as e:
            logger.info(f"Error pulling repository: {str(e)}")

    def pull(self, args):
        repo_url = args.details if args.details else args.target_or_url
        if repo_url == "repo":
            for repo_object in self.repos:
                repo_folder_name = os.path.basename(repo_object.path)
                if "@" in repo_folder_name:
                    self.pull_repo(repo_folder_name)
        else:
            branch = None
            checkout = None
            extras = args.extra
            for item in extras:
                split = item.split("=")
                if split[0] == "--branch":
                    branch = split[1]
                elif split[0] == "--checkout":
                    checkout = split[1]

            self.pull_repo(repo_url, branch, checkout)
            
    def list(self, args):
        logger.info("Listing all repositories.")
        print("\nRepositories:")
        print("-------------")
        for repo_object in self.repos:
            print(f"- Alias: {repo_object.meta.get('alias', 'Unknown')}")
            print(f"  Path:  {repo_object.path}\n")
        print("-------------")
        logger.info("Repository listing ended")
    
    def rm(self, args):
        logger.info("rm command has been called for repo. This would delete the repo folder and unregister the repo from repos.json")
        
        if not args.details:
            logger.error("The repository to be removed is not specified")
            return

        repo_folder_name = args.details

        repo_path = os.path.join(self.repos_path, repo_folder_name)

        if os.path.exists(repo_path):
            shutil.rmtree(repo_path)
            logger.info(f"Repo {args.details} residing in path {repo_path} has been successfully removed")
            logger.info("Checking whether the repo was registered in repos.json")
        else:
            logger.warning(f"Repo {args.details} was not found in the repo folder. repos.json will be checked for any corrupted entry. If any, that will be removed.")

        self.unregister_repo(repo_path)
        

class ScriptAction(Action):
    def search(self, i):
        if not i.get('target_name'):
            i['target_name'] = "script"
        return super().search(i)

    def dynamic_import_module(self, script_path):
        # Validate the script_path
        if not os.path.exists(script_path):
            raise FileNotFoundError(f"Script file not found: {script_path}")

        # Add the parent folder of the script to sys.path
        script_dir = os.path.dirname(script_path)
        automation_dir = os.path.dirname(script_dir)  # automation folder

        if automation_dir not in sys.path:
            sys.path.insert(0, automation_dir)

        # Dynamically load the module
        module_name = os.path.splitext(os.path.basename(script_path))[0]
        spec = importlib.util.spec_from_file_location(module_name, script_path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Cannot create a module spec for: {script_path}")

        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        return module

    def update_script_run_args(self, run_args, inp):
        for key in inp:
            if "=" in key:
                split = key.split("=", 1)  # Split only on the first "="
                arg_key = split[0].strip("-")
                arg_value = split[1]

                # Handle lists: Only if "," is immediately before the "="
                if "," in arg_key:
                    list_key, list_values = arg_key.rsplit(",", 1)
                    if not list_values:  # Ensure "=" follows the last comma
                        run_args[list_key] = arg_value.split(",")
                        continue

                # Handle dictionaries: `--adr.compiler.tags=gcc` becomes `{"adr": {"compiler": {"tags": "gcc"}}}`
                elif "." in arg_key:
                    keys = arg_key.split(".")
                    current = run_args
                    for part in keys[:-1]:
                        if part not in current or not isinstance(current[part], dict):
                            current[part] = {}
                        current = current[part]
                    current[keys[-1]] = arg_value
            
                # Handle simple key-value pairs
                else:
                    run_args[arg_key] = arg_value
        
            # Handle flags: `--flag` becomes `{"flag": True}`
            elif key.startswith("-"):
                run_args[key.strip("-")] = True

    def get_script_run_args(self, args):
        run_args = {}
        if "tags" in args: # # called through access function
            tags = args["tags"]
            cmd = args
            run_args = args
        else:
            tags = ""
            for option in args.extra:
                opt = option.split("=")
                if opt[0] == "--tags":
                    tags = opt[1]
            cmd = args.extra
            
            run_args = {'action': 'run', 'automation': 'script', 'tags': tags, 'cmd': cmd, 'out': 'con',  'parsed_automation': [('script', '5b4e0237da074764')]}
            # update the run args with the extras that are supplied
            self.update_script_run_args(run_args, args.extra)
        return {'return': 0, 'run_args': run_args}


    def docker(self, args):
        self.action_type = "script"
        #logger.info(f"Running script with identifier: {args.details}")
        # The REPOS folder is set by the user, for example via an environment variable.
        repos_folder = self.repos_path
        #logger.info(f"In script action {repos_folder}")

        # Import script submodule 
        script_path = self.find_target_folder("script")
        module_path = os.path.join(script_path, "module.py")
        module = self.dynamic_import_module(module_path)

        res = self.get_script_run_args(args)
        if res['return'] > 0:
            return res
        run_args = res['run_args']

        # Check if ScriptAutomation is defined in the module
        if hasattr(module, 'ScriptAutomation'):
            automation_instance = module.ScriptAutomation(self, module_path)
            #logger.info(f" script automation initialized at {module_path}")
            #logger.info(run_args)
            #return {'return': 1}
            result = automation_instance.docker(run_args)  # Pass args to the run method
            #logger.info(result)
            if result['return'] > 0:
                error = result.get('error', "")
                raise ScriptExecutionError(f"Script docker execution failed. Error : {error}")
            #logger.info(f"Script result: {result}")
            return result
        else:
            logger.info("ScriptAutomation class not found in the script.")
    def run(self, args):
        self.action_type = "script"
        #logger.info(f"Running script with identifier: {args.details}")
        # The REPOS folder is set by the user, for example via an environment variable.
        repos_folder = self.repos_path
        #logger.info(f"In script action {repos_folder}")

        # Import script submodule 
        script_path = self.find_target_folder("script")
        module_path = os.path.join(script_path, "module.py")
        module = self.dynamic_import_module(module_path)

        res = self.get_script_run_args(args)
        if res['return'] > 0:
            return res
        run_args = res['run_args']

        # Check if ScriptAutomation is defined in the module
        if hasattr(module, 'ScriptAutomation'):
            automation_instance = module.ScriptAutomation(self, module_path)
            #logger.info(f" script automation initialized at {module_path}")
            #logger.info(run_args)
            #return {'return': 1}
            result = automation_instance.run(run_args)  # Pass args to the run method
            #logger.info(result)
            if result['return'] > 0:
                error = result.get('error', "")
                raise ScriptExecutionError(f"Script execution failed. Error : {error}")
            #logger.info(f"Script result: {result}")
            return result
        else:
            logger.info("ScriptAutomation class not found in the script.")

    def list(self, args):
        logger.info("Listing all scripts.")


class ScriptExecutionError(Exception):
    """Custom error for configuration issues."""
    pass

class CacheAction(Action):
    
    def search(self, i):
        i['target_name'] = "cache"
        logger.debug(f"Searching for cache with input: {i}")
        return super().search(i)

    def show(self, args):
        self.action_type = "cache"
        logger.info(f"Showing cache with identifier: {args.details}")

    def find(self, args):
        #logger.info(f"Running script with identifier: {args.details}")
        # The REPOS folder is set by the user, for example via an environment variable.
        #logger.info(f"In cache action {repos_folder}")


        if "tags" in args: # access function
            tags = args["tags"]
            cmd = args
            run_args = args
        else:
            tags = ""
            for option in args.extra:
                opt = option.split("=")
                if opt[0] == "--tags":
                    tags = opt[1]
            cmd = args.extra
            
            run_args = {'action': 'run', 'automation': 'cache', 'tags': tags, 'cmd': cmd, 'out': 'con',  'parsed_automation': [('cache', '541d6f712a6b464e')]}
            #self.update_script_run_args(run_args, args.extra)
        run_args['target_name'] = "cache"
        #print(f"run_args = {run_args}")
        return self.search(run_args)

    def list(self, args):
        logger.info("Listing all caches.")

class ExperimentAction(Action):
    def show(self, args):
        logger.info(f"Showing experiment with identifier: {args.details}")

    def list(self, args):
        logger.info("Listing all experiments.")


class CfgAction(Action):
    def load(self, args):
        """
        Load the configuration.
        
        Args:
            args (dict): Contains the configuration details such as file path, etc.
        """
        #logger.info("In cfg load")
        default_config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.yaml')
        config_file = args.get('config_file', default_config_path)
        logger.info(f"In cfg load, config file = {config_file}")
        if not config_file or not os.path.exists(config_file):
            logger.info(f"Error: Configuration file '{config_file}' not found.")
            return {'return': 1, 'error': f"Error: Configuration file '{config_file}' not found."}
        
        #logger.info(f"Loading configuration from {config_file}")
        
        # Example loading YAML configuration (can be modified based on your needs)
        try:
            with open(config_file, 'r') as file:
                config_data = yaml.safe_load(file)
                logger.info(f"Loaded configuration: {config_data}")
                # Store configuration in memory or perform other operations
                self.cfg = config_data
        except yaml.YAMLError as e:
            logger.info(f"Error loading YAML configuration: {e}")
        
        return {'return': 0, 'config': self.cfg}

    def unload(self, args):
        """
        Unload the configuration.
        
        Args:
            args (dict): Optional, could be used to specify a particular configuration to unload.
        """
        if hasattr(self, 'config'):
            logger.info(f"Unloading configuration.")
            del self.config  # Remove the loaded config from memory
        else:
            logger.info("Error: No configuration is currently loaded.")



actions = {
        'repo': RepoAction,
        'script': ScriptAction,
        'cache': CacheAction,
        'cfg': CfgAction,
        'experiment': ExperimentAction
    }

# Factory to get the appropriate action class
def get_action(target):
    action_class = actions.get(target, None)
    return action_class() if action_class else None


def access(i):
    action = i['action']
    automation = i['automation']
    action_class = get_action(automation)
    r = action_class.access(i)
    return r

# Main CLI function
def main():
    parser = argparse.ArgumentParser(prog='mlc', description='A CLI tool for managing repos, scripts, and caches.')

    # Subparsers are added to main parser, allowing for different commands (subcommands) to be defined. 
    # The chosen subcommand will be stored in the "command" attribute of the parsed arguments.
    subparsers = parser.add_subparsers(dest='command', required=True)

    # Pull parser - handles repo URLs directly
    # The chosen subcommand will be stored in the "pull" attribute of the parsed arguments.
    pull_parser = subparsers.add_parser('pull', help='Pull a repository by URL or target.')
    pull_parser.add_argument('target_or_url', help='Target (repo) or URL for the repository.')

    pull_parser.add_argument('details', nargs='?', help='Optional details or identifier.')
    pull_parser.add_argument('extra', nargs=argparse.REMAINDER, help='Extra options (e.g.,  -v)')

    # Script and Cache-specific subcommands
    for action in ['run', 'show', 'update', 'list', 'find', 'search', 'rm']:
        action_parser = subparsers.add_parser(action, help=f'{action.capitalize()} a target.')
        action_parser.add_argument('target', choices=['repo', 'script', 'cache'], help='Target type (repo, script, cache).')
        # the argument given after target and before any extra options like --tags will be stored in "details"
        action_parser.add_argument('details', nargs='?', help='Details or identifier (optional for list).')
        action_parser.add_argument('extra', nargs=argparse.REMAINDER, help='Extra options (e.g.,  -v)')

    # Script and specific subcommands
    for action in ['docker', 'help']:
        action_parser = subparsers.add_parser(action, help=f'{action.capitalize()} a target.')
        action_parser.add_argument('target', choices=['script'], help='Target type (script).')
        # the argument given after target and before any extra options like --tags will be stored in "details"
        action_parser.add_argument('details', nargs='?', help='Details or identifier (optional for list).')
        action_parser.add_argument('extra', nargs=argparse.REMAINDER, help='Extra options (e.g.,  -v)')

    for action in ['load']:
        load_parser = subparsers.add_parser(action, help=f'{action.capitalize()} a target.')
        load_parser.add_argument('target', choices=['cfg'], help='Target type (cfg).')
    
    
    # Parse arguments
    args = parser.parse_args()

    logger.info(f"Args = {args}")


    # Parse extra options into a dictionary
    options = {}
    for opt in args.extra:
        if opt.startswith('--'):
            # Handle --key=value (long form)
            if '=' in opt:
                key, value = opt.lstrip('--').split('=')
                options[key] = value
            else:
                options[opt.lstrip('--')] = True  # --key (flag without value)
        elif opt.startswith('-'):
            # Handle short options (-j or -xyz)
            for char in opt.lstrip('-'):
                options[char] = True
        else:
            logger.info(f"Warning: Unrecognized option '{opt}' ignored.")

    if args.command == 'pull':
        # If the first argument looks like a URL, assume repo pull
        if args.target_or_url.startswith("http"):
            action = RepoAction()
            action.pull(args)
        else:
            action = get_action(args.target_or_url)
            if action and hasattr(action, 'pull'):
                action.pull(args)
            else:
                logger.info(f"Error: '{args.target_or_url}' is not a valid target for pull.")
    else:
        # Get the action handler for other commands
        action = get_action(args.target)
        # Dynamically call the method (e.g., run, list, show)
        if action and hasattr(action, args.command):
            method = getattr(action, args.command)
            method(args)
        else:
            logger.info(f"Error: '{args.command}' is not supported for {args.target}.")

if __name__ == '__main__':
    main()

__version__ = "0.0.1"
