# coding: utf-8
# Module: git_versioning.py
#-=-=-=-=-=-=-=--=-=-=-=-=-=-=-
# by harland.coles on 20180326
#-=-=-=-=-=-=-=--=-=-=-=-=-=-=-
__version__ = '20180330.0145'
"""
LibreOffice Python Marco:
- Stores versions of current doc into a git repo using a similarily-named sub-directory

Notes
===========
LibroOffice Filters:
https://cgit.freedesktop.org/libreoffice/core/tree/filter/source/config/fragments/filters

Requires:
===========
- script needs to reside in, either:
	- ${HOME}/.config/libreoffice/4-suse/user/Scripts/python/ (4-suse on openSUSE installs), or
	- /usr/lib64/libreoffice/share/Scripts/python/

- LibreOffice Uno Python addons
- pygit2 -- requires compatible libgit2 library, eg libgit-26 for pygit2-26
	$> zypper in libgit2 libgit2-devel
	$> pip install pygit2==0.26.*

TODO:
===========
- Prompt for commit message
- Setup easy branching for story edit ideas
- Get more info / properties from LO document model, like document type, created, etc

"""
#-=-=-=-=-=-=-=--=-=-=-=-=-=-=-
#import random
#import sys
import os
import datetime as dt
from urllib.parse import (quote as url_quote, unquote as url_unquote)

from com.sun.star.beans import PropertyValue

#import git  # GitPython: https://github.com/gitpython-developers/GitPython
#or
import pygit2 as git  # http://www.pygit2.org/, https://github.com/libgit2/pygit2,

#--<>--<>--<>--<>--<>--<>--<>--


#--------------------------------------------------
# LIBREOFFICE Python Script Context

if XSCRIPTCONTEXT is None:
	raise Exception("Not running in LibreOffice python script context")

def get_lo_desktop():
	"""Return the LO active document context"""
	return XSCRIPTCONTEXT.getDesktop()

def get_lo_model():
	"""Return the LO active document model"""
	desktop = get_lo_desktop()
	return desktop.getCurrentComponent()

#--------------------------------------------------
# LIBREOFFICE Functions

def _url_to_path_file(url):
	return os.path.split(url_unquote(url.replace('file://', '')))

def _url_ify(path, fn):
	return "file://{}".format(url_quote(os.path.join(path, fn)))

# Ref: https://cgit.freedesktop.org/libreoffice/core/tree/filter/source/config/fragments/filters
FILTERS = {
	'.fodt' : 'OpenDocument Text Flat XML',          #writer_ODT_FlatXML
	'.fods' : 'OpenDocument Spreadsheet Flat XML',   #calc_ODS_FlatXML
	'.fodp' : 'OpenDocument Presentation Flat XML',  #impress_ODP_FlatXML
	'.fodg' : 'OpenDocument Drawing Flat XML',       #draw_ODG_FlatXML
	'.txt' : 'Text',
	'.csv' : 'Text - txt - csv (StarCalc)',
	#'.html' : 'XHTML Writer File'  #XHTML_File
	#'.html' : 'XHTML Calc File'
	}

STORE_TO_EXTN = {
	'.fodt' : ('.fodt', '.odt', '.docx', '.doc'),
	'.fods' : ('.fods', '.ods', '.xlsx', '.xls'),
	'.fodp' : ('.fodp', '.odp', '.pptx', '.ppt'),
	'.fodg' : ('.fodg', '.odg'),
	'.txt' : ('.fodt', '.odt', '.docx', '.doc'),
	'.csv' : ('.fods', '.ods', '.xlsx', '.xls'),
	#'.html' : ('.fodt', '.odt', '.docx', '.doc'),
	#'.html' : ('.fods', '.ods', '.xlsx', '.xls', '.fodp', '.odp', '.pptx', '.ppt', '.fodg', '.odg'),
	}


def create_property(pname, pvalue):
	p = PropertyValue()
	p.Name, p.Value = pname, pvalue
	return p

def get_filter_as_property(filtertype):
	return create_property('FilterName', FILTERS[filtertype])

