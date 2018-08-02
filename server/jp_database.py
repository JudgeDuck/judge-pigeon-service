#encoding=utf-8

from . import jd_utils as utils

path_prefix = "jp_data/"
path_temp = path_prefix + "temp/"
path_files = path_prefix + "files/"
path_tasks = path_prefix + "tasks/"
path_problems = path_prefix + "problems/"

import threading
lock = threading.Lock()

import base64


# Map md5 to ???
all_files = None

# Map taskid to ???
all_tasks = None



def do_query_file(md5):
	ret = {"status": "failed"}
	lock.acquire()
	tmp = all_files.get(md5, None)
	if tmp != None:
		ret["status"] = "success"
	else:
		ret["error"] = "File not found"
	lock.release()
	return ret

def do_send_file(md5, content):
	ret = {"status": "failed"}
	content = base64.b64decode(content.encode("utf-8"))
	md5sum = utils.md5sum_b(content)
	if md5 != md5sum:
		ret["error"] = "MD5 mismatch"
		return ret
	lock.acquire()
	utils.write_file_b(path_files + md5, content)
	all_files[md5] = 1
	lock.release()
	ret["status"] = "success"
	return ret

def do_submit_task(taskid, contestant_md5, problem_md5, priority):
	ret = {"status": "failed"}
	if taskid == "":
		ret["error"] = "Invalid taskid"
		return ret
	lock.acquire()
	global all_tasks
	if all_tasks.get(taskid, None) != None:
		ret["error"] = "The task already exists"
		lock.release()
		return ret
	task = {
		"taskid": taskid,
		"issue_time": utils.get_current_time(),
		"contestant_md5": contestant_md5,
		"problem_md5": problem_md5,
		"priority": priority,  # int
		"compilation_result": "N/A",  # success or failed
		"details": [],  # keep sorted
		"status": "Pending",
		"status_short": "PD",
		"has_completed": "false",
		"max_time_ns": 0,
		"max_mem_kb": 0,
		"score": 0,
		"todos": [],
		"runnings": [],
	}
	all_tasks[taskid] = task
	lock.release()
	ret["status"] = "success"
	return ret

def do_get_task_results(taskids):
	ret = []
	lock.acquire()
	for taskid in taskids:
		tmp = {"status": "failed"}
		global all_tasks
		task = all_tasks.get(taskid, None)
		if task == None:
			tmp["error"] = "No such task"
			ret.append(tmp)
			continue
		tmp["status"] = "success"
		tmp["taskid"] = taskid
		tmp["result"] = {
			"status": task["status"],
			"status_short": task["status_short"],
			"max_time_ns": task["max_time_ns"],
			"max_mem_kb": task["max_mem_kb"],
			"score": task["score"],
			"details": task["details"],
			"has_completed": task["has_completed"],
		}
		ret.append(tmp)
	lock.release()
	return ret

#

def do_get_pending_compile_task():
	lock.acquire()
	global all_tasks
	global all_files
	ret = None
	for taskid in all_tasks:
		task = all_tasks[taskid]
		if task["compilation_result"] != "N/A":
			continue
		if all_files.get(task["contestant_md5"], None) == None:
			continue
		#if all_files.get(task["problem_md5"], None) == None:
		#	continue
		if (ret == None) or compare_tasks(task, ret):
			ret = task
	lock.release()
	return ret

def do_get_todo_task():
	lock.acquire()
	global all_tasks
	ret = None
	for taskid in all_tasks:
		task = all_tasks[taskid]
		if len(task["todos"]) == 0:
			continue
		if task["compilation_result"] != "success":
			continue
		if (ret == None) or compare_tasks(task, ret):
			ret = task
	lock.release()
	return ret

def do_get_todo_task_with_duck_id(id, n_ducks):
	lock.acquire()
	global all_tasks
	ret = None
	for taskid in all_tasks:
		task = all_tasks[taskid]
		if len(task["todos"]) == 0:
			continue
		if task["compilation_result"] != "success":
			continue
		ok = False
		for todo in task["todos"]:
			if todo["preferred_duck_id"] % n_ducks == id:
				ok = True
				break
		if not ok:
			continue
		if (ret == None) or compare_tasks(task, ret):
			ret = task
	lock.release()
	return ret

#

def compare_tasks(task1, task2):
	if task1["priority"] != task2["priority"]:
		return task1["priority"] > task2["priority"]
	return task1["issue_time"] < task2["issue_time"]




def init():
	lock.acquire()
	init_files()
	init_tasks()
	lock.release()

def reload():
	init()

def init_files():
	global all_files
	all_files = {}
	li = utils.list_dir(path_files)
	for md5 in li:
		content = utils.read_file_b(path_files + md5)
		if utils.md5sum_b(content) != md5:
			utils.remove_file(path_files + md5)
			print("[jp] Removed corrupted file '%s'" % md5)
			pass
		all_files[md5] = 1

def init_tasks():
	global all_tasks
	all_tasks = {}
	utils.system("rm", ["-rf", path_tasks + "*"], 100)






init()
