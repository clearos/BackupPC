# enable -PIE build
%global _hardened_build 1

%if 0%{?rhel} && 0%{?rhel} < 5
%global _without_selinux 1
%endif

# tmpfiles.d & systemd support in all supported Fedora now, but not RHEL
%if 0%{?fedora}
%global _with_tmpfilesd 1
%global _with_systemd 1
%endif

%global _updatedb_conf /etc/updatedb.conf

Name:           BackupPC
Version:        3.3.0
Release:        4%{?dist}
Summary:        High-performance backup system
Group:          Applications/System
License:        GPLv2+
URL:            http://backuppc.sourceforge.net/

Source0:        http://downloads.sourceforge.net/backuppc/%{name}-%{version}.tar.gz
Patch0:         BackupPC-3.2.1-locatedb.patch
Patch1:         BackupPC-3.2.1-rundir.patch
Patch2:         BackupPC-3.2.1-piddir.patch
Patch3:         BackupPC-3.3.0-fix-shadow-access.patch
Source1:        BackupPC.htaccess
Source2:        BackupPC.logrotate
Source3:        BackupPC-README.fedora
#A C wrapper to use since perl-suidperl is no longer provided
Source4:        BackupPC_Admin.c
Source5:        backuppc.service
Source6:        BackupPC.tmpfiles
Source7:        README.RHEL

BuildRequires:  %{_bindir}/smbclient, %{_bindir}/nmblookup
BuildRequires:  rsync
BuildRequires:  coreutils
BuildRequires:  tar
BuildRequires:  openssh-clients
BuildRequires:  perl(Compress::Zlib)
BuildRequires:  perl(Data::Dumper)
BuildRequires:  perl(Digest::MD5)
BuildRequires:  perl(Pod::Usage)
%if 0%{?_with_systemd}
BuildRequires:  systemd-units
%endif

# Unbundled libraries
Requires:       perl(Net::FTP::AutoReconnect), perl(Net::FTP::RetrHandle)

Requires:       httpd
Requires:       perl(File::RsyncP), perl(Compress::Zlib), perl(Archive::Zip)
Requires:       perl-Time-modules, perl(XML::RSS), perl(Digest::MD5)
Requires:       rsync
# This is a file dependency so EL5 can use samba or samba-client or
# samba3x-client
Requires:       %{_bindir}/smbclient, %{_bindir}/nmblookup

Requires(pre):  %{_sbindir}/useradd
%if 0%{?_with_systemd}
Requires(preun): systemd-units
Requires(post):  systemd-units, %{_sbindir}/usermod
Requires(postun): systemd-units
%else
Requires(preun): initscripts, chkconfig
Requires(post): initscripts, chkconfig, %{_sbindir}/usermod
Requires(postun): initscripts
%endif

%if ! 0%{?_without_selinux}
Requires:       policycoreutils
BuildRequires:  selinux-policy-devel, checkpolicy
%endif
Provides:       backuppc = %{version}

# BuildRoot required for RHEL5
BuildRoot:      %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)

%description
BackupPC is a high-performance, enterprise-grade system for backing up Linux
and WinXX and Mac OS X PCs and laptops to a server's disk. BackupPC is highly
configurable and easy to install and maintain.

%prep

%setup -q

%patch0 -p1 -b .locatedb
%patch1 -p1 -b .rundir
%patch2 -p1 -b .piddir
%patch3 -p1 -b .shadow-access

sed -i "s|\"backuppc\"|\"$LOGNAME\"|g" configure.pl
for f in ChangeLog doc/BackupPC.pod doc/BackupPC.html; do
  iconv -f ISO-8859-1 -t UTF-8 $f > $f.utf && mv $f.utf $f
done

