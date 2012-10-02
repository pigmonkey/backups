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
import argparse

# Set the location of the config file. This file is optional. If used, it
# will overwrite the options below. The file should be in the INI-style format
# parsable by the ConfigParser module. If the specified file does not exist,
# Tarsnapper will simply continue. Note that the os module is available.
CONFIG = os.path.expanduser('~/.tarsnapper.conf')

# Set the location of the Tarsnap binary.
TARSNAP = '/usr/local/bin/tarsnap'

# Specify a dictionary of archives. The key should be the base name of the
# archive. The value should be a string of the files or directories that the
# archive should contain. Multiple files or directories may be contained within
# a single string value. For example:
#     BACKUPS = {'home': '/home',
#                'logs': '/var/logs /srv/mywebsite.com/logs'}
BACKUPS = {'home': '/home'}

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

# Specify a Tarsnap key-file to be used when deleting archives. This is useful
# if you have a read/write key specified in your tarsnap.conf file as the
# default key to be used when creating archives, but you have a separate
# delete-only key that should be used when deleting archives.
#DELETE_KEY = os.path.expanduser('~/.tarsnap.del.key')
DELETE_KEY = ''

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


def prepare_archive(archive, contents):
    """
    Prepare an archive by building the archive name and checking permissions,
    if requested. Return the full name of the archive.
    """
    # Check the permissions.
    if PERMISSION_CHECK:
        for item in contents.strip().split():
            # If the permission check fails, return false.
            if os.access(item, os.R_OK) is False:
                permissions = False
                return False

    # Build the archive name by adding the suffix to the base.
    if SUFFIX:
        archive_name = '%s.%s' % (archive, SUFFIX)
    else:
        archive_name = archive

    return archive_name


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
    if DELETE_KEY:
        args.extend(['--keyfile', DELETE_KEY])
    for archive in archive_list:
        args.extend(['-f', archive])
    return execute(TARSNAP, args)


def list_archives():
    """Return a list of available Tarsnap archives."""
    archives = execute(TARSNAP, ['--list-archives', '-v'])
    if archives:
        return archives.strip().split('\n')

    return False

# Set available command-line arguments.
parser = argparse.ArgumentParser(description='A Python script to manage \
                                              Tarsnap archives.')
parser.add_argument('-c', '--config', action='store', dest='config',
                    help='Specify the configuration file to use.')
parser.add_argument('-a', '--archive', action='store', dest='archive',
                    help='Specify a named archive to execute.')
parser.add_argument('-r', '--remove', action='store_const', const=True,
                    help='Remove archives old archives and exit.')
# Parse command-line arguments.
args = parser.parse_args()

# Read the user's configuration file.
config = ConfigParser.RawConfigParser()
if args.config:
    CONFIG = args.config
config.read(CONFIG)
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
    if config.has_option('Settings', 'delete_key'):
        DELETE_KEY = config.get('Settings', 'delete_key')
# Get any archives defined in the config file.
if config.has_section('Archives'):
    BACKUPS = {}
    for name in config.options('Archives'):
        BACKUPS[name] = config.get('Archives', name)

# If the user did not request deletion only, perform the backups.
if not args.remove:
    # If the user specified a single archive, only execute that one.
    if args.archive:
        try:
            archive_name = prepare_archive(args.archive, BACKUPS[args.archive])
        except KeyError:
            print 'Archive %s is not configured.' % args.archive
            sys.exit(2)
        else:
            create_archive(archive_name, BACKUPS[args.archive])
    # If the user did not specify a single archive, execute all of them.
    else:
        for archive, contents in BACKUPS.items():
            archive_name = prepare_archive(archive, contents)
            if archive_name:
                create_archive(archive_name, contents)

# Look for any old backups to delete, if requested.
if MAXIMUM_AGE:
    now = datetime.datetime.now()
    maximum_timedelta = convert_to_timedelta(MAXIMUM_AGE)
    # Create an empty list to hold the aged archives.
    aged = []
    # For each archive, if the difference between the current date and the
    # archive date is greater than the maximum allowed age, add it to the list
    # of archives to be deleted.
    archives = list_archives()
    if archives:
        for archive in archives:
            archive = archive.strip().partition('\t')
            name =  archive[0]
            date = datetime.datetime.strptime(archive[-1], '%Y-%m-%d %H:%M:%S')
            if (now - date) > maximum_timedelta:
                aged.append(name)
    # Delete any aged archives.
    if aged:
        delete_archives(aged)
