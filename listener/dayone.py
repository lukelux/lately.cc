#!/usr/bin/python

import time
import dropbox
import logging
import threading

class DayOneStore:
  """
    Object to represent Day One storage
    Dropbox storage is assumed for now
  """

  dayone_root    = '/Day One/journal.dayone'

  def __init__(self, access_token, cursor, jobqueue):
    self.cursor = cursor
    self.access_token = access_token
    self.log = logging.getLogger(self.__class__.__name__)
    self.dropbox_client = None
    self.jobqueue = jobqueue
    self.shutdown_event = None
    self.cached = []

  def start(self):
    self.shutdown_event = threading.Event()
    self.change_listener = threading.Thread(target=self.run)
    self.change_listener.daemon = True
    self.change_listener.start()

  def shutdown(self):
    self.shutdown_event.set()
    self.change_listener.join()

  def run(self):
    while not self.shutdown_event.is_set():
      entry = self.poll(30)
      if not entry is None:
        self.jobqueue.put(entry)

  def check_and_connect(self):
    if self.dropbox_client is None:
      try:
        self.dropbox_client = dropbox.client.DropboxClient(self.access_token)
        self.log.info("Connected to dropbox")
      except:
        self.log.error('Error connecting to dropbox, trying again in the next poll()')
        self.dropbox_client = None
        return False
    return True

  def poll(self, timeoutsec):
    if not self.check_and_connect():
      return None

    if self.cached:
      return self.realize(self.cached.pop(0))

    if not self.cursor is None:
      self.log.debug("Calling longpoll with %d sec timeout" % timeoutsec)
      longpoll_result = self.dropbox_client.longpoll_delta(self.cursor, timeout=timeoutsec)

      # something must have angered dropbox
      # backoff until desired interval
      if 'backoff' in longpoll_result:
        backoffsec = longpoll_result['backoff']
        self.log.debug("Backing off for %d sec" % backoffsec)
        time.sleep(backoffsec)

      # no changes, simply return nothing
      if not longpoll_result['changes']:
        self.log.debug("No changes, retrying later")
        return None

    results = []
    hasmore = True

    while hasmore:
      result = self.dropbox_client.delta(self.cursor, self.dayone_root)
      self.cursor = result['cursor']
      hasmore = result['has_more']

      lastrevision = 0
      syncrequired = False

      for entry in result['entries']:
        filename = entry[0]
        meta = entry[1]

        if meta is None:
          results.append({
              'type' : 'remove',
              'name': filename
            })
          syncrequired = True
          continue

        # skip any dir level notification
        if meta['is_dir']:
          continue

        lastrevision = meta['revision']

        self.log.debug('Appending %s to change list' % filename)
        results.append({
          'type' : 'entry',
          'entry' : entry
        })

      if syncrequired or lastrevision > 0:
        cursormark = {
          'type'     : 'cursor',
          'pos'      : self.cursor,
        }

        if lastrevision > 0:
          cursormark['revision'] = lastrevision

        results.append(cursormark)

    if not results:
      return None

    self.cached.extend(results)
    return self.realize(self.cached.pop(0))

  def realize(self, desc):
    if desc is None:
      return None

    if desc['type'] == 'cursor' or desc['type'] == 'remove':
      return desc

    entry = desc['entry']

    name = entry[0]
    meta = entry[1]

    try:
      f = self.dropbox_client.get_file(name)
      return {
        'type' : 'entry',
        'name' : name,
        'meta' : meta,
        'fp'   : f
      }
    except:
      self.log.error('Error fetching file %s' % name)

    return None
