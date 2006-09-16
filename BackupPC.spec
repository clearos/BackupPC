Name:		BackupPC
Version:	2.1.2
Release:	7%{?dist}
Summary:	BackupPC - high-performance backup system

Group:		Applications/System
License:	GPL
URL:		http://backuppc.sourceforge.net/
Source0:	http://dl.sourceforge.net/backuppc/%{name}-%{version}.tar.gz
Source1:	BackupPC.htaccess
Source2:	BackupPC.logrotate
Patch0:		BackupPC-2.1.2pl2.diff
BuildRoot:	%{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)
BuildArch:	noarch

BuildRequires:	/bin/cat /bin/df /bin/gtar %{_bindir}/nmblookup %{_bindir}/rsync %{_sbindir}/sendmail %{_bindir}/smbclient %{_bindir}/split %{_bindir}/ssh
Requires: httpd
Requires: perl-suidperl
Requires: perl(File::RsyncP)
Requires: rsync
Requires(pre): %{_sbindir}/useradd
Requires(preun): /sbin/service, /sbin/chkconfig
Requires(post): /sbin/chkconfig, /sbin/service, %{_sbindir}/usermod
Requires(postun): /sbin/service



%description
BackupPC is a high-performance, enterprise-grade system for backing up Linux
and WinXX PCs and laptops to a server's disk. BackupPC is highly configurable
and easy to install and maintain.

%prep
%setup -q
%patch0 -p0
sed -i s/\"backuppc\"/\"$LOGNAME\"/ configure.pl

# There is no good build method for backuppc.  Instead the configure script
# also does installation of files.

%install
rm -rf %{buildroot}
perl configure.pl --batch \
		--cgi-dir %{buildroot}/%{_datadir}/%{name}/sbin/ \
		--data-dir %{buildroot}/%{_localstatedir}/lib/%{name}/ \
		--html-dir %{buildroot}/%{_datadir}/%{name}/html/ \
		--html-dir-url /%{name}/images \
		--install-dir %{buildroot}/%{_datadir}/%{name} \
		--uid-ignore
for f in `find %{buildroot}`
do
	if [ -f $f ]
	then
		sed -i s,%{buildroot},,g $f
		sed -i s,$LOGNAME,backuppc,g $f
	fi
done
sed -i s,%{buildroot},,g init.d/linux-backuppc
sed -i s,$LOGNAME,backuppc,g init.d/linux-backuppc

%{__mkdir} -p %{buildroot}/%{_initrddir}
%{__mkdir} -p %{buildroot}/%{_sysconfdir}/httpd/conf.d/
%{__mkdir} -p %{buildroot}/%{_sysconfdir}/logrotate.d/
%{__mkdir} -p %{buildroot}/%{_localstatedir}/log/%{name}

%{__cp} init.d/linux-backuppc %{buildroot}/%{_initrddir}/%{name}
%{__cp} %{SOURCE1} %{buildroot}/%{_sysconfdir}/httpd/conf.d/%{name}.conf
%{__cp} %{SOURCE2} %{buildroot}/%{_sysconfdir}/logrotate.d/%{name}

%{__chmod} 755 %{buildroot}/%{_datadir}/%{name}/bin/*
%{__chmod} 755 %{buildroot}/%{_initrddir}/%{name}

%{__mv} %{buildroot}/%{_localstatedir}/lib/%{name}/conf %{buildroot}/%{_sysconfdir}/%{name}

%{__rm} -f %{buildroot}/%{_datadir}/%{name}/html/CVS
%{__rm} -rf %{buildroot}/%{_localstatedir}/lib/%{name}/log

sed -i 's/^\$Conf{XferMethod}\ =.*/$Conf{XferMethod} = "rsync";/' %{buildroot}/%{_sysconfdir}/%{name}/config.pl
sed -i 's/^\$Conf{ServerHost}\ =.*/$Conf{ServerHost} = "localhost";/' %{buildroot}/%{_sysconfdir}/%{name}/config.pl
sed -i 's,^\$Conf{CgiURL}\ =.*,$Conf{CgiURL} = "http://localhost/cgi-bin/BackupPC_Admin";,' %{buildroot}/%{_sysconfdir}/%{name}/config.pl

ln -s %{_sysconfdir}/%{name}/ %{buildroot}/%{_localstatedir}/lib/%{name}/conf
ln -s ../../log/%{name}/ %{buildroot}/%{_localstatedir}/lib/%{name}/log


%clean
rm -rf %{buildroot}


%pre
%{_sbindir}/useradd -d %{_localstatedir}/lib/%{name} -r -s /sbin/nologin backuppc 2> /dev/null || :

%preun
if [ $1 = 0 ]; then
        /sbin/service %{name} stop > /dev/null 2>&1 || :
        /sbin/chkconfig --del %{name} || :
fi

%post
/sbin/chkconfig --add %{name} || :
/sbin/service httpd condrestart > /dev/null 2>&1 || :
%{_sbindir}/usermod -a -G backuppc apache || :

%postun
/sbin/service httpd condrestart > /dev/null 2>&1 || :

%files
%defattr(-,root,root,-)
%doc README ChangeLog LICENSE doc/
%dir %{_datadir}/%{name}/

%dir %attr(-,backuppc,backuppc) %{_localstatedir}/log/%{name}
%dir %attr(-,backuppc,backuppc) %{_sysconfdir}/%{name}/

%config(noreplace) %{_sysconfdir}/httpd/conf.d/%{name}.conf
%config(noreplace) %attr(-,backuppc,backuppc) %{_sysconfdir}/%{name}/*
%config(noreplace) %{_sysconfdir}/logrotate.d/%{name}

%{_datadir}/%{name}/[^s]*
%{_initrddir}/%{name}

%attr(4750,backuppc,apache) %{_datadir}/%{name}/sbin/BackupPC_Admin
%attr(-,backuppc,root) %{_localstatedir}/lib/%{name}/


%changelog
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
