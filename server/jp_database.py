#encoding=utf-8

from . import jd_utils as utils

path_prefix = "jp_data/"
path_temp = path_prefix + "temp/"
path_files = path_prefix + "files/"

import threading
lock = threading.Lock()


# Map md5 to ???
all_files = None



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






def init():
	lock.acquire()
	init_files()
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






init()
