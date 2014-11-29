#!/usr/bin/python

import re
import os
import sys
import shutil
import subprocess
from jinja2 import Template, Environment, FileSystemLoader

def init_required(userinput):
  basedir = userinput['basepath']
  required = [
    ('img/p',      'photo upload'),
    ('_plugins', 'Jekyll plugins'),
    ('data',     'lately metadata'),
    ('log',      'logger')
  ]
  for required_dir in required:
    fullpath = "%s/%s" % (basedir, required_dir[0])
    if not os.path.exists(fullpath):
      os.makedirs(fullpath)
    print "[+] Generated %s directory %s" % (required_dir[1], required_dir[0])

  file_exists_plugin_path = "%s/_plugins/%s" % (basedir, "file_exists.rb")
  shutil.copyfile("contrib/file_exists.rb", file_exists_plugin_path)
  print "[+] Copied file_exists Jekyll plugin"

def generate_config(basepath, sitepath, access_token, jekyllpath):
  PATH = os.path.dirname(os.path.abspath(__file__))
  TEMPLATE_ENVIRONMENT = Environment(
    autoescape=False,
    loader=FileSystemLoader(os.path.join(PATH, 'templates')),
    trim_blocks=False)

  t = TEMPLATE_ENVIRONMENT.get_template('config.template')

  f = open("listener/config.ini", "w")
  f.write(t.render(
    access_token=access_token,
    basepath=basepath,
    sitepath=sitepath,
    jekyllpath=jekyllpath
  ))
  f.close()

  print "[+] Generating configuration ini file"

def get_user_input(desc):
  regex = re.compile(desc['regex'])
  tried = 0
  for tried in range(0,3):
    param = desc['param']
    if tried > 0:
      print "\nInvalid input, please try again"

    token = raw_input("+ Please provide %s: " % param)
    if regex.match(token):
      return token

    if 'default' in desc:
      return desc['default']

  return None

def get_jekyll_path():
  path=os.getenv('PATH')
  for p in path.split(os.path.pathsep):
    filepath=os.path.join(p, 'jekyll')
    if os.path.exists(filepath) and os.access(filepath, os.X_OK):
      return filepath
  return None

def convert_to_abs(path):
  if not os.path.isabs(path):
    path = "%s/%s" % (os.path.dirname(os.path.abspath(__file__)), path)
  return path

def main():
  print "------------------------------------------------------------"
  print " _           _         _         ___       _                "
  print "| |    __ _ | |_  ___ | | _  _  / __| ___ | |_  _  _  _ __  "
  print "| |__ / _` ||  _|/ -_)| || || | \__ \/ -_)|  _|| || || '_ \."
  print "|____|\__,_| \__|\___||_| \_, | |___/\___| \__| \_,_|| .__/ "
  print "                          |__/                       |_|    "
  print "                                                            "
  print "------------------------------------------------------------"
  inputs = [
    {
      "key"   : "access_token",
      "param" : "Dropbox generated access token",
      "regex" : "^[a-zA-z0-9\-]+$"
    },
    {
      "key"     : "basepath",
      "param"   : "path to Jekyll source directory [default: app]",
      "regex"   : "(.+)",
      "default" : "app"
    },
    {
      "key"   : "sitepath",
      "param" : "path to webapp site directory",
      "regex" : "(.+)"
    }
  ]

  print ""
  jekyllpath = get_jekyll_path()
  if jekyllpath is None:
    print "Jekyll is not found. Lately only works with Jekyll."
    print "Please install by:\n"
    print "  gem install jekyll\n"
    sys.exit(1)

  userinput = {}
  for desc in inputs:
    answer = get_user_input(desc)
    if answer is None:
      print "\nCould not get a valid answer, exiting ..."
      sys.exit(1)
    userinput[desc['key']] = answer

  access_token = userinput['access_token']
  basepath     = convert_to_abs(userinput['basepath'])
  sitepath     = convert_to_abs(userinput['sitepath'])

  generate_config(basepath, sitepath, access_token, jekyllpath)

  if not os.path.exists(userinput['basepath']):
    print "[+] Setting up Jekyll app directory"
    subprocess.call([ jekyllpath, 'new', userinput['basepath']])

  init_required(userinput)

  print "\nSetup is complete!\n"
  print "start lately.cc by:"
  print "\n  cd listener"
  print "  nohup ./lately.py &\n"

if __name__ == "__main__":
  main()
