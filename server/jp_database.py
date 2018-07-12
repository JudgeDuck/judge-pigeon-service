#encoding=utf-8

from . import jd_utils as utils

path_prefix = "jp_data/"
path_temp = path_prefix + "temp/"
path_files = path_prefix + "files/"

import threading
lock = threading.Lock()


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
	md5sum = utils.md5sum(content)
	if md5 != md5sum:
		ret["error"] = "MD5 mismatch"
		return ret
	lock.acquire()
	utils.write_file(path_files + md5, content)
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
	task = {
		"taskid": taskid,
		"contestant_md5": contestant_md5,
		"problem_md5": problem_md5,
		"priority": priority,
		"compilation_result": "N/A",  # success or failed
		"details": [],  # keep sorted
		"status": "Pending",
		"status_short": "PD",
		"max_time_ns": 0,
		"max_mem_kb": 0,
		"score": 0,
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
		}
		ret.append(tmp)
	lock.release()
	return ret








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
		content = utils.read_file(path_files + md5)
		if utils.md5sum(content) != md5:
			utils.remove_file(path_files + md5)
			print("[jp] Removed corrupted file '%s'" % md5)
			pass
		all_files[md5] = 1

def init_tasks():
	global all_tasks
	all_tasks = {}






init()
