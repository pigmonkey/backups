#!/bin/bash
#
# Perform a backup if a certain amount of time has passed.
#
# This script performs a backup of a user-specified directory using a
# user-specified backup command. If the backup command exits successfully (with
# an exit code of zero) the current timestamp is saved in a file. Every time
# the script runs, it checks the timestamp stored in the file. If the timestamp
# is greater than a user-specified period, the backup command is executed.
#
# I want to perform daily, remote backups on a laptop. I only want the backup
# to attempt to execute if I am logged in and online, so I don't want to run it
# as a normal cron job. Further, the backup is of a filesystem. I only want the
# backup to execute if the filesystem is mounted.
#
# The idea is that this script could be called every time you login. Even if
# you login numerous times per day, backups will only be executed once per day
# (assuming that the period you specified was one day). If you use a network
# manager, such as wicd, you could have this script execute every time you
# connect to a network. Again, backups will only be executed once per period,
# even if you connect to the network more frequently.
#
#
# Hey yo but wait, back it up, hup, easy back it up
#
#
# Author:   Pig Monkey (pm@pig-monkey.com)
# Website:  https://github.com/pigmonkey/backups
#
###############################################################################

# Define the directory to be backed up.
DIRECTORY="$HOME/work"

# Define the file that will hold the timestamp of the last successful backup.
# It is recommended that this file be *inside* the directory to be backed up.
LASTRUN="$DIRECTORY/.lastrun"

# Define the backup command.
BACKUP="$HOME/bin/tarsnapper.py"

# Define the command to be executed if the file which holds the time of the
# previous backup does not exist. The default behaviour here is to simply
# create the file, which will then cause the backup to be executed. If the
# directory you specified above is a mount point, the file not existing may
# indicate that the filesystem is not mounted. In that case, you would place
# your mount command in this string. If you want the script to exit when the
# file does not exist, simply set this to a blank string.
NOFILE="touch $LASTRUN"

# Define the period, in seconds, for backups to attempt to execute.
# Hourly:   3600
# Daily:    86400
# Weekly:   604800
# The period may also be set to the string 'DAILY', 'WEEKLY' or 'MONTHLY'.
# Note that this will result in behaviour that is different from setting the
# period to the equivalent seconds.
PERIOD='DAILY'

# End configuration here.
###############################################################################

backup() {
    # Execute the backup.
    echo 'Executing backup...'
    $BACKUP
    # If the backup was succesful, store the current time.
    if [ $? -eq 0 ]; then
        echo 'Backup completed.'
        date $timeformat > "$LASTRUN"
    else
        echo 'Backup failed.'
    fi
    exit
}

# Set the format of the time string to store.
if [ $PERIOD == 'DAILY' ]; then
    timeformat='+%Y%m%d'
elif [ $PERIOD == 'WEEKLY' ]; then
    timeformat='+%G-W%W'
elif [ $PERIOD == 'MONTHLY' ]; then
    timeformat='+%Y%m'
else
    timeformat='+%s'
fi

# If the file does not exist, perform the user requested action. If no action
# was specified, exit.
if [ ! -e "$LASTRUN" ]; then
    if [ -n "$NOFILE" ]; then
        $NOFILE
    else
        exit
    fi
fi

# If the file exists and is not empty, get the timestamp contained within it.
if [ -s "$LASTRUN" ]; then
    timestamp=$(eval cat \$LASTRUN)

    # If the backup period is daily, weekly or monthly, perform the backup if
    # the stored timestamp is not equal to the current date in the same format.
    if [ $PERIOD == 'DAILY' -o $PERIOD == 'WEEKLY' -o $PERIOD == 'MONTHLY' ]; then
        if [ $timestamp != `date $timeformat` ]; then
            backup
        else
            echo "Already backed up once for period $PERIOD. Exiting."
            exit
        fi

    # If the backup period is not daily, perform the backup if the difference
    # between the stored timestamp and the current time is greater than the
    # defined period.
    else
        diff=$(( `date $timeformat` - $timestamp))
        if [ "$diff" -gt "$PERIOD" ]; then
            backup
        else
            echo "Backed up less than $PERIOD seconds ago. Exiting."
            exit
        fi
    fi
fi

# If the file exists but is empty, the script has never been run before.
# Execute the backup.
if [ -e "$LASTRUN" ]; then
    backup
fi
