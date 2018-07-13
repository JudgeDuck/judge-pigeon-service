#encoding=utf-8
"""server URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.8/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Add an import:  from blog import urls as blog_urls
    2. Add a URL to urlpatterns:  url(r'^blog/', include(blog_urls))
"""
from django.conf.urls import include, url
from django.contrib import admin
from django.http import HttpResponse, HttpResponseRedirect
from django.template import loader, Context
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render_to_response
from threading import *
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect
from django.contrib.staticfiles import views as static_views
from django.views.static import serve as static_view_serve
from django.http import Http404
import html
import os
import subprocess
import threading
import time
import datetime
import markdown2
import json
import re
import hashlib
import urllib

from . import jd_utils as utils
from . import jp_database as db
from . import jp_compilation

jp_compilation.start()

def json_response(req, info):
	return HttpResponse(json.dumps(info), content_type="application/json")

def reload_view(req):
	db.reload()
	return HttpResponseRedirect("/")

def index_view(req):
	res = HttpResponse(content_type="text/plain")
	res.write("Welcome to judge pigeon! Gu gu gu !!!")
	return res

def do_query_file(req):
	md5 = req.POST.get("md5", "")
	return json_response(req, db.do_query_file(md5))

def do_send_file(req):
	md5 = req.POST.get("md5", "")
	content = req.POST.get("content", "")
	return json_response(req, db.do_send_file(md5, content))

def do_submit_task(req):
	taskid = req.POST.get("taskid", "")
	contestant_md5 = req.POST.get("contestant_md5", "")
	problem_md5 = req.POST.get("problem_md5", "")
	priority = utils.parse_int(req.POST.get("priority", ""), -1)
	return json_response(req, db.do_submit_task(taskid, contestant_md5, problem_md5, priority))

def do_get_task_results(req):
	taskids = req.POST.get("taskids", "").split("|")
	return json_response(req, db.do_get_task_results(taskids))


def entry(req):
	path = req.path
	
	if path == "/api/query_file":
		return do_query_file(req)
	if path == "/api/send_file":
		return do_send_file(req)
	if path == "/api/submit_task":
		return do_submit_task(req)
	if path == "/api/get_task_results":
		return do_get_task_results(req)
	
	if path == "/":
		return index_view(req)
	
	if path == "/reload":
		return reload_view(req)
	
	raise Http404()
#

