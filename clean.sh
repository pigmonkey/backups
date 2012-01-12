#!/usr/bin/env bash
#
# A simple Bash script to remove files older than a given age.
#
# Specify the directories to search and the age of the files. The script will
# then remove all files in that directory older than the given age.
#
# Author:  Pig Monkey (pm@pig-monkey.com)
# Website: https://github.com/pigmonkey/backups
#
###############################################################################

# Set the directories to search. Example:
#   DIRECTORIES[0]="$HOME/backup"
#   DIRECTORIES[1]="$HOME/projects/myproject/logs"
DIRECTORIES[0]="$HOME/backup"

# The age given in days.
AGE=60

# Stop defining variables here.
###############################################################################

for i in "${DIRECTORIES[@]}"
do
    /usr/bin/find $i -type f -mtime +$AGE -exec /bin/rm -v {} \;
done