#incorrect FSF address
sed -i 's|59 Temple Place, Suite 330, Boston, MA  *02111-1307  USA|51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA|' \
    lib/BackupPC/CGI/Queue.pm \
    bin/BackupPC_archive \
    lib/BackupPC/CGI/StartServer.pm \
    lib/BackupPC/CGI/HostInfo.pm \
    lib/BackupPC/CGI/Archive.pm \
    lib/BackupPC/CGI/LOGlist.pm \
    lib/BackupPC/FileZIO.pm \
    lib/BackupPC/CGI/GeneralInfo.pm \
    lib/BackupPC/CGI/Browse.pm \
    lib/BackupPC/CGI/RSS.pm \
    lib/BackupPC/CGI/Restore.pm \
    lib/BackupPC/CGI/RestoreFile.pm \
    bin/BackupPC_restore \
    lib/BackupPC/CGI/DirHistory.pm \
    lib/BackupPC/Xfer/Archive.pm \
    lib/BackupPC/Config/Meta.pm \
    lib/BackupPC/CGI/ArchiveInfo.pm \
    lib/BackupPC/CGI/ReloadServer.pm \
    lib/BackupPC/CGI/View.pm \
    bin/BackupPC_tarExtract \
    lib/BackupPC/CGI/EmailSummary.pm \
    lib/BackupPC/Xfer/RsyncFileIO.pm \
    lib/BackupPC/CGI/RestoreInfo.pm \
    lib/BackupPC/CGI/StartStopBackup.pm \
    lib/BackupPC/CGI/StopServer.pm \
    lib/BackupPC/CGI/AdminOptions.pm \
    lib/BackupPC/CGI/Summary.pm \
    lib/BackupPC/CGI/EditConfig.pm

chmod a-x LICENSE README

cp %{SOURCE3} README.fedora
cp %{SOURCE7} README.RHEL
cp %{SOURCE4} BackupPC_Admin.c

%if ! 0%{?_without_selinux}
mkdir selinux
pushd selinux

cat >%{name}.te <<EOF
policy_module(%{name},0.0.5)
require {
        type var_log_t;
        type httpd_t;
        class sock_file write;
        type initrc_t;
        class unix_stream_socket connectto;
        type ssh_exec_t;
        type ping_exec_t;
        type sendmail_exec_t;
        class file getattr;
        type var_run_t;
        class sock_file getattr;
        type httpd_log_t;
        class file open;
        class dir read;
}

allow httpd_t var_run_t:sock_file write;
allow httpd_t initrc_t:unix_stream_socket connectto;
allow httpd_t ping_exec_t:file getattr;
allow httpd_t sendmail_exec_t:file getattr;
allow httpd_t ssh_exec_t:file getattr;
allow httpd_t var_run_t:sock_file getattr;
allow httpd_t httpd_log_t:file open;
allow httpd_t httpd_log_t:dir read;
EOF

cat >%{name}.fc <<EOF
%{_sysconfdir}/%{name}(/.*)?            gen_context(system_u:object_r:httpd_sys_script_rw_t,s0)
%{_localstatedir}/run/%{name}(/.*)?     gen_context(system_u:object_r:var_run_t,s0)
%{_localstatedir}/log/%{name}(/.*)?     gen_context(system_u:object_r:httpd_log_t,s0)
EOF
popd
%endif

# attempt to unbundle as much as possible
for m in Net/FTP; do
  rm -rf lib/$m
  pwd; ls -l
  sed -i "\@lib/$m@d" configure.pl 
done

%build
gcc -o BackupPC_Admin BackupPC_Admin.c $RPM_OPT_FLAGS
%if ! 0%{?_without_selinux}
     # SElinux 
     pushd selinux
     make -f %{_datadir}/selinux/devel/Makefile
     popd
%endif

%install
rm -rf $RPM_BUILD_ROOT
perl configure.pl \
        --batch \
        --dest-dir $RPM_BUILD_ROOT \
        --config-dir %{_sysconfdir}/%{name}/ \
        --cgi-dir %{_datadir}/%{name}/sbin/ \
        --data-dir %{_localstatedir}/lib/%{name}/ \
        --html-dir %{_datadir}/%{name}/html/ \
        --html-dir-url /%{name}/images \
        --log-dir %{_localstatedir}/log/%{name} \
        --install-dir %{_datadir}/%{name} \
        --hostname localhost \
        --uid-ignore

