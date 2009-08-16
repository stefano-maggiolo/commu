#!/usr/bin/env python
# -*- coding: utf-8 -*-
##
##    Copyright (C) 2007 manatlan manatlan[at]gmail(dot)com
##
## This program is free software; you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published
## by the Free Software Foundation; version 2 only.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##
import os
import sys
import shutil
import time,string
from glob import glob
from datetime import datetime
import socket # gethostname()

__version__ = "0.4"
__author__ = "manatlan"
__mail__ = "manatlan@gmail.com"

"""
Known limitations :
- don't sign package (-us -uc)
- no distinctions between author and maintainer(packager)

depends on :
- dpkg-dev (dpkg-buildpackage)
- alien
- python
- fakeroot

changelog
 - 0.4 14/10/2008
    - use os.environ USERNAME or USER (debian way)
    - install on py 2.(4,5,6) (*FIX* do better here)

"""
from subprocess import Popen,PIPE
def run(cmds):
    p = Popen(cmds, shell=False,stdout=PIPE,stderr=PIPE)
    time.sleep(0.01)    # to avoid "IOError: [Errno 4] Interrupted system call"
    out = string.join(p.stdout.readlines() ).strip()
    outerr = string.join(p.stderr.readlines() ).strip()
    return out

def deb2rpm(file):
    txt=run(['alien','-r',file])
    return txt.split(" generated")[0]

class Py2debException(Exception): pass

