#!/bin/bash
#
# Open and mount a LUKS volume before performing a backup with rsnapshot.
#
# This script first checks to see if a volume with the given UUID exists.
# If the volume is found, it is treated as a LUKS volume and decrypted with
# the given key file, after which it is mounted. The script then runs
# rsnapshot. After the backup is complete, the volume is unmounted and the
# LUKS mapping is removed. Optionally, the mount point can be deleted to
# complete the clean-up.
#
# This provides for a way to achieve encrypted backups to an external drive
# with a backup tool that does not inherently provide encryption. It can
# easily be modified to execute a backup program other than rsnapshot. Since
# the first step taken is to check if the given volume exists, it is
# appropriate for situations where the external backup volume is not always
# available to the machine (such as a USB backup drive and a laptop).
#
# The script should be called with the rsnapshot interval as the first
# argument. After it and rsnapshot are configured, simply replacing any
# instance of 'rsnapshot' in your crontab with 'cryptshot.sh' should do the
# job.
#
# Author:   Pig Monkey (pm@pig-monkey.com)
# Website:  https://github.com/pigmonkey/backups
#
###############################################################################

# Define the UUID of the backup volume.
UUID=""

# Define the location of the LUKS key file.
KEYFILE=""

# Define the mount point for the backup volume.
# This will be created if it does not already exist.
MOUNTPOINT="/mnt/$UUID"

# Any non-zero value here will caused the mount point to be deleted after the
# volume is unmounted.
REMOVEMOUNT=1

# Define the location of rsnapshot.
RSNAPSHOT="/usr/bin/rsnapshot"

# End configuration here.
###############################################################################

# Exit if no volume is specified.
if [ "$UUID" = "" ]; then
    echo 'No volume specified.'
    exit
fi

# Exit if no key file is specified.
if [ "$KEYFILE" = "" ]; then
    echo 'No key file specified.'
    exit
fi

# Exit if no mount point is specified.
if [ "$MOUNTPOINT" = "" ]; then
    echo 'No mount point specified.'
    exit
fi

# Exit if no interval was specified.
if [ "$1" = "" ]; then
    echo "No interval specified."
    exit
fi

# If the mount point does not exist, create it.
if [ ! -d "$MOUNTPOINT" ]; then
    mkdir $MOUNTPOINT
    # Exit if the mount point was not created.
    if [ $? -ne 0 ]; then
        echo "Failed to create mount point."
        exit
    fi
fi

# Build the reference to the volume.
volume="/dev/disk/by-uuid/$UUID"

# Create a unique name for the LUKS mapping.
name="crypt-$UUID"

# Continue if the volume exists.
if [ -e $volume ];
then
    # Attempt to open the LUKS volume.
    cryptsetup luksOpen --key-file $KEYFILE $volume $name
    # If the volume was decrypted, mount it. 
    if [ $? -eq 0 ];
    then
        mount /dev/mapper/$name $MOUNTPOINT
        # If the volume was mounted, run the backup.
        if [ $? -eq 0 ];
        then
            $RSNAPSHOT $1
            # Unmount the volume
            umount $MOUNTPOINT
            # If the volume was unmounted and the user has requested that the
            # mount point be removed, remove it.
            if [ $? -eq 0 -a $REMOVEMOUNT -ne 0 ]; then
                rmdir $MOUNTPOINT
            fi
        else
            echo "Failed to mount $volume at $MOUNTPOINT."
        fi
        # Close the LUKS volume.
        cryptsetup luksClose $name
    else
        echo "Failed to open $volume with key $KEYFILE."
    fi
else
    echo "Volume $UUID not found."
fi