for f in `find $RPM_BUILD_ROOT`
do
        if [ -f $f ]
        then
                sed -i s,$LOGNAME,backuppc,g $f
        fi
done
sed -i s,$LOGNAME,backuppc,g init.d/linux-backuppc

%if 0%{?_with_tmpfilesd}
install -d $RPM_BUILD_ROOT/%{_sysconfdir}/tmpfiles.d
install -p -m 0644 %{SOURCE6} $RPM_BUILD_ROOT/%{_sysconfdir}/tmpfiles.d/%{name}.conf
%endif
install -d $RPM_BUILD_ROOT/%{_localstatedir}/run/%{name}

%if 0%{?_with_systemd}
install -d $RPM_BUILD_ROOT/%{_unitdir}
install -p -m 0644 %{SOURCE5} $RPM_BUILD_ROOT/%{_unitdir}/
%else
install -d $RPM_BUILD_ROOT/%{_initrddir}
install -p -m 0755 init.d/linux-backuppc $RPM_BUILD_ROOT%{_initrddir}/backuppc
%endif

install -d $RPM_BUILD_ROOT/%{_sysconfdir}/httpd/conf.d/
install -d $RPM_BUILD_ROOT/%{_sysconfdir}/logrotate.d/
install -d $RPM_BUILD_ROOT/%{_localstatedir}/log/%{name}
install -d $RPM_BUILD_ROOT/%{_sysconfdir}/%{name}

install -p -m 0644 %{SOURCE1} $RPM_BUILD_ROOT/%{_sysconfdir}/httpd/conf.d/%{name}.conf
install -p -m 0644 %{SOURCE2} $RPM_BUILD_ROOT/%{_sysconfdir}/logrotate.d/%{name}

chmod 755 $RPM_BUILD_ROOT%{_datadir}/%{name}/bin/*

sed -i 's/^\$Conf{XferMethod}\ =.*/$Conf{XferMethod} = "rsync";/' $RPM_BUILD_ROOT%{_sysconfdir}/%{name}/config.pl
sed -i 's|^\$Conf{CgiURL}\ =.*|$Conf{CgiURL} = "http://localhost/%{name}";|' $RPM_BUILD_ROOT%{_sysconfdir}/%{name}/config.pl
sed -i 's|ClientNameAlias           => 1,|ClientNameAlias           => 0,|' $RPM_BUILD_ROOT%{_sysconfdir}/%{name}/config.pl

#perl-suidperl is no longer avaialable, we use a C wrapper
mv $RPM_BUILD_ROOT%{_datadir}/%{name}/sbin/BackupPC_Admin $RPM_BUILD_ROOT%{_datadir}/%{name}/sbin/BackupPC_Admin.pl
install -p BackupPC_Admin $RPM_BUILD_ROOT%{_datadir}/%{name}/sbin/

%if ! 0%{?_without_selinux}
     # SElinux 
     %{__mkdir_p} $RPM_BUILD_ROOT%{_datadir}/selinux/packages/%{name}
     %{__install} -m644 selinux/%{name}.pp $RPM_BUILD_ROOT%{_datadir}/selinux/packages/%{name}/%{name}.pp
%endif


%clean
rm -rf $RPM_BUILD_ROOT


%pre
%{_sbindir}/useradd -d %{_localstatedir}/lib/%{name} -r -s /sbin/nologin backuppc 2> /dev/null || :


%preun
if [ $1 = 0 ]; then
  # Package removal, not upgrade
  %if 0%{?_with_systemd}
  /bin/systemctl --no-reload disable backuppc.service > /dev/null 2>&1 || :
  /bin/systemctl stop backuppc.service > /dev/null 2>&1 || :
  %else
  service backuppc stop > /dev/null 2>&1 || :
  chkconfig --del backuppc || :
  %endif
fi

%post
%if ! 0%{?_without_selinux}
(
     # Install/update Selinux policy
     semodule -i %{_datadir}/selinux/packages/%{name}/%{name}.pp
     # files created by app
     restorecon -R %{_sysconfdir}/%{name}
     restorecon -R %{_localstatedir}/log/%{name}
) &>/dev/null
%endif

