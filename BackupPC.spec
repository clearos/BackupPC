%if %{?fedora}%{?rhel} >= 5
%define useselinux 1
%else
%define useselinux 0
%endif

Name:           BackupPC
Version:        3.1.0
Release:        4%{?dist}
Summary:        High-performance backup system

Group:          Applications/System
License:        GPLv2+
URL:            http://backuppc.sourceforge.net/
Source0:        http://dl.sourceforge.net/backuppc/%{name}-%{version}.tar.gz
Source1:        BackupPC.htaccess
Source2:        BackupPC.logrotate
Source3:        BackupPC-README.fedora
Patch0:         BackupPC-TopDir_change.patch
BuildRoot:      %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)
BuildArch:      noarch

BuildRequires:  /bin/cat
BuildRequires:  /bin/df
BuildRequires:  /bin/gtar
BuildRequires:  %{_bindir}/nmblookup
BuildRequires:  %{_bindir}/rsync
BuildRequires:  %{_sbindir}/sendmail
BuildRequires:  %{_bindir}/smbclient
BuildRequires:  %{_bindir}/split
BuildRequires:  %{_bindir}/ssh
BuildRequires:  perl(Compress::Zlib)

Requires:       httpd
Requires:       perl-suidperl
Requires:       perl(File::RsyncP)
Requires:       perl(Compress::Zlib)
Requires:       perl(Archive::Zip)
Requires:       perl-Time-modules
Requires:       perl(XML::RSS)
Requires:       rsync
Requires:       samba-client
Requires(pre):  %{_sbindir}/useradd
Requires(preun): initscripts, chkconfig
Requires(post): initscripts, chkconfig, %{_sbindir}/usermod
Requires(postun): initscripts
%if %{useselinux}
Requires:       policycoreutils
BuildRequires:  selinux-policy-devel, checkpolicy
%endif
Provides:       backuppc = %{version}

%description
BackupPC is a high-performance, enterprise-grade system for backing up Linux
and WinXX PCs and laptops to a server's disk. BackupPC is highly configurable
and easy to install and maintain.

%prep
%setup -q
%patch0 -p1
sed -i "s|\"backuppc\"|\"$LOGNAME\"|g" configure.pl
iconv -f ISO-8859-1 -t UTF-8 ChangeLog > ChangeLog.utf && mv ChangeLog.utf ChangeLog
pushd doc
iconv -f ISO-8859-1 -t UTF-8 BackupPC.pod > BackupPC.pod.utf && mv BackupPC.pod.utf BackupPC.pod
iconv -f ISO-8859-1 -t UTF-8 BackupPC.html > BackupPC.html.utf && mv BackupPC.html.utf BackupPC.html
popd
cp %{SOURCE3} README.fedora

%if %{useselinux}
%{__mkdir} selinux
pushd selinux

cat >%{name}.te <<EOF
policy_module(%{name},0.0.3)
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
        type httpd_sys_content_t;
        class sock_file getattr;
}

allow httpd_t httpd_sys_content_t:sock_file write;
allow httpd_t initrc_t:unix_stream_socket connectto;
allow httpd_t ping_exec_t:file getattr;
allow httpd_t sendmail_exec_t:file getattr;
allow httpd_t ssh_exec_t:file getattr;
allow httpd_t httpd_sys_content_t:sock_file getattr;
EOF

cat >%{name}.fc <<EOF
%{_sysconfdir}/%{name}(/.*)?            gen_context(system_u:object_r:httpd_sys_content_t,s0)
%{_sysconfdir}/%{name}/pc(/.*)?         gen_context(system_u:object_r:httpd_sys_script_rw_t,s0)
%{_localstatedir}/log/%{name}(/.*)?     gen_context(system_u:object_r:httpd_sys_content_t,s0)
EOF
%endif

%build
%if %{useselinux}
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

%{__mkdir} -p $RPM_BUILD_ROOT%{_initrddir}
%{__mkdir} -p $RPM_BUILD_ROOT%{_sysconfdir}/httpd/conf.d/
%{__mkdir} -p $RPM_BUILD_ROOT%{_sysconfdir}/logrotate.d/
%{__mkdir} -p $RPM_BUILD_ROOT%{_localstatedir}/log/%{name}
%{__mkdir} -p $RPM_BUILD_ROOT%{_sysconfdir}/%{name}/pc

