#!/usr/bin/python

import sys
import time
import shelve
import logging
import signal, os
import threading

import ConfigParser
import Queue

import dayone
import journal
import meta

inshutdown = False

def initdirs(dirlist):
  for d in dirlist:
    if not os.path.exists(d):
      os.makedirs(d)

def shutdown_handler(signum, frame):
  global inshutdown
  if signum == signal.SIGINT or signum == signal.SIGTERM:
    inshutdown = True

def main():
  global inshutdown

  signal.signal(signal.SIGTERM, shutdown_handler)
  signal.signal(signal.SIGINT, shutdown_handler)

  config = ConfigParser.ConfigParser()
  config.read('config.ini')

  basepath     = config.get    ( 'server' ,  'basepath'     )
  dbname       = config.get    ( 'server' ,  'dbname'       )
  pollsec      = config.getint ( 'server' ,  'pollsec'      )
  qsize        = config.getint ( 'server' ,  'qsize'        )
  access_token = config.get    ( 'dropbox',  'access_token' )

  dbpath   = "%s/data/%s" % (basepath, dbname)
  logpath  = "%s/log/lately.cc" % basepath

  basedirs = []
  basedirs.append("%s/data"   % basepath)
  basedirs.append("%s/log"    % basepath)
  basedirs.append("%s/_posts" % basepath)
  basedirs.append("%s/img"    % basepath)

  # create base directories
  initdirs(basedirs)

  logging.basicConfig(
    filename=logpath,
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(name)s: %(message)s'
  )

  log = logging.getLogger("main")

  log.info("------------------")
  log.info("Lately starting up")
  log.info("------------------")

  metadb = meta.MetaDb(dbpath)
  cursor = metadb.cursor()

  if not cursor is None:
    logging.info("Using persisted cursor = %s" % cursor)

  jobqueue = Queue.Queue(qsize)

  dayone_listener = dayone.DayOneStore(access_token, cursor, jobqueue)
  blog_writer = journal.JournalWriter(basepath, metadb)

  log.info("Starting Lately Sync")
  dayone_listener.start()

  while not inshutdown:
    try:
      desc = jobqueue.get(block=True, timeout=5)

      if desc['type'] == 'cursor':
        # this is a cursor entry, persist to position disk
        metadb.commit(desc['pos'])
        log.debug("Persisted cursor pos=%s" % desc['pos'])

        # now is the chance to regenerate static pages

      else:
        # do journal write here
        blog_writer.write(desc)

    except Queue.Empty:
      log.debug('Queue is empty, retrying')

  log.info("Shutting down")
  dayone_listener.shutdown()

  # close shelves db
  metadb.close()

if __name__ == "__main__":
  main()