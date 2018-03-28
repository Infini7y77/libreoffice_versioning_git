==================================
 README - Libreoffice Versioning In Git
==================================
 .. kate: syntax RestructuredText HRC;
:by: harland.coles
:dt: 20180326

.. comment


PURPOSE
+++++++++++++++
To store versioning of Libreoffice / ODF Documents in a git repository.



INSTALL
+++++++++++++++
To Install, copy 'git_versioning.py' into, either:
- ${HOME}/.config/libreoffice/4-suse/user/Scripts/python/, or
- /usr/lib64/libreoffice/share/Scripts/python/

Requires:
- python library: pygit2,



USAGE
+++++++++++++++

Toolbar Button
-----------------------
Easiest is to setup a toolbar button within LibreOffice Writer for Text Documents:
1. Goto LibreOffice File Menu> Tools > Customize
2. Then Tab[Toolbars] > {New...} --> Name: eg. "Versioning1" or "Macros1"
3. Then {Add Command} --> Category: Scroll to "LibreOffice Macros", and expand
4. Then expand "My Macros", select 'git_versioning', and select 'save_version_git',
5. Then {Add}, and {Close}.
6. Optionally, goto {Modify} and 'Change Icon', and select any icon to suit.
7. Then {OK} to complete "Customize" dialog

Any time want to Save a Version into the Git repository, then click toolbar button 'save_version_git'.
This will save to the "<doc name>__versions" directory and commit the changes into git.

Use Git tools to work with Git repo to compare with past versions, etc.









REFERENCE
+++++++++++++++

Source links
===========
.. _link: http://docutils.sourceforge.net/docs/ref/rst/restructuredtext.html

.. eof