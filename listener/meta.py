#!/usr/bin/python

import shelve

class MetaDb:
  """
  Simple shelve db to record meta data about blog posts
  """

  def __init__(self, dbpath):
    self.path = dbpath
    self.db = shelve.open(dbpath)

  def close(self):
    self.db.close()

  def rewind(self):
    if self.db.has_key('cursor'):
      del self.db['cursor']

  def cursor(self):
    if self.db.has_key('cursor'):
      return self.db.get('cursor')
    return None

  def commit(self, cursor):
    self.db['cursor'] = cursor
    self.db.sync()

  def register(self, hashkey, desc):
    k = hashkey.encode('utf-8')
    self.db[k] = desc
    self.db.sync()

  def deregister(self, hashkey):
    k = hashkey.encode('utf-8')
    if self.db.has_key(k):
      del self.db[k]
      self.db.sync()
      
  def describe(self, hashkey):
    k = hashkey.encode('utf-8')
    if self.db.has_key(k):
      return self.db[k]
    return None
