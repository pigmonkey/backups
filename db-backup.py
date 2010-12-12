#! /usr/bin/env python
#
# A simply python scrip to backup databases.
#
# Backups are stored in the given directory. A GPG symmetrically encrypted
# tar of the backup and a hash of the backup are emailed to the given
# addresses via SMTP.
#
# Currently supported databases:
#       - MySQL
#       - PostgreSQL
#
# Run with -h or --help flag to see command line options
#   (Ex: db-backup.py -h)
#
# Requires Python 2.5 or greater.
#
# Author:   Pig Monkey (pm@pig-monkey.com)
# Website:  https://github.com/pigmonkey/backups
#
##############################################################################

from datetime import date
import subprocess
import sys
import os
import getopt
from smtplib import SMTP
from smtplib import SMTP_SSL
from email.MIMEMultipart import MIMEMultipart
from email.MIMEBase import MIMEBase
from email import Encoders
from email.Utils import COMMASPACE

# Define a dictionary of databases to backup.
# Example:
#   DATABASES = {
#        'mydatabase' : {
#            'type' : 'mysql',
#            'database_name' : 'thedatabasename'
#            'username' : 'myuser',
#            'password' : 'secret',
#            'host' : 'localhost'
#            'key' : 'my_long_passphrase'
#            'send_to' : ['backup@mydomain.tld']
#        },
#    }

# Set the backup directory.
DIR = os.path.expanduser('~/backup/')

# Define where the PostgreSQL Password File should be.
# This file is used to store login information for databases.
# If the file does not exist, the script will create it.
#
# See: http://www.postgresql.org/docs/8.1/interactive/libpq-pgpass.html
POSTGRESQL_FILE = os.path.expanduser('~/.pgpass')

# Set locations of programs.
# OPENSSL may be set to False if you don't want to generate a hash
MYSQLDUMP = '/usr/bin/mysqldump'
PG_DUMP = '/usr/bin/pg_dump'
OPENSSL = '/usr/bin/openssl'
TAR = '/bin/tar'
GPG = '/usr/bin/gpg'

# If True, backups will be encrypted and emailed.
# Note that this can be overridden on the command line with the -m flag
MAIL = True

# Define mail options.
MAIL_SSL = True
FROM = 'user@domain.tld'
SMTP_SERVER = 'mail.domain.tld'
SMTP_USER = 'user'
SMTP_PASS = 'myawesomepassword'

# Set which hash algorithm to use.
# For options, see '$ openssl dgst -h'
HASH = 'sha512'

# Get today's date.
TODAY = date.today()

# Stop defining variables here
##############################################################################

def usage():
    print '''Backs up databases. See source for configuration and further help.

    Options:
        -d, --database NAME # Backup database of NAME.
                            # (Must be defined in the DATABASES dictionary.)
        -m, --nomail        # Do not email backup.
                            # (Overrides MAIL variable in configuration.)
        -f, --directory DIR # Uses DIR as destination for backups.
                            # (Overrides DIR in configuration.)
        -h, --help          # Displays this help list!
    '''

# Get any flags from the user
try:
    opts, args = getopt.getopt(sys.argv[1:], "hd:mf:",
        ["help", "database=", "nomail", "directory="])
except getopt.GetoptError:
    usage()
    sys.exit(2)
for opt, arg in opts:
    if opt in ("-h", "--help"):
        usage()
        sys.exit()
    elif opt in ("-d", "--database"):
        if arg in DATABASES:
            DATABASES = {arg: DATABASES[arg]}
        else:
            print '%s is not defined!' % (arg)
            sys.exit(1)
    elif opt in ("-m", "--nomail"):
        MAIL = False
    elif opt in ("-f", "--directory"):
        DIR = arg

# Create the backup directory if it doesn't exist
if not os.path.exists(DIR):
    try:
        print 'Creating directory %s...' % (DIR)
        os.makedirs(DIR)
    except OSError:
        print 'Could not create directory %s' % (DIR)
        sys.exit(1)

# Change the directory
os.chdir(DIR)

# Test directory permissions
try:
    test = open('.test', 'wb')
except IOError:
    print 'Cannot write to %s' % (DIR)
    sys.exit(1)