if [ $1 -eq 1 ]; then
  # initial installation
  %if 0%{?_with_systemd}
  /bin/systemctl daemon-reload > /dev/null 2>&1 || :
  %else
  chkconfig --add backuppc || :
  service httpd condrestart > /dev/null 2>&1 || :
  %endif
  %{_sbindir}/usermod -a -G backuppc apache || :
fi


# add BackupPC backup directories to PRUNEPATHS in locate database
if [ -w %{_updatedb_conf} ]; then
  grep ^PRUNEPATHS %{_updatedb_conf} | grep %{_localstatedir}/lib/%{name} > /dev/null
  if [ $? -eq 1 ]; then
    sed -i '\@PRUNEPATHS@s@"$@ '%{_localstatedir}/lib/%{name}'"@' %{_updatedb_conf}
  fi
fi
:

%postun
# clear out any BackupPC configuration in apache
service httpd condrestart > /dev/null 2>&1 || :

if [ $1 -eq 0 ]; then
  # uninstall
  %if ! 0%{?_without_selinux}
  # Remove the SElinux policy.
  semodule -r %{name} &> /dev/null || :
  %endif

  # remove BackupPC backup directories from PRUNEPATHS in locate database
  if [ -w %{_updatedb_conf} ]; then
    sed -i '\@PRUNEPATHS@s@[ ]*'%{_localstatedir}/lib/%{name}'@@' %{_updatedb_conf} || :
  fi
fi

if [ $1 -eq 1 ]; then
  # package upgrade, not uninstall
  %if 0%{?_with_systemd}
  /bin/systemctl try-restart backuppc.service > /dev/null 2>&1 || :  
  %endif
  # at least one command required
  :
fi

%files
%defattr(-,root,root,-)
%doc README README.fedora README.RHEL ChangeLog LICENSE doc/

%dir %attr(-,backuppc,backuppc) %{_localstatedir}/log/%{name} 
%dir %attr(-,backuppc,backuppc) %{_sysconfdir}/%{name}/

