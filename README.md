Backups
=======

These are scripts written to perform various backup-related tasks.


cryptshot.sh
------------

Open and mount a LUKS volume before performing a backup with
[rsnapshot](http://rsnapshot.org/).

This script first checks to see if a volume with the given UUID exists.
If the volume is found, it is treated as a LUKS volume and decrypted with
the given key file, after which it is mounted. The script then runs
rsnapshot. After the backup is complete, the volume is unmounted and the
LUKS mapping is removed. Optionally, the mount point can be deleted to
complete the clean-up.

This provides for a way to achieve encrypted backups to an external drive
with a backup tool that does not inherently provide encryption. It can
easily be modified to execute a backup program other than rsnapshot. Since
the first step taken is to check if the given volume exists, it is
appropriate for situations where the external backup volume is not always
available to the machine (such as a USB backup drive and a laptop).

The script should be called with the rsnapshot interval as the first
argument. After it and rsnapshot are configured, simply replacing any
instance of 'rsnapshot' in your crontab with 'cryptshot.sh' should do the
job.

    $ cryptshot.sh daily

See source for configuration.


backitup.sh
-----------

Perform a backup if a certain amount of time has passed.

This script performs a backup of a user-specified directory using a
user-specified backup command. If the backup command exits successfully (with
an exit code of zero) the current timestamp is saved in a file. Every time
the script runs, it checks the timestamp stored in the file. If the timestamp
is greater than a user-specified period, the backup command is executed.

I want to perform daily, remote backups on a laptop. I only want the backup
to attempt to execute if I am logged in and online, so I don't want to run it
as a normal cron job. Further, the backup is of a filesystem. I only want the
backup to execute if the filesystem is mounted.

The idea is that this script could be called every time you login. Even if
you login numerous times per day, backups will only be executed once per day
(assuming that the period you specified was one day). If you use a network
manager, such as wicd, you could have this script execute every time you
connect to a network. Again, backups will only be executed once per period,
even if you connect to the network more frequently.

See source for configuration.


tarsnapper.py
------------

A Python script to manage [Tarsnap](https://www.tarsnap.com/) archives.

Tarsnapper will use `tarsnap` to backup any specified files or directories. It
can create one archive or many. The archive is named by the user, and can have
an optional suffix (such as the current date) automatically added to the name.

That's dandy, but the real reason that Tarsnapper exists is to delete old
archives. Give it a maximum age, such as 7d (7 days) or 8w (8 weeks), and any
archives older than that age will be deleted.

Save your picodollars! Don't waste disk-space.

See source for configuration.


db-backup.py
------------

Backup databases! See source for configuration and usage.

I like to use email for remote backups. It's cheap (a free Gmail account
provides 7+ gigs of storage) and one-way: if an attacker breaks into my
server, he can see what address I'm sending backups to, but is going to
have a difficult time accessing and altering those backups.

But email is sent across the internets in plain text and (in my case) I do
not control the destination server. Thus, the backups must be encrypted.
I use GPG's symmetric encryption for this. It gets the job done and is
simpler than asymmetric encryption with keys.


file-backup.sh
--------------

Backup files in a directory! See source for configuration.

Nothing fancy here.


clean.sh
--------

A simple Bash script to remove files older than a given age.
