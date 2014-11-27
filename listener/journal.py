#!/usr/bin/python

import os
import logging
import dropbox
import plistlib
from jinja2 import Template, Environment, FileSystemLoader

class JournalWriter:
  """
    Converts Dropbox entry into journal entry file
  """
  log = logging.getLogger(__name__)
  yamldivide = "---"

  def __init__(self, basepath, metadb):
    self.basepath = basepath
    self.metadb = metadb

  def remove(self, entry):
    filename = entry['name']
    hashkey    = os.path.splitext(os.path.basename(filename))[0]
    extension  = os.path.splitext(os.path.basename(filename))[1]
    
    # now remove whatever is present
    d = self.metadb.describe(hashkey)
    if d is None:
      return

    if 'imgpath' in d and os.path.exists(d['imgpath']):
      os.remove(d['imgpath'])
      self.log.info('Removed image file - %s' % d['imgpath'])

    if 'entrypath' in d and os.path.exists(d['entrypath']):
      os.remove(d['entrypath'])
      self.log.info('Removed entry file - %s' % d['entrypath'])

    # remove items from metadb
    self.metadb.deregister(hashkey)

  def resolve_fullpath(self, name, meta, pfile=None):
    fileparts = os.path.splitext(os.path.basename(name))

    hashkey   = fileparts[0]
    extension = fileparts[1]

    mime      = meta['mime_type']

    d = self.metadb.describe(hashkey)
    if d is None:
      d = { 'revision' : meta['revision'] }

    revision = d['revision']
    if mime.startswith('image'):
      if 'imgpath' in d:
        return (revision, d['imgpath'])

      newpath = "%s/img/p/%s%s" % (self.basepath, revision, extension)
      d['imgpath'] = newpath
      self.metadb.register(hashkey, d)
      return (revision, newpath)

    if 'entrypath' in d:
      return (revision, d['entrypath'])

    if pfile is None:
      return None

    created = pfile['Creation Date']
    newpath = "%s/_posts/%s-%s.markdown" % (self.basepath, created.strftime("%Y-%m-%d"), revision)

    d['entrypath'] = newpath
    self.metadb.register(hashkey, d)

    return (revision, newpath)

  def write(self, entry):
    name = entry['name']
    meta = entry['meta']
    fp   = entry['fp']

    mime = meta['mime_type']
    payload = fp.read()

    revision = 0
    if mime.startswith('image'):
      (revision, fullpath) = self.resolve_fullpath(name, meta)
      self.persist(fullpath, payload)
      return True

    pfile    = plistlib.readPlistFromString(payload)
    (revision, fullpath) = self.resolve_fullpath(name, meta, pfile)
    self.store_entry(fullpath, revision, pfile)

    # TODO, do exception handling
    return True

  def get_header(self, frontmatter):
    headeritems = []
    headeritems.append(self.yamldivide)
    for key, value in frontmatter.iteritems():
      headeritems.append("%s: %s" % (key,value))
    headeritems.append(self.yamldivide)
    return "\n".join(headeritems)

  def get_image_pull_syntax(self, revision):
    PATH = os.path.dirname(os.path.abspath(__file__))
    TEMPLATE_ENVIRONMENT = Environment(
      autoescape=False,
      loader=FileSystemLoader(os.path.join(PATH, '../templates')),
      trim_blocks=False)

    t = TEMPLATE_ENVIRONMENT.get_template('img-check-syntax.template')
    return t.render(basepath=self.basepath, revision=revision)

  def unpublish(self, fullpath):
    if os.path.exists(fullpath) and os.path.isfile(fullpath):
      self.log.info("%s is no longer published, removing" % fullpath)
      os.remove(fullpath)

  def store_entry(self, fullpath, revision, pfile):
    published = pfile['Starred']

    if not published:
      self.unpublish(fullpath)
      return

    entrytext = pfile['Entry Text'].encode('utf8').split("\n",1)

    content = "%s\n" % entrytext[1]
    title   = entrytext[0]

    frontmatter = {}
    frontmatter['layout'] = 'post'
    frontmatter['title'] = title

    header = "%s\n" % self.get_header(frontmatter)
    syntax = "%s\n" % self.get_image_pull_syntax(revision)

    self.persist(fullpath, [header, syntax, content])
    self.log.info("Processed changes to %s" % title)

  def persist(self, filename, parts):
    out = open(filename, 'wb')
    for part in parts:
      out.write(part)
    out.close()