def store_to_URL(model, url, filtertype, overwrite=True, extra_properties=None):
	"""Stores current LO document to vpath, resulting file depends on filtertype"""
	props = [get_filter_as_property(filtertype), create_property('Overwrite', overwrite)]
	if extra_properties is not None:
		props.extend([ p for p in extra_properties if isinstance(p, PropertyValue) ])
	return model.storeToURL(url, tuple(props))

def store_to__by_extn(model, vpath, extn, fn_suffix=''):
	"""Stores current LO document to vpath based on extension"""
	_, fn = _url_to_path_file(model.getURL())
	#TODO: check type using model?
	_fn, extn_found = _find_replace(fn, STORE_TO_EXTN[extn], extn)
	if fn_suffix:
		_fn = _fn.replace(extn, '_{}{}'.format(fn_suffix, extn))
	if extn_found:
		return store_to_URL(model, _url_ify(vpath, _fn), extn)
	return False

def store_to_flat_XML(model, vpath):
	"""Store current LO document to vpath, as a ODF flat XML file"""
	return store_to__by_extn(model, vpath, '.fodt') or \
		store_to__by_extn(model, vpath, '.fods') or False

def store_to_text(model, vpath):
	"""Store current LO document to vpath, as a text document"""
	if hasattr(model, "Text"):
		return store_to__by_extn(model, vpath, '.txt')
	return False

def store_to_csv(model, vpath):
	"""Store current LO document to vpath, as a csv file"""
	# TODO: Only does current sheet, how to do it for all sheets?
	#   append sheet number or name to <filename>
	#   get sheet info from model, how?
	return store_to__by_extn(model, vpath, '.csv')

def create_new_lo_writer_document():
	"""Returns LO document model of new writer document"""
	desktop = desktop = get_lo_desktop()
	return desktop.loadComponentFromURL("private:factory/swriter", "_blank", 0, ())

#TODO: Untested
def create_new_lo_calc_document():
	"""Returns LO document model of new calc document"""
	desktop = desktop = get_lo_desktop()
	return desktop.loadComponentFromURL("private:factory/scalc", "_blank", 0, ())

#--------------------------------------------------
# GIT Functions

def _repo_path(vpath):
	return os.path.join(vpath, '.git/')

def _get_repo(vpath):
	return git.Repository(_repo_path(vpath))

def check_git_repo(vpath):
	"""Check for a valid Git Repository exists or not in Versioning directory"""
	# use python git interface to check for valid repo in path dir
	if os.access(_repo_path(vpath), os.R_OK):
		try:
			repo = git.Repository(_repo_path(vpath))
			repo.status()
		except git.GitError as e:
			if e.message.startswith('Repository not found'):
				return False
			raise
		return True
	return False

def git_repo_init(vpath):
	"""Initialize a Git Repository in the Versioning directory"""
	# if path exists and git repo dNE, then .. else ?? return False? (or raise error?)
	if not check_git_repo(vpath):
		# git init
		repo = git.init_repository(vpath, bare=False)

		# create .gitignore
		fn = os.path.join(vpath, '.gitignore')
		ts = "#.gitignore\n~*\n.~lock.*\n*.kate-swp\n"
		with open(fn, 'w') as fp:
			fp.write(ts)

		# optionally? create local .gitconfig?
		fn = os.path.join(vpath, '.gitconfig')
		ts = "#.gitconfig\n"
		with open(fn, 'w') as fp:
			fp.write(ts)

		repo.config.add_file(fn)

		_, fn = os.path.split(vpath)
		# git add .
		# git commit -m 'Initial Commit ;)'
		oid = _git_commit_with_add(repo, 'Initial Commit ;) in {}'.format(fn), init=True)

		return repo
	return False

def _git_commit(repo, msg, init=False):
	#repo = git.Repository(_repo_path(vpath))

	if repo.status():
		user_name = repo.config['user.name']
		user_email = repo.config['user.email']
		author = git.Signature(user_name, user_email)
		commiter = git.Signature('LibreOffice - Save Versions to Git(v{})'.format(__version__),
						   'infini7y@yellow')

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

def _find_replace(sobj, find_items, replacement):
	# Note: Order of items matter
	flag_found = False
	for wo in find_items:
		if sobj.find(wo) > 0:
			sobj = sobj.replace(wo, replacement)
			flag_found = True
	return sobj, flag_found

