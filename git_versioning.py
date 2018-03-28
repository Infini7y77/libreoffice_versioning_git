# coding: utf-8
# Module: git_versioning.py
#-=-=-=-=-=-=-=--=-=-=-=-=-=-=-
# by harland.coles on 20180326
#-=-=-=-=-=-=-=--=-=-=-=-=-=-=-
__version__ = '20180328.0045'
"""
LibreOffice Python Marco:
- Stores versions of current doc into a git repo using a similarily-named subdirectory

Notes
===========
LibroOffice Filters:
https://cgit.freedesktop.org/libreoffice/core/tree/filter/source/config/fragments/filters

Requires:
===========
- script needs to reside in, either:
	- ${HOME}/.config/libreoffice/4-suse/user/Scripts/python/, or
	- /usr/lib64/libreoffice/share/Scripts/python/

- LibreOffice Uno Python addons
- pygit2 -- requires compatible libgit2 library, eg libgit-26 for pygit2-26
	$> zypper in libgit2 libgit2-devel
	$> pip install pygit2==0.26.*
"""
#-=-=-=-=-=-=-=--=-=-=-=-=-=-=-
#import random

import sys
import os
import datetime as dt
from urllib.parse import (quote as url_quote, unquote as url_unquote)

from com.sun.star.beans import PropertyValue

#import git  # GitPython: https://github.com/gitpython-developers/GitPython
#or
import pygit2 as git  # http://www.pygit2.org/, https://github.com/libgit2/pygit2,

#--<>--<>--<>--<>--<>--<>--<>--


#--------------------------------------------------
def get_lo_model():
	desktop = XSCRIPTCONTEXT.getDesktop()
	model = desktop.getCurrentComponent()
	return model

def _url_to_path_file(url):
	return os.path.split(url_unquote(url.replace('file://','')))

def _url_ify(path,fn):
	return "file://{}".format(url_quote(os.path.join(path,fn)))

#--------------------------------------------------

def _repo_path(vpath):
	return os.path.join(vpath,'.git/')

def _get_repo(vpath):
	return git.Repository(_repo_path(vpath))

def check_git_repo(vpath):
	""" """
	# use python git interface to check for valid repo in path dir
	if os.access(_repo_path(vpath), os.R_OK):
		try:
			repo = git.Repository(_repo_path(vpath))
		except GitError as e:
			if e.message.startswith('Repository not found'):
				return False
			else:
				raise
		return True
	return False

def git_repo_init(vpath):
	""" """
	# if path exists and git repo dNE, then .. else ?? return False? (or raise error?)
	if check_git_repo(vpath) == False:
		# git init
		repo = git.init_repository(vpath, bare=False)

		# create .gitignore
		fn = os.path.join(vpath,'.gitignore')
		ts = "#.gitignore\n~*\n.~lock.*\n*.kate-swp\n"
		with open(fn,'w') as fp:
			fp.write(ts)

		# optionally? create local .gitconfig?
		fn = os.path.join(vpath,'.gitconfig')
		ts = "#.gitconfig\n"
		with open(fn,'w') as fp:
			fp.write(ts)

		repo.config.add_file(fn)

		_, fn = os.path.split(vpath)
		# git add .
		# git commit -m 'Initial Commit ;)'
		oid = _git_commit_with_add(repo,'Initial Commit ;) in {}'.format(fn), init=True)

		return repo
	return False

def _git_commit(repo, msg, init=False):
	#repo = git.Repository(_repo_path(vpath))

	if repo.status():
		user_name = repo.config['user.name']
		user_email = repo.config['user.email']
		author = git.Signature(user_name, user_email)
		commiter = git.Signature('LibreOffice - Save Versions to Git: {}'.format(__version__), 'infini7y@yellow')

		tree = repo.index.write_tree()

		if init:
			author = commiter
			ref = 'HEAD'
			parents = []
		else:
			commiter = author
			ref = repo.head.name
			parents = [repo.head.get_object().hex]

		oid = repo.create_commit(ref, author, commiter, msg, tree, parents)
		return oid
	return None

def _git_commit_with_add(repo, msg, init=False):
	#repo = git.Repository(_repo_path(vpath))
	repo.index.add_all()
	repo.index.write()

	return _git_commit(repo, msg, init)

#--------------------------------------------------

def get_versioning_dir_name(model, suffix='versions'):
	""" """
	# Filename used for versioning subdirectory name
	path, fn = _url_to_path_file(model.getURL())
	for wo,wi in ((' ','_'),('.odt',''),('.fodt',''),('.ods',''),('.fods','')):
		fn = fn.replace(wo,wi)
	if path and fn:
		return os.path.join(path,'{}__{}'.format(fn,suffix))
	return None

