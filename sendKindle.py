#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
CLI tool for sending files via email to your Kindle device.
You need to have a working IMAP account.

This script is originally based on:
http://rakesh.fedorapeople.org/misc/pykindle.py (Public Domain)

Author: Kamil Páral <kamil.paral /at/ gmail.com>
'''
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import ConfigParser
import getpass
import optparse
import os
import smtplib
import sys
import traceback
from StringIO import StringIO
from email import encoders
from email.MIMEBase import MIMEBase
from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText
from email.generator import Generator

_version = '2.1'


class SendKindle:
    smtp_server = None
    smtp_port = 0
    smtp_login = None
    user_email = None
    kindle_email = None
    smtp_password = None
    convert = False

    parser = None
    files = []

    conffile = os.path.expanduser('~/.config/sendKindle/sendKindle.cfg')
    sample_conf = '''[Default]
smtp_server = smtp.gmail.com
smtp_port = 465
smtp_login = username
user_email = username@gmail.com
kindle_email = username@free.kindle.com
# optional
smtp_password = password
convert = False'''


    def __init__(self):
        self.parse_args()
        self.read_config()
        self.check_args()


    def create_config(self):
        '''Creates an empty config file from the template if no config file
        exists. Halts program execution in that case. Otherwise nothing
        happens.'''

        try:
            if not os.path.exists(self.conffile):
                # create directory
                parent = os.path.dirname(self.conffile)
                if not os.path.exists(parent):
                    os.makedirs(parent)
                # create file
                f = open(self.conffile, 'w')
                f.write(self.sample_conf)
                f.close()
            else:
                return
        except IOError:
            traceback.print_exc()
            message = ('Error creating a new config file, maybe wrong '
                       'permissions?')
            print >> sys.stderr, message
            sys.exit(4)
        else:
            message = ('A new config file created in: %s\n'
                'Please edit it, provide correct values and run the program '
                'again.' % self.conffile)
            print >> sys.stderr, message
            sys.exit(5)


    def read_config(self):
        '''Parse the config file. Create a new one if needed.'''

        self.create_config()
        config = ConfigParser.SafeConfigParser()
        try:
            if not config.read([self.conffile]):
                raise IOError('%s could not be read' % self.conffile)
            self.smtp_server = config.get('Default', 'smtp_server')
            self.smtp_port = config.getint('Default', 'smtp_port')
            self.smtp_login = config.get('Default', 'smtp_login')
            self.user_email = config.get('Default', 'user_email')
            self.kindle_email = config.get('Default', 'kindle_email')
            if config.has_option('Default', 'smtp_password'):
                # prefer value from cmdline option
                self.smtp_password = (self.smtp_password or
                                      config.get('Default', 'smtp_password') or
                                      getpass.getpass('Password for %s: ' %
                                                            self.user_email))
            if config.has_option('Default', 'convert'):
                # prefer value from cmdline option
                self.convert = (self.convert or
                                config.getboolean('Default', 'convert'))
        except (IOError, ConfigParser.Error, ValueError):
            traceback.print_exc()
            message = ("Your config file could not be read or contains "
                       "invalid values: %s" % self.conffile)
            print >> sys.stderr, message
            sys.exit(3)


    def parse_args(self):
        usage = ('Usage: %prog [options] FILE...\n'
                '  FILE is a file to be sent as an email attachment.')
        description = ('SendKindle will send any number of files via email '
                      'to your Kindle device.')
        parser = optparse.OptionParser(usage=usage, version=_version,
                                       description=description)
        self.parser = parser
        parser.add_option('--password', help=('Use provided password instead '
            'of smtp_password value from your config file. If you provide '
            "neither of these, you'll be asked interactively."))
        parser.add_option('-c', '--convert', action='store_true',
            default=False, help=('Ask Kindle service to convert the documents '
            'to Kindle format (mainly for PDFs) [default: %default]'))
        (options, args) = parser.parse_args()

        self.convert = options.convert
        if options.password:
            self.smtp_password = options.password
        if not args:
            parser.error('No files provided as arguments! See --help.')
        self.files = args


    def check_args(self):
        if not self.smtp_password:
            self.smtp_password = getpass.getpass('Password for %s: '
                                                 % self.user_email)


    def send_mail(self):
        '''Send email with attachments'''

        # create MIME message
        msg = MIMEMultipart()
        msg['From'] = self.user_email
        msg['To'] = self.kindle_email
        msg['Subject'] = 'Convert' if self.convert else 'Sent to Kindle'
        text = 'This email has been automatically sent by SendKindle tool.'
        msg.attach(MIMEText(text))

        # attach files
        for file_path in self.files:
            msg.attach(self.get_attachment(file_path))

        # convert MIME message to string
        fp = StringIO()
        gen = Generator(fp, mangle_from_=False)
        gen.flatten(msg)
        msg = fp.getvalue()

        # send email
        try:
            mail_server = smtplib.SMTP_SSL(host=self.smtp_server,
                                          port=self.smtp_port)
            mail_server.login(self.smtp_login, self.smtp_password)
            mail_server.sendmail(self.user_email, self.kindle_email, msg)
            mail_server.close()
        except smtplib.SMTPException:
            traceback.print_exc()
            message = ('Communication with your SMTP server failed. Maybe '
                       'wrong connection details? Check exception details and '
                       'your config file: %s' % self.conffile)
            print >> sys.stderr, message
            sys.exit(7)

        print('Sent email to %s' % self.kindle_email)


    def get_attachment(self, file_path):
        '''Get file as MIMEBase message'''

        try:
            file_ = open(file_path, 'rb')
            attachment = MIMEBase('application', 'octet-stream')
            attachment.set_payload(file_.read())
            file_.close()
            encoders.encode_base64(attachment)

            attachment.add_header('Content-Disposition', 'attachment',
                                  filename=os.path.basename(file_path))
            return attachment
        except IOError:
            traceback.print_exc()
            message = ('The requested file could not be read. Maybe wrong '
                       'permissions?')
            print >> sys.stderr, message
            sys.exit(6)


def main():
    '''Run the main program'''
    try:
        kindle = SendKindle()
        kindle.send_mail()
    except KeyboardInterrupt:
        print >> sys.stderr, 'Program interrupted, exiting...'
        sys.exit(10)


if __name__ == '__main__':
    main()