%config(noreplace) %{_sysconfdir}/httpd/conf.d/%{name}.conf
%config(noreplace) %attr(-,backuppc,backuppc) %{_sysconfdir}/%{name}/*
%config(noreplace) %{_sysconfdir}/logrotate.d/%{name}

%dir %{_datadir}/%{name} 
%dir %{_datadir}/%{name}/sbin
%{_datadir}/%{name}/[^s]*

%if 0%{?_with_tmpfilesd}
%config(noreplace) %{_sysconfdir}/tmpfiles.d/%{name}.conf
%endif
%dir %attr(0775,backuppc,backuppc) %{_localstatedir}/run/%{name} 

%if 0%{?_with_systemd}
%{_unitdir}/backuppc.service
%else
%attr(0755,root,root) %{_initrddir}/backuppc
%endif

%attr(4750,backuppc,apache) %{_datadir}/%{name}/sbin/BackupPC_Admin
%attr(750,backuppc,apache) %{_datadir}/%{name}/sbin/BackupPC_Admin.pl
%attr(-,backuppc,root) %{_localstatedir}/lib/%{name}/

%if ! 0%{?_without_selinux}
%{_datadir}/selinux/packages/%{name}/%{name}.pp
%endif

%changelog
* Fri Aug 15 2014 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 3.3.0-4
- Rebuilt for https://fedoraproject.org/wiki/Fedora_21_22_Mass_Rebuild

* Fri Jun 06 2014 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 3.3.0-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_21_Mass_Rebuild

* Fri Feb 21 2014 Bernard Johnson <bjohnson@symetrix.com> 3.3.0-2
- fix typo in README.RHEL
- enable PIE build (bz #965523)
- add patch that causes getpwnam to return only uid to fix selinux denials
  (bz #827854)
- add local-fs.target and remote-fs.target to startup dependency (bz #959309)

* Fri Feb 21 2014 Johan Cwiklinski <johan AT x-tnd DOT be> 3.3.0-1
- Last upstream release
- Remove no longer needeed patches
- Fix incorrect-fsf-address to reduce rpmlint output

* Fri Feb 21 2014 Bernard Johnson <bjohnson@symetrix.com> - 3.3.0-1
- v 3.3.0
- fixed typos

* Fri Aug 02 2013 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 3.2.1-15
- Rebuilt for https://fedoraproject.org/wiki/Fedora_20_Mass_Rebuild

* Wed Jul 17 2013 Petr Pisar <ppisar@redhat.com> - 3.2.1-14
- Perl 5.18 rebuild

* Sun Mar 31 2013 Ville Skyttä <ville.skytta@iki.fi> - 3.2.1-13
- Add build dependency on Pod::Usage (#913855).
- Fix bogus dates in %%changelog.

* Wed Feb 13 2013 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 3.2.1-12
- Rebuilt for https://fedoraproject.org/wiki/Fedora_19_Mass_Rebuild

* Sun Jan 20 2013 Bernard Johnson <bjohnson@symetrix.com> 3.2.1-11
- Missing backuppc.service file after upgrade to 3.2.1-10 causes service to
  exit at start (bz #896626)

* Mon Dec 24 2012 Bernard Johnson <bjohnson@symetrix.com> 3.2.1-10
- cleanup build macros for Fedora
- fix deprecated qw messages (partial fix for bz #755076)
- CVE-2011-5081 BackupPC: XSS flaw in RestoreFile.pm
  (bz #795017, #795018, #795019)
- Broken configuration for httpd 2.4 (bz #871353)

* Sun Dec  9 2012 Peter Robinson <pbrobinson@fedoraproject.org> 3.2.1-9
- Fix FTBFS on F-18+

* Wed Jul 18 2012 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 3.2.1-8
- Rebuilt for https://fedoraproject.org/wiki/Fedora_18_Mass_Rebuild

* Sun Jan 22 2012 Bernard Johnson <bjohnson@symetrix.com> - 3.2.1-7
- change %%{_sharedstatedir} to %%{_localstatedir}/lib as these expand
  differently on EL (bz #767719)
- fix XSS vulnerability (bz #749846, bz #749847, bz #749848) CVE-2011-3361
- additional documentation about enabling correct channels in RHEL to resolve
  all dependencies (bz #749627)
- fix bug with missing tmpfiles.d directory
- add perl(Digest::MD5) to list of build and install dependencies

* Wed Sep 21 2011 Bernard Johnson <bjohnson@symetrix.com> - 3.2.1-6
- fix postun scriptlet error (bz #736946)
- make postun scriptlet more coherent
- change selinux context on log files to httpd_log_t and allow access
  to them (bz #730704)

* Fri Aug 12 2011 Bernard Johnson <bjohnson@symetrix.com> - 3.2.1-4
- change macro conditionals to include tmpfiles.d support starting at
  Fedora 15 (bz #730053)
- change install lines to preserve timestamps

* Fri Jul 08 2011 Bernard Johnson <bjohnson@symetrix.com> - 3.2.1-1
- v 3.2.1
- add lower case script URL alias for typing impaired
- cleanup selinux macros
- spec cleanup
- make samba dependency on actual files required to EL5 can use samba-client
  or samba3x-client (bz #667479)
- unbundle perl(Net::FTP::AutoReconnect) and perl(Net::FTP::RetrHandle)
- remove old patch that is no longer needed
- attempt to make sure $Conf{TopDir} is listed in updatedb PRUNEPATHS,
  otherwise at least generate a warning on statup (bz #554491)
- move sockets to /var/run (bz #719499)
- add support for systemd starting at F16 (bz #699441)
- patch to move pid dir under /var/run
- unbundle Net::FTP::*
- add support for tmpfiles.d

* Mon Feb 07 2011 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 3.1.0-17
- Rebuilt for https://fedoraproject.org/wiki/Fedora_15_Mass_Rebuild

* Mon Aug 02 2010 Johan Cwiklinski <johan AT x-tnd DOT be> 3.1.0-16
- Debugingo with no sources (fix bug #620257)

* Sat Jul 31 2010 Johan Cwiklinski <johan AT x-tnd DOT be> 3.1.0-15
- perl-suidperl is no longer available (fix bug #611009)

* Fri Jul 09 2010 Mike McGrath <mmcgrath@redhat.com> 3.1.0-14.1
- Rebuilding to fix perl-suidperl broken dep

* Mon May 17 2010 Johan Cwiklinski <johan AT x-tnd DOT be> 3.1.0-14
- Fix for bug #592762

* Sun Feb 28 2010 Johan Cwiklinski <johan AT x-tnd DOT be> 3.1.0-12
- Add "::1" to the apache config file for default allowed adresses
- Fix a typo in the apache config file

* Sun Jan 17 2010 Johan Cwiklinski <johan AT x-tnd DOT be> 3.1.0-11
- Really fix selinux labelling backup directory (bug #525948)

* Fri Jan 15 2010 Johan Cwiklinski <johan AT x-tnd DOT be> 3.1.0-10
- Fix selinux labelling backup directory (bug #525948)

* Fri Sep 25 2009 Johan Cwiklinski <johan AT x-tnd DOT be> 3.1.0-9
- Fix security bug (bug #518412)

* Wed Sep 23 2009 Johan Cwiklinski <johan AT x-tnd DOT be> 3.1.0-8
- Rebuild with latest SELinux policy (bug #524630)

* Fri Sep 18 2009 Johan Cwiklinski <johan AT x-tnd DOT be> 3.1.0-7
- Fix SELinux policy module for UserEmailInfo.pl file

* Fri Jul 24 2009 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 3.1.0-6
- Rebuilt for https://fedoraproject.org/wiki/Fedora_12_Mass_Rebuild

* Fri Apr 10 2009 Johan Cwiklinski <johan AT x-tnd DOT be> 3.1.0-5
- Fix TopDir change (bug #473944)

* Mon Feb 23 2009 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 3.1.0-4
- Rebuilt for https://fedoraproject.org/wiki/Fedora_11_Mass_Rebuild

* Mon Aug 11 2008 Johan Cwiklinski <johan AT x-tnd DOT be> 3.1.0-3
- using /dev/null with SELinux policy to avoid broken pipe errors (bug #432149)

* Sat Apr 05 2008 Johan Cwiklinski <johan AT x-tnd DOT be> 3.1.0-2
- correcting nologin path

* Thu Nov 29 2007 Johan Cwiklinski <johan AT x-tnd DOT be> 3.1.0-1
- New upstream version
- Added samba-client as a dependency
- Added readme.fedora
- Changed CGI admin path in default config file

* Fri Sep 21 2007 Johan Cwiklinski <johan AT x-tnd DOT be> 3.0.0-3
- Fixed SELinux policy module

* Wed Sep 12 2007 Johan Cwiklinski <johan AT x-tnd DOT be> 3.0.0-2
- Added SELinux policy module

* Tue Jan 30 2007 Johan Cwiklinski <johan AT x-tnd DOT be> 3.0.0-1
- Rebuild RPM for v 3.0.0

* Sat Aug 26 2006 Mike McGrath <imlinux@gmail.com> 2.1.2-7
- Release bump for rebuild

* Tue Jul 25 2006 Mike McGrath <imlinux@gmail.com> 2.1.2-6
- One more config change

* Sun Jul 23 2006 Mike McGrath <imlinux@gmail.com> 2.1.2-5
- Added upstream patch for better support for rsync

* Sun Jul 23 2006 Mike McGrath <imlinux@gmail.com> 2.1.2-4
- Properly marking config files as such

* Sun Jul 23 2006 Mike McGrath <imlinux@gmail.com> 2.1.2-3
- Changes to defaults in config.pl
- Added Requires: rsync

* Fri Jul 21 2006 Mike McGrath <imlinux@gmail.com> 2.1.2-2
- Added requires: perl(File::RsyncP)

* Tue Jul 18 2006 Mike McGrath <imlinux@gmail.com> 2.1.2-1
- Initial Fedora Packaging
