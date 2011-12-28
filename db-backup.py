#! /usr/bin/env python
#
# A simple python script to backup databases.
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
# Requires Python 2.6 or greater.
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

# Initialize database backup variables.
# These can be set here, but will be overriden by command-line options.
TYPE = None
DATABASE = None
HOST = None
USER = None
PASSWORD = None
DIRECTORY = None
MAIL = None
KEY = None

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

# Define mail server options.
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
        -t, --type TYPE         # The type of database (MySQL or PostgreSQL).
        -d, --database NAME     # The name of the database.
        -h, --host HOST         # The database host. (Optional)
                                # If no host is provided, localhost will be assumed.
        -u, --user USER         # The database username. (Optional)
                                # If no username is provided, the name of the database will be used instead.
        -p, --password PASS     # The database password.
        -f, --directory DIR     # The destination directory.
        -m, --mail EMAIL        # The email address to send the backup to. (Optional)
        -k, --key KEY           # The encryption key. (Required if --mail option is used.)
        -h, --help              # Displays this help list.
    '''

# Get any flags from the user
try:
    opts, args = getopt.getopt(sys.argv[1:], "t:d:h:u:p:f:m:k:h",
        ["type=", "database=", "host=", "user=", "password=", "directory=",
        "mail=", "key=", "help"])
except getopt.GetoptError:
    usage()
    sys.exit(2)
for opt, arg in opts:
    if opt in ("-h", "--help"):
        usage()
        sys.exit()
    elif opt in ("-t", "--type"):
        TYPE = arg.lower()
    elif opt in ("-d", "--database"):
        DATABASE = arg
    elif opt in ("-h", "--host"):
        HOST = arg
    elif opt in ("-u", "--user"):
        USER = arg
    elif opt in ("-p", "--password"):
        PASSWORD = arg
    elif opt in ("-f", "--directory"):
        DIRECTORY = arg
    elif opt in ("-m", "--mail"):
        MAIL = arg.split(',')
    elif opt in ("-k", "--key"):
        KEY = arg

# Define the supported database types
SUPPORTED_DATABASES = ('mysql', 'postgresql',)

# Check to make sure all required options have been given.
if not DATABASE:
    print 'No database specified.'
    usage()
    sys.exit(2)
if not TYPE:
    print 'No database type specified.'
    usage()
    sys.exit(2)
if not DIRECTORY:
    print 'No backup directory specified.'
    usage()
    sys.exit(2)
if MAIL and not KEY:
    print 'No encryption key specified.'
    usage()
    sys.exit(2)

# Make sure the specified database type is specified.
if TYPE not in SUPPORTED_DATABASES:
    print 'Unsupported database type specified. Currently only MySQL and PostgreSQL are supported.'
    sys.exit(2)

# If a database user was not specified, assume that the name of the database is
# also the name of the user.
if not USER:
    USER = DATABASE
    print 'No database user specified. Assuming that the name of the database is also the username.'

# If a database hostname was not specified, assume that it is localhost.
if not HOST:
    HOST = 'localhost'
    print 'No hostname specified. Assuming that the host is localhost.'

# Create the backup directory if it doesn't exist
if not os.path.exists(DIRECTORY):
    try:
        print 'Creating directory %s...' % (DIRECTORY)
        os.makedirs(DIRECTORY)
    except OSError:
        print 'Could not create directory %s' % (DIRECTORY)
        sys.exit(1)

# If the type is MySQL, a password is required.
if not PASSWORD and TYPE == 'mysql':
    print 'No database password specified.'
    usage()
    sys.exit(2)

# Change the directory
os.chdir(DIRECTORY)

# Test directory permissions
try:
    test = open('.test', 'wb')
except IOError:
    print 'Cannot write to %s' % (DIRECTORY)
    sys.exit(1)
else:
    test.close()
    os.remove('.test')
    
# Perform the backups
filename = DATABASE + '.' + str(TODAY)

backup_file = filename + '.' + TYPE
checksum_file = backup_file + '.' + HASH
tar_file = filename + '.tar.bz'
crypt_file = tar_file + '.gpg'

# Backup the MySQL database.
if TYPE == 'mysql':
    backup = open(backup_file, 'wb')

    try:
        p = subprocess.check_call([MYSQLDUMP, '-u', USER, '-p' + PASSWORD,
                                  '-h', HOST, DATABASE], stdout=backup)
    except OSError:
        os.remove(backup_file)
        print 'Could not find %s' % (MYSQLDUMP)
    except subprocess.CalledProcessError:
        os.remove(backup_file)
        print '%s returned non-zero status' % (MYSQLDUMP)
    else:
        backup.close()

# Backup the PostgreSQL database.
if TYPE == 'postgresql':
    # Check for the current database in the PostgreSQL Password File.
    try:
        # If the file exists, open it.
        f = open(POSTGRESQL_FILE, 'r')
    except:
        # If the file does not exist, make sure we were passed a password.
        try:
            pgpass = '*:*:' + DATABASE + ':' + USER + ':' + PASSWORD + '\n'
        except TypeError:
            print 'No database password specified.'
            sys.exit(2)
        # Create the file and add the current database.
        f = open(POSTGRESQL_FILE, 'w')
        f.write(pgpass)
        f.close()
        # Permissions must be 0600.
        os.chmod(POSTGRESQL_FILE, 0600)
    else:
        # Check if the current database is in the file.
        match = False
        for line in f:
            search = line.find(':' + DATABASE + ':')
            if search != -1:
                match = True
                break
        # If the database is not in the file, add it.
        if match is False:
            # Close the file so that we can reopen it for appending.
            f.close()
            # Make sure we were passed the password.
            try:
                pgpass = '*:*:' + DATABASE + ':' + USER + ':' + PASSWORD + '\n'
            except TypeError:
                print 'No database password specified.'
                sys.exit(2)
            f = open(POSTGRESQL_FILE, 'a')
            f.write(pgpass)
            f.close()

    try:
        p = subprocess.check_call([PG_DUMP, '-h', HOST, '-U', USER, DATABASE,
                                  '-f', backup_file])
    except OSError:
        print 'Could not find %s' % (PG_DUMP)
    except subprocess.CalledProcessError:
        print '%s returned non-zero status' % (PG_DUMP)

# Make sure backup file was created.
try:
    f = open(backup_file, 'rb')
except IOError:
    print 'Backup failed!'
    sys.exit(1)
else:
    f.close()

# Check if backup file is empty.
if os.stat(backup_file).st_size == 0:
    print 'Backup failed!'
    os.remove(backup_file)
    sys.exit(1)

# Generate the hash, if requested.
if OPENSSL:
    try:
        p = subprocess.check_call([OPENSSL, 'dgst', '-' + HASH, '-out',
            checksum_file, backup_file])
    except OSError:
        os.remove(backup_file)
        print '\tCould not find %s' % (OPENSSL)
    except subprocess.CalledProcessError:
        print '\t%s returned non-zero status' % (OPENSSL)

    # Make sure hash file was created.
    try:
        f = open(checksum_file, 'rb')
    except IOError:
        print '\tBackup failed!'
    else:
        f.close()

print 'Backup successful!'

if MAIL:
    print 'Emailing...'
    # Compress the backup and hash file
    try:
        p = subprocess.check_call([TAR, 'cjf', tar_file, backup_file,
            checksum_file])
    except OSError:
        print '\tCould not find %s' % (TAR)
    except subprocess.CalledProcessError:
        print '\t%s returned non-zero status' % (TAR)

    # Encrypt the compressed file
    try:
        p = subprocess.check_call([GPG, '-cao', crypt_file,'--passphrase',
            KEY, tar_file])
    except OSError:
        print '\tCould not find %s' % (GPG)
        print '\tEmail failed'
    except subprocess.CalledProcessError:
        print '\t%s returned non-zero status' % (GPG)

    # Create the email message
    msg = MIMEMultipart()
    msg['From'] = FROM
    msg['To'] = ', '.join(MAIL)
    msg['Subject'] = DATABASE + ' Database Backup: ' + str(TODAY)

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
    try:
        s.connect(SMTP_SERVER)
    except:
        print '\tCould not connect to specified SMTP server.'
        os.remove(crypt_file)
        os.remove(tar_file)
        sys.exit(1)
    s.login(SMTP_USER, SMTP_PASS)
    s.sendmail(FROM, MAIL, msg.as_string())
    s.quit()

    print '\tMessage sent!'

    # Clean up
    os.remove(crypt_file)
    os.remove(tar_file)
