#! /usr/bin/env python
#
# A simple python script to backup directories (or files!).
#
# Author:   Pig Monkey (pm@pig-monkey.com)
# Website:  https://github.com/pigmonkey/backups
#
##############################################################################

import os
import sys
import subprocess
from datetime import date

# Define directories to backup
# Example:
#   DIRECTORIES = {
#       'mybackup' : os.path.expanduser('~/veryimportant'),
#       'myotherbackup' : '/var/www/htdocs'
#   }
DIRECTORIES = {
    'peter' : os.path.expanduser('~/webapps/django/peter'),
    'rainstrain' : os.path.expanduser('~/webapps/rainstrain_wp')
}

# Set the directory to backup to.
DIR = os.path.expanduser('~/backup/')

# Where is tar?
TAR = '/bin/tar'

# Get today's date.
TODAY = date.today()

# Stop defining variables here
##############################################################################

# Create the backup directory if it doesn't exist
if not os.path.exists(DIR):
    try:
        os.makedirs(DIR)
    except OSError:
        print 'Could not create directory %s' % (DIR)
        sys.exit(1)
    else:
        print 'Backup directory %s created!' % (DIR)


# Test directory permissions
try:
    test = open(DIR + '.test', 'wb')
except IOError:
    print 'Cannot write to %s' % (DIR)
    sys.exit(1)

# Perform the backups
for name, directory in DIRECTORIES.iteritems():

    filename = DIR + name + '.' + str(TODAY) + '.tar.bz'
    
    print 'Backing up %s to %s' % (name, filename)

    # Get absolute path of directory
    directory = os.path.abspath(directory)

    # Confirm that the requested directory exists
    if not os.path.exists(directory):
        print '\tDirectory %s does not exist' % (directory)
        continue

    # Get parent directory and confirm its existence
    parent_dir = os.path.abspath(os.path.join(directory, os.path.pardir))
    if not os.path.exists(parent_dir):
        print '\tParent directory %s does not exist' % (parent_dir)
        continue

    # Get the relative path from the parent directory
    child_dir = os.path.split(directory)[-1]
    
    # Change to parent directory
    os.chdir(parent_dir)

    try:
        p = subprocess.check_call([TAR, 'cjf', filename, child_dir])
    except OSError:
        print '\tCould not find %s' % (TAR)
        continue
    except subprocess.CalledProcessError:
        print '\t%s returned non-zero status' % (TAR)
        continue
    else:
        print '\tSuccess!'