%{__cp} init.d/linux-backuppc $RPM_BUILD_ROOT%{_initrddir}/backuppc
%{__cp} %{SOURCE1} $RPM_BUILD_ROOT%{_sysconfdir}/httpd/conf.d/%{name}.conf
%{__cp} %{SOURCE2} %{buildroot}/%{_sysconfdir}/logrotate.d/%{name}

%{__chmod} 755 $RPM_BUILD_ROOT%{_datadir}/%{name}/bin/*
%{__chmod} 755 $RPM_BUILD_ROOT%{_initrddir}/backuppc

sed -i 's/^\$Conf{XferMethod}\ =.*/$Conf{XferMethod} = "rsync";/' $RPM_BUILD_ROOT%{_sysconfdir}/%{name}/config.pl
sed -i 's|^\$Conf{CgiURL}\ =.*|$Conf{CgiURL} = "http://localhost/BackupPC";|' $RPM_BUILD_ROOT%{_sysconfdir}/%{name}/config.pl
sed -i 's|ClientNameAlias           => 1,|ClientNameAlias           => 0,|' $RPM_BUILD_ROOT%{_sysconfdir}/%{name}/config.pl

%if %{useselinux}
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
        service backuppc stop > /dev/null 2>&1 || :
        chkconfig --del backuppc || :
fi

%post
%if %{useselinux}
(
     # Install/update Selinux policy
     semodule -i %{_datadir}/selinux/packages/%{name}/%{name}.pp
     # files created by app
     restorecon -R %{_sysconfdir}/%{name}
     restorecon -R %{_localstatedir}/lib/%{name}
     restorecon -R %{_localstatedir}/log/%{name}
) &>/dev/null
%endif
chkconfig --add backuppc || :
service httpd condrestart > /dev/null 2>&1 || :
%{_sbindir}/usermod -a -G backuppc apache || :


%postun
service httpd condrestart > /dev/null 2>&1 || :
%if %{useselinux}
if [ "$1" -eq "0" ]; then
     (
     # Remove the SElinux policy.
     semodule -r %{name} || :
     )&>/dev/null
fi
%endif


%files
%defattr(-,root,root,-)
%doc README README.fedora ChangeLog LICENSE doc/

%dir %attr(-,backuppc,backuppc) %{_localstatedir}/log/%{name} 
%dir %attr(-,backuppc,backuppc) %{_sysconfdir}/%{name}/

%config(noreplace) %{_sysconfdir}/httpd/conf.d/%{name}.conf
%config(noreplace) %attr(-,backuppc,backuppc) %{_sysconfdir}/%{name}/*
%config(noreplace) %{_sysconfdir}/logrotate.d/%{name}

%dir %{_datadir}/%{name} 
%dir %{_datadir}/%{name}/sbin
%{_datadir}/%{name}/[^s]*
%{_initrddir}/backuppc

%attr(4750,backuppc,apache) %{_datadir}/%{name}/sbin/BackupPC_Admin
%attr(-,backuppc,root) %{_localstatedir}/lib/%{name}/

%if %{useselinux}
%{_datadir}/selinux/packages/%{name}/%{name}.pp
%endif

%changelog
* Fri Jan 15 2010 Johan Cwiklinski <johan AT x-tnd DOT be> 3.1.0-4
- Fix selinux labelling backup directoru (bug #525948)
- Fix security bug (bug #518412)
- Fix SELinux policy module for UserEmailInfo.pl file

* Fri Apr 10 2009 Johan Cwiklinski <johan AT x-tnd DOT be> 3.1.0-3
- Fix TopDir change (bug #473944)

* Sat Aug 23 2008 Johan Cwiklinski <johan AT x-tnd DOT be> 3.1.0-2
- using /dev/null with SELinux policy to avoid broken pipe errors (bug #432149)
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

* Sat Aug 16 2006 Mike McGrath <imlinux@gmail.com> 2.1.2-7
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
