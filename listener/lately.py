#!/usr/bin/python

import sys
import time
import shelve
import logging
import signal, os
import threading
import subprocess

import ConfigParser
import Queue

import dayone
import journal
import meta

from logging.handlers import TimedRotatingFileHandler

inshutdown = False

def initdirs(dirlist):
  for d in dirlist:
    if not os.path.exists(d):
      os.makedirs(d)

def shutdown_handler(signum, frame):
  global inshutdown
  if signum == signal.SIGINT or signum == signal.SIGTERM:
    inshutdown = True

def release(basepath, destdir, sitelink, jekyllpath, log):
  log.info('Releasing new version to %s' % destdir)

  # now is the chance to regenerate static pages
  subprocess.call([
    jekyllpath,
    'build',
    '--source',
    basepath,
    '--destination',
    destdir
  ])

  # point to newly built directory
  if os.path.exists(sitelink):
    os.unlink(sitelink)

  os.symlink(destdir, sitelink)

def main():
  global inshutdown

  signal.signal(signal.SIGTERM, shutdown_handler)
  signal.signal(signal.SIGINT, shutdown_handler)

  config = ConfigParser.ConfigParser()
  config.read('config.ini')

  basepath     = config.get    ( 'server' ,  'basepath'     )
  sitepath     = config.get    ( 'server' ,  'sitepath'     )
  jekyllpath   = config.get    ( 'server' ,  'jekyllpath'   )
  prefixurl    = config.get    ( 'server' ,  'prefixurl'    )
  dbname       = config.get    ( 'server' ,  'dbname'       )
  debugmode    = config.get    ( 'server' ,  'debug'        )
  pollsec      = config.getint ( 'server' ,  'pollsec'      )
  qsize        = config.getint ( 'server' ,  'qsize'        )
  access_token = config.get    ( 'dropbox',  'access_token' )

  dbpath        = "%s/data/%s" % (basepath, dbname)
  logpath       = "%s/log/change.log" % basepath
  sitelink      = "%s%s"  % (sitepath, prefixurl)
  releasedir    = "%s/releases" % sitepath

  basedirs = []

  # this is done from setup.py
  # but do this as precaution
  basedirs.append("%s/data"     % basepath)
  basedirs.append("%s/log"      % basepath)
  basedirs.append("%s/_posts"   % basepath)
  basedirs.append("%s/img/p"    % basepath)
  basedirs.append("%s/releases" % sitepath)

  # create base directories
  initdirs(basedirs)

  loglevel = logging.INFO
  if debugmode == "on":
    loglevel = logging.DEBUG

  formatter = logging.Formatter("%(asctime)s %(name)s [%(levelname)s] - %(message)s")

  handler = TimedRotatingFileHandler(logpath, when='midnight', backupCount=7)
  handler.setFormatter(formatter)

  # root logger
  log = logging.getLogger()

  log.setLevel(loglevel)
  log.addHandler(handler)

  # logging ends at this level
  log.propagate = False

  log.info("------------------")
  log.info("Lately starting up")
  log.info("------------------")

  metadb = meta.MetaDb(dbpath)
  cursor = metadb.cursor()

  if not cursor is None:
    logging.info("Using persisted cursor = %s" % cursor)

  jobqueue = Queue.Queue(qsize)

  dayone_listener = dayone.DayOneStore(access_token, cursor, jobqueue)
  blog_writer = journal.JournalWriter(basepath, prefixurl, metadb)

  log.info("Starting Lately Sync")
  dayone_listener.start()

  while not inshutdown:
    try:
      desc = jobqueue.get(block=True, timeout=5)

      if blog_writer.process(desc):
        # obtain last revision number and make a release
        destdir = '%s/%s' % (releasedir, blog_writer.revision())
        release(basepath, destdir, sitelink, jekyllpath, log)

    except Queue.Empty:
      log.debug('Queue is empty, retrying')

    except Exception, e:
      log.exception(e)

  log.info("Shutting down")
  dayone_listener.shutdown()

  # close shelves db
  metadb.close()

if __name__ == "__main__":
  main()
