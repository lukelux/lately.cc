#!/usr/bin/python

import re
import os
import sys
from jinja2 import Template, Environment, FileSystemLoader
 
def setup_appdirs(userinput):
  basepath = userinput['basepath']
  if not os.path.exists(basepath) or not os.path.isdir(basepath):
    print "\n%s does not seem to be a valid directory" % basepath
    print "Exiting...\n"
    sys.exit(1)
 
  print "[+] Checking to see if valid app directory exists"

  required_dirs = [ '_posts', '_layouts' ]
  for d in required_dirs:
    if not os.path.exists("%s/%s" % (basepath,d)) or not os.path.isdir("%s/%s" % (basepath,d)):
      print "\n%s does not seem to be a jekyll instance" % basepath
      print "Please try creating with:"
      print "\n  jekyll new %s\n" % basepath
      sys.exit(1) 
  
  print "[+] Checking to see if app directory is Jekyll-enabled"

def generate_config(userinput):
  PATH = os.path.dirname(os.path.abspath(__file__))
  TEMPLATE_ENVIRONMENT = Environment(
    autoescape=False,
    loader=FileSystemLoader(os.path.join(PATH, 'templates')),
    trim_blocks=False)

  t = TEMPLATE_ENVIRONMENT.get_template('config.template')

  f = open("listener/config.ini", "w")
  f.write(t.render(
    access_token=userinput["access_token"], 
    basepath=userinput["basepath"]
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

  return None


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
      "regex" : "^[a-zA-z0-9]+$"
    },
    {
      "key"   : "basepath",
      "param" : "Absolute path to Jekyll source directory",
      "regex" : "/(.+)$"
    }
  ]

  userinput = {}
  for desc in inputs:
    answer = get_user_input(desc)
    if answer is None:
      print "\nCould not get a valid answer, exiting ..."
      sys.exit(1)
    userinput[desc['key']] = answer

  print ""

  generate_config(userinput)
  setup_appdirs(userinput)

  if not os.path.exists("%s/img" % userinput['basepath']):
    os.makedirs("%s/img" % userinput['basepath'])
  print "[+] Generated photo upload directory %s/img" % userinput['basepath']
  print "\nSetup is complete!\n"
  print "start lately.cc by:"
  print "\n  cd listener"
  print "  nohup ./lately.py &\n" 

if __name__ == "__main__":
  main()


