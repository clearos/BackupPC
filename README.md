# BackupPC

Forked version of clamav with ClearOS changes applied

* git clone git+ssh://git@github.com/clearos/BackupPC.git
* cd BackupPC
* git checkout epel7
* git remote add upstream git://pkgs.fedoraproject.org/BackupPC.git
* git pull upstream epel7
* git checkout clear7
* git merge --no-commit epel7
* git commit
