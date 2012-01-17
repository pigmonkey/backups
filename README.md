Backups
=======

These are scripts written to perform various backup-related tasks.


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
