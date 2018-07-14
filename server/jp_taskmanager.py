#encoding=utf-8

import time
import os
import subprocess
import threading
import re

from . import jd_utils as utils
from . import jp_database as db
from . import jp_duck as dk

def init_ducks():
	ducks = []
	config_content = utils.read_file("ducks-config.txt").split("\n")
	duck_cnt = 0
	for s in config_content:
		s = s.split(" ")
		if len(s) != 2:
			continue
		duck_cnt += 1
		ducks.append(dk.start_duck("Duck #%d" % duck_cnt, s[0], s[1]))
	return ducks

def update_task_result(task, result):
	job_name = result["name"]
	todo = None
	todo_idx = -1
	for i in range(len(task["runnings"])):
		x = task["runnings"][i]
		if x["name"] == job_name:
			todo = x
			todo_idx = i
			break
	task["runnings"] = task["runnings"][:todo_idx] + task["runnings"][todo_idx+1:]
	todo["try_cnt"] += 1
	if result["status"] == "Judge Failed":
		if todo["try_cnt"] < 3:
			task["todos"].append(todo)
			return
	
	uoj_stid = todo.get("uoj_subtask_id", 0)
	if uoj_stid != 0:
		if not "uoj_st_status" in task: task["uoj_st_status"] = {}
		uoj_st_status = task["uoj_st_status"]
		if not uoj_stid in uoj_st_status:
			uoj_st_status[uoj_stid] = result["status"]
		elif uoj_st_status[uoj_stid] == "Accepted":
			uoj_st_status[uoj_stid] = result["status"]
			result["score"] -= todo["max_score"]
		else:
			result["score"] = 0
	
	task["score"] += result["score"]
	if result["time_ns"] != None:
		task["max_time_ns"] = max(task["max_time_ns"], result["time_ns"])
	if result["mem_kb"] != None:
		task["max_mem_kb"] = max(task["max_mem_kb"], result["mem_kb"])
	result["time_ns"] = utils.render_time_ns(result["time_ns"])
	result["mem_kb"] = utils.render_memory_kb(result["mem_kb"])
	insert_idx = -1
	for idx in range(len(task["details"])):
		if task["details"][idx]["detail_index"] > todo["detail_index"]:
			insert_idx = idx
			break
	result["detail_index"] = todo["detail_index"]
	if insert_idx == -1:
		task["details"].append(result)
	else:
		task["details"] = task["details"][:idx] + [result] + task["details"][idx:]
	if len(task["todos"]) + len(task["runnings"]) == 0:
		status_string = "Accepted"
		for detail in task["details"][1:]:
			tmp = detail["status"]
			if tmp != "Accepted":
				status_string = tmp
				break
		task["status"] = status_string
		task["status_short"] = ""
		task["has_completed"] = "true"

def jp_taskmanager_thread_func():
	ducks = init_ducks()
	while True:
		time.sleep(0.2)
		while True:
			for duck in ducks:
				if duck.has_result:
					update_task_result(duck.task, duck.result)
					duck.has_result = False
			free_duck = None
			for duck in ducks:
				if not duck.has_task:
					free_duck = duck
					break
			if free_duck == None:
				break
			task = db.do_get_todo_task()
			if task == None:
				break
			todo = task["todos"][0]
			task["todos"] = task["todos"][1:]
			task["runnings"].append(todo)
			task["status"] = "Running %s of %s" % (
				len(task["details"]) - 1,
				len(task["details"]) + len(task["todos"]) + len(task["runnings"]) - 1
			)
			task["status_short"] = "RUN"
			print("Start task %s : %s on %s" % (task["taskid"], todo["name"], free_duck.name))
			free_duck.task = task
			free_duck.args = {
				"name": todo["name"],
				"input_file": todo["input_file"],
				"answer_file": todo["answer_file"],
				"binary_file": todo["binary_file"],
				"time_ns": todo["time_limit_ns"],
				"mem_kb": todo["memory_limit_kb"],
				"max_score": todo["max_score"],
			}
			free_duck.has_task = True



class myThread(threading.Thread):
	def __init__(self, name, func):
		threading.Thread.__init__(self)
		self.name = name
		self.func = func
	def run(self):
		self.func()

def start():
	mythread = myThread("jp_taskmanager", jp_taskmanager_thread_func)
	mythread.start()
