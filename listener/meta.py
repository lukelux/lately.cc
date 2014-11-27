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
    self.db[hashkey] = desc
    self.db.sync()

  def deregister(self, hashkey):
    if self.db.has_key(hashkey):
      del self.db[hashkey]
      self.db.sync()
      
  def describe(self, hashkey):
    if self.db.has_key(hashkey):
      return self.db[hashkey]
    return None
