import os
import requests
import http.client as http_client
import logging
import json

from syncall.cattr.cattr_task import CattrTask
from syncall.sync_side import SyncSide
from typing import Optional, Sequence
from xdg import xdg_config_home
from pathlib import Path

http_client.HTTPConnection.debuglevel = 1

# You must initialize logging, otherwise you'll not see debug output.
logging.basicConfig()
logging.getLogger().setLevel(logging.DEBUG)
requests_log = logging.getLogger("requests.packages.urllib3")
requests_log.setLevel(logging.DEBUG)
requests_log.propagate = True
cattr_config_file=Path().joinpath(xdg_config_home(),'syncall','cattr.json')
if cattr_config_file.exists():
    with open(cattr_config_file,'r') as f:
        self.cattr_config=json.load(f)

class CattrSide(SyncSide):
    def __init__(self):
        self.headers={"Authorization":os.getenv("CATTR_TOKEN","Bearer Foo")}
        self.api=os.getenv("CATTR_URL")
        self.tasks={}
        self.users={}
        self.projects={}
        self.dirty=[]
        super().__init__(name="Cattr", fullname="Cattr")
    def start(self):
        """Initialization steps.

        Call this manually. Derived classes can take care of setting up data
        structures / connection, authentication requests etc.
        """
        self.get_all_users()
        self.get_all_projects()

    def finish(self):
        """Finalization steps.

        Call this manually. Derived classes can take care of closing open connections, flashing
        their cached data, etc.
        """
    def get_all_projects(self):
        t=requests.post(self.api+"projects/list",headers=self.headers)
        prj=t.json()["data"]
        for u in prj:
            self.projects[u['name']]={"id":u['id']}
    def get_project(self,name):
        return self.projects[name]
    def get_project_id(self,name):
        if name in self.projects:
            return self.projects[name]['id']
        else:
            assert 0,f"Project {name} not on server {self.projects}"
            return 1

    def get_all_users(self):
        t=requests.post(self.api+"users/list",headers=self.headers)
        users=t.json()["data"]
        for u in users:
            self.users[u['full_name']]={"id":u['id'],"email":u["email"]}
    def get_user(self,name):
        return self.users[name]



    def get_all_items(self, **kargs) -> Sequence[CattrTask]:
        t=requests.post(self.api+"tasks/list",headers=self.headers)
        tasks=t.json()["data"]
        results=[]
        for t in tasks:
            self.tasks[t["id"]]=t
            results.append(CattrTask.from_json(t))
        """Query side and return a sequence of items

        :param kargs: Extra options for the call
        :return: A list of items. The type of these items depends on the derived class
        """
        return results

    def get_item(self, item_id: str, use_cached: bool = False) -> Optional[CattrTask]:
        """Get a single item based on the given UUID.

        :use_cached: False if you want to fetch the latest version of the item. True if a
                     cached version would do.
        :returns: None if not found, the item in dict representation otherwise
        """
        if use_cached:
            return CattrTask.from_json(self.tasks[item_id])

        self.get_all_items()
        return CattrTask.from_json(self.tasks[int(item_id)])

    def delete_single_item(self, item_id: str):
        """Delete an item based on the given UUID.

        .. raises:: Keyerror if item is not found.
        """
        requests.post(self.api+"tasks/remove",headers=self.headers,payload={"id":item_id})
        del self.tasks[item_id]


    def update_item(self, item_id: str, **changes):
        """Update with the given item.

        :param item_id : ID of item to update
        :param changes: Keyword only parameters that are to change in the item
        .. warning:: The item must already be present
        """
        edit_task=None
        requests_log.info(changes)
        for id,task in self.tasks.items():
            if task["id"] == item_id:
                for k,v in changes:
                    task[k]= v
                self.dirty.append(task["id"])
                edit_task=task
                break

        if edit_task is not None:
            requests.post(self.api+"tasks/edit",headers=self.headers,params={
            "id":item_id,
            "project_id":get_project_id(edit_task.get("project_name"," ")),
            "active":task["status_id"]!=2,
            "priority_id":1,
            })

    def get_mapped_users(self,task):
        users=[]
        if 'tags' in task:
            for name,u in self.users.items():
                if name in task['tags']:
                    users.append(u['id'])
        return users
    def add_item(self, item: CattrTask) -> CattrTask:
        """Add a new item".

        :returns: The newly added event
        """
        r=requests.post(self.api+"tasks/create",headers=self.headers,params={
            "start_date":item.start_date,
            "due_date":item.due_date,
            #'users':[1,2],
            "project_id":self.get_project_id(item.project_name),
            "task_name":item.task_name,
            "description":"todo",
            "important":1,
            "priority_id":1,
            "status_id":1,
            })
        return CattrTask.from_json(r.json()["data"])

    @classmethod
    def id_key(cls) -> str:
        """Key in the dictionary of the added/updated/deleted item that refers to the ID of
        that Item.
        """
        return "id"

    @classmethod
    def summary_key(cls) -> str:
        """Key in the dictionary of the item that refers to its summary."""
        return "task_name"

    @classmethod
    def last_modification_key(cls) -> str:
        """Key in the dictionary of the item that refers to its modification date."""
        return "updated_at"

    @classmethod
    def items_are_identical(
        cls, item1: CattrTask, item2: CattrTask, ignore_keys: Sequence[str] = [],
    ) -> bool:
        """Determine whether two items are identical.

        .. returns:: True if items are identical, False otherwise.
        """
        compare_keys=["project_id","task_name"]
        return SyncSide._items_are_identical(item1,item2,compare_keys)