def _find_replace_pairs(sobj, find_replace_pairs):
	# Note: Order of items matter
	flag_found = False
	for wo, wi in find_replace_pairs:
		if sobj.find(wo) > 0:
			sobj = sobj.replace(wo, wi)
			flag_found = True
	return sobj, flag_found

def get_versioning_dir_name(model, suffix='versions'):
	"""Versioning Directory Name
	Directory name based off of current LO document.
	"""
	# Filename used for versioning sub-directory name
	path, fn = _url_to_path_file(model.getURL())
	_fn = fn.replace(' ', '_')

	replace_what = ('.fodt', '.odt', '.fods', '.ods',
					  '.docx', '.doc', '.xlsx', '.xls',)
	_fn, _ = _find_replace(_fn, replace_what, '')

	if path and _fn:
		return os.path.join(path, '{}__{}'.format(_fn, suffix))
	return None

def setup_version_dir(vpath):
	"""Setup Versioning Directory
	Checks first for existence, and initiates creation if not found.
	"""
	if not vpath: return False

	# Check existence first
	if check_git_repo(vpath): return True

	# if path dNE, then mkdir
	if not os.access(vpath, os.F_OK):
		os.mkdir(vpath)

	# if repo dNE, then Init
	git_repo_init(vpath)

	if os.access(vpath, os.R_OK) and check_git_repo(vpath):
		return True

	return False

def save_and_commit_version_git(model, vpath, msg=''):
	"""Store LO document to ODF Flat XML, and text or csv.
	Creates versioning directory and git initial repository if none exists
	"""
	if not setup_version_dir(vpath): return False

	# save a copy of LO file into path as flat XML
	store_to_flat_XML(model, vpath)

	# save a copy of LO file into path: as text file for ODT, as csv for ODS
	store_to_text(model, vpath)
	store_to_csv(model, vpath)

	# git commit -am <msg>
	repo = _get_repo(vpath)
	_git_commit_with_add(repo, msg)

	return True

#--------------------------------------------------
# LibreOffice Entry Functions

def save_version_git(*args):
	"""LibreOffice Macro Entry Point:
	Save a copy of current LO document to a git working directory and commit changes.
	Initiates git repository if none existing in working directory.
	Working directory is a sub-directory in directory of current LO document.
	"""
	model = get_lo_model()
	#print_to_textdoc(dir(model))

	vpath = get_versioning_dir_name(model)
	#print_to_textdoc(vpath)

	# TODO: may get commit msg from prompt
	today = dt.datetime.today().strftime("%Y-%m-%d.%H%M")
	msg = '{} - New Version Added'.format(today)

	save_and_commit_version_git(model, vpath, msg)

def save_version_git_branch(*args):
	"""LibreOffice Macro Entry Point: """
	# Prompt for branch name
	# check if branch exists, then create or goto
	#git branch <branch>, or git checkout <branch>
	# then save_version_git()
	pass

def save_version_git_master(*args):
	"""LibreOffice Macro Entry Point: """
	#git checkout master
	pass


# lists the scripts, that shall be visible inside OOo.
# Can be omitted, if all functions shall be visible
g_exportedScripts = save_version_git,


#--------------------------------------------------

def print_to_textdoc(msg='x-x-x'):
	"""Print Message into current LO Text document if exists"""
	model = get_lo_model()

	#check whether there's already an opened document. Otherwise, create a new one
	if not hasattr(model, "Text"):
		model = create_new_lo_writer_document()

	#get the XText interface
	text = model.Text
	#create an XTextRange at the end of the document
	tRange = text.End
	#and set the string
	tRange.String = "\n%s\n" % (msg)

	return None


#--#--#--#--#--#--#--#--#--#--#--
# Testing:  Use unittest(?)
# - Deploy to LO python script directory,
# - open new or an example ODT, or ODS,
# - run save_version_git macro


# vim: ts=4 sw=4 sts=4 noexpandtab
# kate: indent-mode python; indent-width 4; tab-width 4; _replace-tabs on;
#eof