def setup_version_dir(vpath):
	""" """
	if not vpath: return False

	# Check existence first
	if check_git_repo(vpath): return True

	# if path dNE, then mkdir
	if not os.access(vpath, os.F_OK): os.mkdir(vpath)

	# if repo dNE, then Init
	git_repo_init(vpath)

	if os.access(vpath, os.R_OK) and check_git_repo(vpath): 	return True

	return False

#--------------------------------------------------

FILTERS = { 'fodt' : 'OpenDocument Text Flat XML',  #writer_ODT_FlatXML
			'fods' : 'OpenDocument Spreadsheet Flat XML',   #calc_ODS_FlatXML
			'txt' : 'Text',
			'csv' : 'Text - txt - csv (StarCalc)',
			}

def create_property(pname, pvalue):
	p = PropertyValue()
	p.Name, p.Value = pname, pvalue
	return p

def get_filter_as_property(filtertype):
	return create_property('FilterName', FILTERS[filtertype])

def store_to_URL(model, url, filtertype, overwrite=True, extra_properties=None):
	""" """
	props = [get_filter_as_property(filtertype), create_property('Overwrite', overwrite)]
	if extra_properties is not None and isinstance(extra_properties,(list,tuple)):
		for p in extra_properties:
			if isinstance(p, PropertyValue):
				props.append(p)
	return model.storeToURL(url, tuple(props))

def store_to_flat_XML(model, vpath):
	_, fn = _url_to_path_file(model.getURL())
	#TODO: check type using model
	fn = fn.replace('.odt','.fodt')
	return store_to_URL(model, _url_ify(vpath,fn), 'fodt')

def store_to_text(model, vpath):
	_, fn = _url_to_path_file(model.getURL())
	#TODO: check type using model
	if fn.find('.odt') > 0 or fn.find('.fodt') > 0:
		fn = fn.replace('.odt','.txt')
		fn = fn.replace('.fodt','.txt')
		return store_to_URL(model, _url_ify(vpath,fn), 'txt')
	return False

def store_to_csv(model, vpath):
	_, fn = _url_to_path_file(model.getURL())
	#TODO: check type using model
	if fn.find('.ods') > 0 or fn.find('.fods') > 0:
		fn = fn.replace('.ods','.csv')
		fn = fn.replace('.fods','.csv')
		return store_to_URL(model, _url_ify(vpath,fn), 'csv')
	return False

#--------------------------------------------------

def save_and_commit_version_git(model, vpath, msg=''):
	""" """
	if not setup_version_dir(vpath): return False

	# save a copy of LO file into path as flat XML
	store_to_flat_XML(model,vpath)

	# save a copy of LO file into path: as text file for ODT, as csv for ODS
	store_to_text(model,vpath)

	# git commit -am <msg>
	repo = _get_repo(vpath)
	_git_commit_with_add(repo, msg)

	return True

#--------------------------------------------------
# LibreOffice Entry Functions

def save_version_git(*args):
	""" """
	model = get_lo_model()
	#print_to_textdoc(dir(model))

	vpath = get_versioning_dir_name(model)
	#print_to_textdoc(vpath)

	# TODO: may get commit msg from prompt
	today = dt.datetime.today().strftime("%Y-%m-%d.%H%M")
	msg = '{} - New Version Added'.format(today)

	save_and_commit_version_git(model, vpath, msg)

def save_version_git_branch(*args):
	""" """
	# Prompt for branch name
	# check if branch exists, then create or goto
	#git branch <branch>, or git checkout <branch>
	# then save_version_git()
	pass

def save_version_git_master(*args):
	""" """
	#git checkout master
	pass


# lists the scripts, that shall be visible inside OOo.
# Can be omitted, if all functions shall be visible
g_exportedScripts = save_version_git,


#--------------------------------------------------

def print_to_textdoc(msg='x-x-x'):
    model = get_lo_model()

	#check whether there's already an opened document. Otherwise, create a new one
    if not hasattr(model, "Text"):
        model = desktop.loadComponentFromURL(
            "private:factory/swriter","_blank", 0, () )

	#get the XText interface
    text = model.Text
	#create an XTextRange at the end of the document
    tRange = text.End
	#and set the string
    tRange.String = "\n%s\n" % (msg)

    return None


#--#--#--#--#--#--#--#--#--#--#--
# Testing:  Use unittest





#eof