class Py2deb(object):
    """
    heavily based on technic described here :
    http://wiki.showmedo.com/index.php?title=LinuxJensMakingDeb
    """
    ## STATICS
    clear=True  # clear build folder after py2debianization

    # http://www.debian.org/doc/debian-policy/ch-archive.html#s-subsections
    SECTIONS="admin, base, comm, contrib, devel, doc, editors, electronics, embedded, games, gnome, graphics, hamradio, interpreters, kde, libs, libdevel, mail, math, misc, net, news, non-free, oldlibs, otherosfs, perl, python, science, shells, sound, tex, text, utils, web, x11".split(", ")

    #http://www.debian.org/doc/debian-policy/footnotes.html#f69
    ARCHS="all i386 ia64 alpha amd64 armeb arm hppa m32r m68k mips mipsel powerpc ppc64 s390 s390x sh3 sh3eb sh4 sh4eb sparc darwin-i386 darwin-ia64 darwin-alpha darwin-amd64 darwin-armeb darwin-arm darwin-hppa darwin-m32r darwin-m68k darwin-mips darwin-mipsel darwin-powerpc darwin-ppc64 darwin-s390 darwin-s390x darwin-sh3 darwin-sh3eb darwin-sh4 darwin-sh4eb darwin-sparc freebsd-i386 freebsd-ia64 freebsd-alpha freebsd-amd64 freebsd-armeb freebsd-arm freebsd-hppa freebsd-m32r freebsd-m68k freebsd-mips freebsd-mipsel freebsd-powerpc freebsd-ppc64 freebsd-s390 freebsd-s390x freebsd-sh3 freebsd-sh3eb freebsd-sh4 freebsd-sh4eb freebsd-sparc kfreebsd-i386 kfreebsd-ia64 kfreebsd-alpha kfreebsd-amd64 kfreebsd-armeb kfreebsd-arm kfreebsd-hppa kfreebsd-m32r kfreebsd-m68k kfreebsd-mips kfreebsd-mipsel kfreebsd-powerpc kfreebsd-ppc64 kfreebsd-s390 kfreebsd-s390x kfreebsd-sh3 kfreebsd-sh3eb kfreebsd-sh4 kfreebsd-sh4eb kfreebsd-sparc knetbsd-i386 knetbsd-ia64 knetbsd-alpha knetbsd-amd64 knetbsd-armeb knetbsd-arm knetbsd-hppa knetbsd-m32r knetbsd-m68k knetbsd-mips knetbsd-mipsel knetbsd-powerpc knetbsd-ppc64 knetbsd-s390 knetbsd-s390x knetbsd-sh3 knetbsd-sh3eb knetbsd-sh4 knetbsd-sh4eb knetbsd-sparc netbsd-i386 netbsd-ia64 netbsd-alpha netbsd-amd64 netbsd-armeb netbsd-arm netbsd-hppa netbsd-m32r netbsd-m68k netbsd-mips netbsd-mipsel netbsd-powerpc netbsd-ppc64 netbsd-s390 netbsd-s390x netbsd-sh3 netbsd-sh3eb netbsd-sh4 netbsd-sh4eb netbsd-sparc openbsd-i386 openbsd-ia64 openbsd-alpha openbsd-amd64 openbsd-armeb openbsd-arm openbsd-hppa openbsd-m32r openbsd-m68k openbsd-mips openbsd-mipsel openbsd-powerpc openbsd-ppc64 openbsd-s390 openbsd-s390x openbsd-sh3 openbsd-sh3eb openbsd-sh4 openbsd-sh4eb openbsd-sparc hurd-i386 hurd-ia64 hurd-alpha hurd-amd64 hurd-armeb hurd-arm hurd-hppa hurd-m32r hurd-m68k hurd-mips hurd-mipsel hurd-powerpc hurd-ppc64 hurd-s390 hurd-s390x hurd-sh3 hurd-sh3eb hurd-sh4 hurd-sh4eb hurd-sparc".split(" ")

    # license terms taken from dh_make
    LICENSES=["gpl","lgpl","bsd","artistic"]
    ## ========


    def __setitem__(self,path,files):

        if not type(files)==list:
            raise Py2debException("value of key path '%s' is not a list"%path)
        if not files:
            raise Py2debException("value of key path '%s' should'nt be empty"%path)
        if not path.startswith("/"):
            raise Py2debException("key path '%s' malformed (don't start with '/')"%path)
        if path.endswith("/"):
            raise Py2debException("key path '%s' malformed (shouldn't ends with '/')"%path)

        nfiles=[]
        for file in files:

            if ".." in file:
                raise Py2debException("file '%s' contains '..', please avoid that!"%file)


            if "|" in file:
                if file.count("|")!=1:
                    raise Py2debException("file '%s' is incorrect (more than one pipe)"%file)

                file,nfile = file.split("|")
            else:
                nfile=file  # same localisation

            if os.path.isdir(file):
                raise Py2debException("file '%s' is a folder, and py2deb refuse folders !"%file)

            if not os.path.isfile(file):
                raise Py2debException("file '%s' doesn't exist"%file)

            if file.startswith("/"):    # if an absolute file is defined
                if file==nfile:         # and not renamed (pipe trick)
                    nfile=os.path.basename(file)   # it's simply copied to 'path'

            nfiles.append( (file,nfile) )

        nfiles.sort( lambda a,b :cmp(a[1],b[1]))    #sort according new name (nfile)

        self.__files[path]=nfiles


    def __delitem__(self,k):
        del self.__files[k]

    def __init__(self,
                    name,
                    description="no description",
                    license="gpl",
                    depends="",
                    section="utils",
                    arch="all",

                    url="",
                    author = None,
                    mail = None
                ):

        if author is None:
            author = ("USERNAME" in os.environ) and os.environ["USERNAME"] or None
            if author is None:
                author = ("USER" in os.environ) and os.environ["USER"] or "unknown"

        if mail is None:
            mail = author+"@"+socket.gethostname()

        self.name = name
        self.description = description
        self.license = license
        self.depends = depends
        self.section = section
        self.arch = arch
        self.url = url
        self.author = author
        self.mail = mail

        self.__files={}

    def __repr__(self):
        name = self.name
        license = self.license
        description = self.description
        depends = self.depends
        section = self.section
        arch = self.arch
        url = self.url
        author = self.author
        mail = self.mail

        paths=self.__files.keys()
        paths.sort()
        files=[]
        for path in paths:
            for file,nfile in self.__files[path]:
                #~ rfile=os.path.normpath( os.path.join(path,nfile) )
                rfile=os.path.join(path,nfile)
                if nfile==file:
                    files.append( rfile )
                else:
                    files.append( rfile + " (%s)"%file)

        files.sort()
        files = "\n".join(files)

        return """
----------------------------------------------------------------------
NAME        : %(name)s
----------------------------------------------------------------------
LICENSE     : %(license)s
URL         : %(url)s
AUTHOR      : %(author)s
MAIL        : %(mail)s
----------------------------------------------------------------------
DEPENDS     : %(depends)s
ARCH        : %(arch)s
SECTION     : %(section)s
----------------------------------------------------------------------
DESCRIPTION :
%(description)s
----------------------------------------------------------------------
FILES :
%(files)s
""" % locals()

    def generate(self,version,changelog="",rpm=False,src=False):
        """ generate a deb of version 'version', with or without 'changelog', with or without a rpm
            (in the current folder)
            return a list of generated files
        """
        if not sum([len(i) for i in self.__files.values()])>0:
            raise Py2debException("no files are defined")

        if not changelog:
            changelog="no changelog"

        name = self.name
        description = self.description
        license = self.license
        depends = self.depends
        section = self.section
        arch = self.arch
        url = self.url
        author = self.author
        mail = self.mail
        files=self.__files

        if section not in Py2deb.SECTIONS:
            raise Py2debException("section '%s' is unknown (%s)" % (section,str(Py2deb.SECTIONS)))

        if arch not in Py2deb.ARCHS:
            raise Py2debException("arch '%s' is unknown (%s)"% (arch,str(Py2deb.ARCHS)))

        if license not in Py2deb.LICENSES:
            raise Py2debException("License '%s' is unknown (%s)" % (license,str(Py2deb.LICENSES)))

        # create dates (buildDate,buildDateYear)
        d=datetime.now()
        buildDate=d.strftime("%a, %d %b %Y %H:%M:%S +0000")
        buildDateYear=str(d.year)


        #clean description (add a space before each next lines)
        description=description.replace("\r","").strip()
        description = "\n ".join(description.split("\n"))

        #clean changelog (add 2 spaces before each next lines)
        changelog=changelog.replace("\r","").strip()
        changelog = "\n  ".join(changelog.split("\n"))


        TEMP = ".py2deb_build_folder"
        DEST = os.path.join(TEMP,name)
        DEBIAN = os.path.join(DEST,"debian")

        # let's start the process
        try:
            shutil.rmtree(TEMP)
        except:
            pass

        os.makedirs(DEBIAN)
        try:
            rules=[]
            dirs=[]
            for path in files:
                for file,nfile in files[path]:
                    if os.path.isfile(file):
                        # it's a file

                        if file.startswith("/"): # if absolute path
                            # we need to change dest
                            dest=os.path.join(DEST,nfile)
                        else:
                            dest=os.path.join(DEST,file)

                        # copy file to be packaged
                        destDir = os.path.dirname(dest)
                        if not os.path.isdir(destDir):
                            os.makedirs(destDir)

                        shutil.copy2(file,dest)

                        ndir = os.path.join(path,os.path.dirname(nfile))
                        nname = os.path.basename(nfile)

                        # make a line RULES to be sure the destination folder is created
                        # and one for copying the file
                        fpath = "/".join(["$(CURDIR)","debian",name+ndir])
                        rules.append('mkdir -p "%s"' % fpath)
                        rules.append('cp -a "%s" "%s"' % (file,os.path.join(fpath,nname)))

                        # append a dir
                        dirs.append(ndir)

                    else:
                        raise Py2debException("unknown file '' "%file) # shouldn't be raised (because controlled before)

            # make rules right
            rules= "\n\t".join(rules) +  "\n"

            # make dirs right
            dirs= [ i[1:] for i in set(dirs)]
            dirs.sort()

            #==========================================================================
            # CREATE debian/dirs
            #==========================================================================
            open(os.path.join(DEBIAN,"dirs"),"w").write("\n".join(dirs))

            #==========================================================================
            # CREATE debian/changelog
            #==========================================================================
            clog="""%(name)s (%(version)s) stable; urgency=low

  %(changelog)s

 -- %(author)s <%(mail)s>  %(buildDate)s
""" % locals()

            open(os.path.join(DEBIAN,"changelog"),"w").write(clog)

            #==========================================================================
            # CREATE debian/compat
            #==========================================================================
            open(os.path.join(DEBIAN,"compat"),"w").write("5\n")

            #==========================================================================
            # CREATE debian/control
            #==========================================================================
            txt="""Source: %(name)s
Section: %(section)s
Priority: extra
Maintainer: %(author)s <%(mail)s>
Build-Depends: debhelper (>= 5)
Standards-Version: 3.7.2

Package: %(name)s
Architecture: %(arch)s
Depends: %(depends)s
Description: %(description)s""" % locals()
            open(os.path.join(DEBIAN,"control"),"w").write(txt)

            #==========================================================================
            # CREATE debian/copyright
            #==========================================================================
            copy={}
            copy["gpl"]="""
    This package is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 2 of the License, or
    (at your option) any later version.

    This package is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this package; if not, write to the Free Software
    Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301 USA

On Debian systems, the complete text of the GNU General
Public License can be found in `/usr/share/common-licenses/GPL'.
"""
            copy["lgpl"]="""
    This package is free software; you can redistribute it and/or
    modify it under the terms of the GNU Lesser General Public
    License as published by the Free Software Foundation; either
    version 2 of the License, or (at your option) any later version.

    This package is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
    Lesser General Public License for more details.

    You should have received a copy of the GNU Lesser General Public
    License along with this package; if not, write to the Free Software
    Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301 USA

On Debian systems, the complete text of the GNU Lesser General
Public License can be found in `/usr/share/common-licenses/LGPL'.
"""
            copy["bsd"]="""
    Redistribution and use in source and binary forms, with or without
    modification, are permitted under the terms of the BSD License.

    THIS SOFTWARE IS PROVIDED BY THE REGENTS AND CONTRIBUTORS ``AS IS'' AND
    ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
    IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
    ARE DISCLAIMED.  IN NO EVENT SHALL THE REGENTS OR CONTRIBUTORS BE LIABLE
    FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
    DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS
    OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
    HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
    LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY
    OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF
    SUCH DAMAGE.

On Debian systems, the complete text of the BSD License can be
found in `/usr/share/common-licenses/BSD'.
"""
            copy["artistic"]="""
    This program is free software; you can redistribute it and/or modify it
    under the terms of the "Artistic License" which comes with Debian.

    THIS PACKAGE IS PROVIDED "AS IS" AND WITHOUT ANY EXPRESS OR IMPLIED
    WARRANTIES, INCLUDING, WITHOUT LIMITATION, THE IMPLIED WARRANTIES
    OF MERCHANTIBILITY AND FITNESS FOR A PARTICULAR PURPOSE.

On Debian systems, the complete text of the Artistic License
can be found in `/usr/share/common-licenses/Artistic'.
"""

            txtLicense = copy[license]
            pv=__version__
            txt="""This package was py2debianized(%(pv)s) by %(author)s <%(mail)s> on
%(buildDate)s.

It was downloaded from %(url)s

Upstream Author: %(author)s <%(mail)s>

Copyright: %(buildDateYear)s by %(author)s

License:

%(txtLicense)s

The Debian packaging is (C) %(buildDateYear)s, %(author)s <%(mail)s> and
is licensed under the GPL, see above.


# Please also look if there are files or directories which have a
# different copyright/license attached and list them here.
""" % locals()
            open(os.path.join(DEBIAN,"copyright"),"w").write(txt)

            #==========================================================================
            # CREATE debian/rules
            #==========================================================================
            txt="""#!/usr/bin/make -f
# -*- makefile -*-
# Sample debian/rules that uses debhelper.
# This file was originally written by Joey Hess and Craig Small.
# As a special exception, when this file is copied by dh-make into a
# dh-make output file, you may use that output file without restriction.
# This special exception was added by Craig Small in version 0.37 of dh-make.

# Uncomment this to turn on verbose mode.
#export DH_VERBOSE=1




CFLAGS = -Wall -g

ifneq (,$(findstring noopt,$(DEB_BUILD_OPTIONS)))
	CFLAGS += -O0
else
	CFLAGS += -O2
endif

configure: configure-stamp
configure-stamp:
	dh_testdir
	# Add here commands to configure the package.

	touch configure-stamp


build: build-stamp

build-stamp: configure-stamp
	dh_testdir
	touch build-stamp

clean:
	dh_testdir
	dh_testroot
	rm -f build-stamp configure-stamp
	dh_clean

install: build
	dh_testdir
	dh_testroot
	dh_clean -k
	dh_installdirs

	# ======================================================
	#$(MAKE) DESTDIR="$(CURDIR)/debian/%(name)s" install
	mkdir -p "$(CURDIR)/debian/%(name)s"

	%(rules)s
	# ======================================================

# Build architecture-independent files here.
binary-indep: build install
# We have nothing to do by default.

# Build architecture-dependent files here.
binary-arch: build install
	dh_testdir
	dh_testroot
	dh_installchangelogs debian/changelog
	dh_installdocs
	dh_installexamples
#	dh_install
#	dh_installmenu
#	dh_installdebconf
#	dh_installlogrotate
#	dh_installemacsen
#	dh_installpam
#	dh_installmime
#	dh_python
#	dh_installinit
#	dh_installcron
#	dh_installinfo
	dh_installman
	dh_link
	dh_strip
	dh_compress
	dh_fixperms
#	dh_perl
#	dh_makeshlibs
	dh_installdeb
	dh_shlibdeps
	dh_gencontrol
	dh_md5sums
	dh_builddeb

binary: binary-indep binary-arch
.PHONY: build clean binary-indep binary-arch binary install configure
""" % locals()
            open(os.path.join(DEBIAN,"rules"),"w").write(txt)
            os.chmod(os.path.join(DEBIAN,"rules"),0755)

            ###########################################################################
            ###########################################################################
            ###########################################################################

            #http://www.debian.org/doc/manuals/maint-guide/ch-build.fr.html
            ret=os.system('cd "%(DEST)s"; dpkg-buildpackage -tc -rfakeroot -us -uc' % locals())
            if ret!=0:
                raise Py2debException("buildpackage failed (see output)")

            l=glob("%(TEMP)s/%(name)s*.deb"%locals())
            if len(l)!=1:
                raise Py2debException("don't find builded deb")

            tdeb = l[0]
            deb = os.path.basename(tdeb)
            shutil.move(tdeb,deb)

            ret=[deb,]

            if rpm:
                rpm = deb2rpm(deb)
                ret.append(rpm)

            if src:
                l=glob("%(TEMP)s/%(name)s*.tar.gz"%locals())
                if len(l)!=1:
                    raise Py2debException("don't find source package tar.gz")

                tar = os.path.basename(l[0])
                shutil.move(l[0],tar)

                ret.append(tar)

            return ret

        #~ except Exception,m:
            #~ raise Py2debException("build error :"+str(m))

        finally:
            if Py2deb.clear:
                shutil.rmtree(TEMP)


if __name__ == "__main__":
    try:
        os.chdir(os.path.dirname(sys.argv[0]))
    except:
        pass

    p=Py2deb("python-py2deb")
    p.description="Generate simple deb(/rpm) from python"
    p.author=__author__
    p.mail=__mail__
    p.depends = "dpkg-dev, fakeroot, alien, python"
    p.section="python"
    p["/usr/lib/python2.6/site-packages"] = ["py2deb.py",]
    p["/usr/lib/python2.5/site-packages"] = ["py2deb.py",]
    p["/usr/lib/python2.4/site-packages"] = ["py2deb.py",]
    print p
    print p.generate(__version__,src=True)