# Perform the backups
for name, database in DATABASES.iteritems():
    filename = name + '.' + str(TODAY)

    backup_file = filename + '.' + database['type']
    checksum_file = backup_file + '.' + HASH
    tar_file = filename + '.tar.bz'
    crypt_file = tar_file + '.gpg'

    print 'Backing up %s' % (name)

    # Backup the database
    if database['type'] == 'mysql':
        backup = open(backup_file, 'wb')

        try:
            p = subprocess.check_call([MYSQLDUMP, '-u', database['username'],
                '-p' + database['password'], '-h', database['host'],
                database['database_name']], stdout=backup)
        except OSError:
            os.remove(backup_file)
            print '\tCould not find %s' % (MYSQLDUMP)
            continue
        except subprocess.CalledProcessError:
            os.remove(backup_file)
            print '\t%s returned non-zero status' % (MYSQLDUMP)
            continue
        finally:
            backup.close()

    if database['type'] == 'postgresql':
        pgpass = '*:*:' + database['database_name'] + ':' + database['username'] + ':' + database['password'] + '\n'

        # If the file exists, check if the database is already in the file
        if os.path.isfile(POSTGRESQL_FILE):
            match = False
            f = open(POSTGRESQL_FILE, 'r')

            for line in f:
                search = line.find(':' + database['database_name'] + ':')
                if search != -1:
                    match = True
            f.close()

            # If the database was not found in the file, add it.
            if match == False:
                f = open(POSTGRESQL_FILE, 'a')
                f.write(pgpass)
                f.close()

        # If the file does not exist, create it and add the line
        else:
            f = open(POSTGRESQL_FILE, 'w')
            f.write(pgpass)
            f.close()
            os.chmod(POSTGRESQL_FILE, 0600)     # Permissions must be 0600

        try:
            p = subprocess.check_call([PG_DUMP, '-h', database['host'], '-U',
                database['username'], database['database_name'], '-f',
                backup_file])
        except OSError:
            print '\tCould not find %s' % (PG_DUMP)
            continue
        except subprocess.CalledProcessError:
            print '\t%s returned non-zero status' % (PG_DUMP)
            continue

        # Make sure backup file was created
        try:
            f = open(backup_file, 'rb')
        except IOError:
            print '\tBackup failed!'
            continue
        finally:
            f.close()


    # Check if backup file is empty.
    if os.stat(backup_file).st_size == 0:
        print '\tBackup failed!'
        os.remove(backup_file)
        continue

    # Generate the hash
    if OPENSSL:
        try:
            p = subprocess.check_call([OPENSSL, 'dgst', '-' + HASH, '-out',
                checksum_file, backup_file])
        except OSError:
            os.remove(backup_file)
            print '\tCould not find %s' % (OPENSSL)
            continue
        except subprocess.CalledProcessError:
            print '\t%s returned non-zero status' % (OPENSSL)
            continue

        # Make sure hash file was created
        try:
            f = open(checksum_file, 'rb')
        except IOError:
            print '\tBackup failed!'
            continue
        finally:
            f.close()

    print '\tSuccess!'

    if MAIL:

        print '\tEmailing...'

        # Compress the backup and hash file
        try:
            p = subprocess.check_call([TAR, 'cjf', tar_file, backup_file,
                checksum_file])
        except OSError:
            print '\t\tCould not find %s' % (TAR)
            continue
        except subprocess.CalledProcessError:
            print '\t%s returned non-zero status' % (TAR)
            continue

        # Encrypt the compressed file
        try:
            p = subprocess.check_call([GPG, '-cao', crypt_file,'--passphrase',
                database['key'], tar_file])
        except OSError:
            print '\t\tCould not find %s' % (GPG)
            print '\t\tEmail failed'
            continue
        except subprocess.CalledProcessError:
            print '\t%s returned non-zero status' % (GPG)
            continue

        # Create the email message
        msg = MIMEMultipart()
        msg['From'] = FROM
        msg['To'] = COMMASPACE.join(database['send_to'])
        msg['Subject'] = name.capitalize() + ' Database Backup: ' + str(TODAY)

        # Attach the file
        part = MIMEBase('application', "pgp-encrypted")
        part.set_payload( open(crypt_file, 'rb').read() )
        Encoders.encode_base64(part)
        part.add_header('Content-Disposition', 'attachment; filename="%s"'
            %crypt_file
        )
        msg.attach(part)

        # Send the mail
        if MAIL_SSL:
            s = SMTP_SSL()
        else:
            s = SMTP()
        s.connect(SMTP_SERVER)
        s.login(SMTP_USER, SMTP_PASS)
        s.sendmail(FROM, database['send_to'], msg.as_string())
        s.quit()

        print '\tMessage sent!'

        # Clean up
        os.remove(crypt_file)
        os.remove(tar_file)
