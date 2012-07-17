#! /usr/bin/env python
#
# A Python script to manage Tarsnap archives.
#
# Tarsnapper will use tarsnap to backup any specified files or directories. It
# can create one archive or many. The archive is named by the user, and can
# have an optional suffix (such as the current date) automatically added to the
# name.
#
# That's dandy, but the real reason that Tarsnapper exists is to delete old
# archives. Give it a maximum age, such as 7d (7 days) or 8w (8 weeks), and any
# archives older than that age will be deleted.
#
# Save your picodollars! Don't waste disk-space.
#
# Configuration may be completed by editing the variables below, or by creating
# a config file at ~/.tarsnapper.conf. A sample configuration file should have
# been included with this distribution.
#
# Requires Python 2.7 or greater.
#
# Author:   Pig Monkey (pm@pig-monkey.com)
# Website:  https://github.com/pigmonkey/backups
#
# Tarsnap online backup service by Dr. Colin Percival.
# https://www.tarsnap.com/
#
###############################################################################
import datetime
import os
import subprocess
import sys
import ConfigParser

# Set the location of the Tarsnap binary.
TARSNAP = '/usr/local/bin/tarsnap'

# Specify a list of files or directories to be backed up, and the base name of
# the archive. Multiple files or directories may be contained within a single
# archive. Each entry in the list should be a tuple, such as:
#     BACKUPS = [('home', '/home'),
#                ('logs', '/var/logs /srv/mywebsite.com/logs')]
BACKUPS = [('home', '/home')]

# Specify a suffix to append to each archive name. This can be anything
# (or nothing), but each archive name must be unique, so you probably want to
# involve the current time somehow. Note that the datetime module is available.
SUFFIX = datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S')

# Specify the maximum age of an archive. Any archives older than this age will
# be deleted. If you wish to never delete backups, leave this option
# empty. See the convert_to_timedelta docstring for appropriate format.
MAXIMUM_AGE = '4w'

# Tarsnap will begin the archival process before it checks permissions on
# the files or directories specified. Even if it has no access, it will
# still create the archive and result in a few bytes being transferred before
# exiting. The following option, if enabled, will cause the script to check if
# the current user has read access to all of the files and directories given.
# If read access does not exist, the current backup will not be executed. This
# will prevent wasting Tarsnap's time and your picodollars. Note that it does
# not check _inside_ any of the given directories.
PERMISSION_CHECK = True

# End configuration here.
###############################################################################

def convert_to_timedelta(time_val):
    """
    Given a *time_val* (string) such as '5d', returns a timedelta object
    representing the given value (e.g. timedelta(days=5)).  Accepts the
    following '<num><char>' formats:
    
    =========   ======= ===================
    Character   Meaning Example
    =========   ======= ===================
    s           Seconds '60s' -> 60 Seconds
    m           Minutes '5m'  -> 5 Minutes
    h           Hours   '24h' -> 24 Hours
    d           Days    '7d'  -> 7 Days
    w           Weeks   '4w'  -> 4 Weeks
    =========   ======= ===================
    
    Examples::
    
        >>> convert_to_timedelta('4w')
        datetime.timedelta(28)
        >>> convert_to_timedelta('7d')
        datetime.timedelta(7)
        >>> convert_to_timedelta('24h')
        datetime.timedelta(1)
        >>> convert_to_timedelta('60m')
        datetime.timedelta(0, 3600)
        >>> convert_to_timedelta('120s')
        datetime.timedelta(0, 120)

    Created by Dan McDougall.
    http://is.gd/bEwEmz

    Licensed under the Apache License 2.0
    https://www.apache.org/licenses/LICENSE-2.0.html
    """
    num = int(time_val[:-1])
    if time_val.endswith('s'):
        return datetime.timedelta(seconds=num)
    elif time_val.endswith('m'):
        return datetime.timedelta(minutes=num)
    elif time_val.endswith('h'):
        return datetime.timedelta(hours=num)
    elif time_val.endswith('d'):
        return datetime.timedelta(days=num)
    elif time_val.endswith('w'):
        return datetime.timedelta(weeks=num)


def execute(binary, arguments):
    """
    Execute a binary with the given arguments. Complain and exit if any errors
    are raised.
    """
    arguments.insert(0, binary)
    try:
        process = subprocess.check_output(arguments)
    except OSError:
        print 'Could not find %s' % binary
        sys.exit(2)
    except subprocess.CalledProcessError:
        print '%s returned non-zero status' % (binary)
        sys.exit(2)
    else:
        return process

    return False


def create_archive(archive_name, item):
    """Create a new Tarsnap archive of an item, or items."""
    arguments = ['-c', '-f', archive_name]
    # If the archive is to include multiple files or directories, split them
    # out so that they are sent as different items in the list.
    arguments.extend(item.strip().split(' '))
    return execute(TARSNAP, arguments)


def delete_archives(archive_list):
    """Delete a list of tarsnap archives."""
    args = ['--no-print-stats', '-d']
    for archive in archive_list:
        args.extend(['-f', archive])
    return execute(TARSNAP, args)


def list_archives():
    """Return a list of available Tarsnap archives."""
    archives = execute(TARSNAP, ['--list-archives', '-v'])
    if archives:
        return archives.strip().split('\n')

    return False


# Read the user's configuration file.
config = ConfigParser.RawConfigParser()
config.read(os.path.expanduser('~/.tarsnapper.conf'))
# Get any settings defined in the config file.
if config.has_section('Settings'):
    if config.has_option('Settings', 'tarsnap'):
        TARSNAP = config.get('Settings', 'tarsnap')
    if config.has_option('Settings', 'maximum_age'):
        MAXIMUM_AGE = config.get('Settings', 'maximum_age')
    if config.has_option('Settings', 'permission_check'):
        PERMISSION_CHECK = config.getboolean('Settings', 'permission_check')
    if config.has_option('Settings', 'suffix'):
        if config.getboolean('Settings', 'suffix') is False:
            SUFFIX = False
# Get any archives defined in the config file.
if config.has_section('Archives'):
    BACKUPS = []
    for name in config.options('Archives'):
        BACKUPS.append((name, config.get('Archives', name)))

# Perform the backups.
for backup in BACKUPS:
    # Initially assume that the user has the proper permissions to perform the
    # backup, or that the user does not care to check.
    permissions = True
    # Check the permissions, if requested.
    if PERMISSION_CHECK:
        for item in backup[1].strip().split():
            if os.access(item, os.R_OK) is False:
                permissions = False
                break
    if permissions:
        if SUFFIX:
            archive_name = '%s.%s' % (backup[0], SUFFIX)
        else:
            archive_name = backup[0]
        create_archive(archive_name, backup[1])

# Look for any old backups to delete, if requested.
if MAXIMUM_AGE:
    now = datetime.datetime.now()
    maximum_timedelta = convert_to_timedelta(MAXIMUM_AGE)
    # Create an empty list to hold the aged archives.
    aged = []
    # For each archive, if the difference between the current date and the
    # archive date is greater than the maximum allowed age, add it to the list
    # of archives to be deleted.
    for archive in list_archives():
        archive = archive.strip().partition('\t')
        name =  archive[0]
        date = datetime.datetime.strptime(archive[-1], '%Y-%m-%d %H:%M:%S')
        if (now - date) > maximum_timedelta:
            aged.append(name)
    # Delete any aged archives.
    if aged:
        delete_archives(aged)
