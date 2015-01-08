#!/usr/bin/python

import os
import pprint
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

  def __init__(self, basepath, prefixurl, metadb):
    self.basepath = basepath
    self.prefixurl = prefixurl
    self.metadb = metadb
    self.lastcursor = None
    self.lastrevision = None
    self.dirty = False

  def process(self, desc):
    self.log.debug(desc)
    if desc['type'] == 'remove':
      return self.remove(desc)

    elif desc['type'] == 'entry':
      return self.write(desc)

    elif desc['type'] == 'cursor':
      self.lastcursor = desc['pos']
      self.sync()

  def sync(self):
    if not self.lastcursor is None:
      self.metadb.commit(self.lastcursor)
      self.log.info("Persisted cursor = %s" % self.lastcursor)

  def revision(self):
    return self.lastrevision

  def remove(self, entry):
    filename = entry['name']
    hashkey    = os.path.splitext(os.path.basename(filename))[0]
    extension  = os.path.splitext(os.path.basename(filename))[1]

    # now remove whatever is present
    d = self.metadb.describe(hashkey)
    if d is None:
      return False

    if 'imgpath' in d and os.path.exists(d['imgpath']):
      os.remove(d['imgpath'])
      self.log.info('Removed image file - %s' % d['imgpath'])

    if 'entrypath' in d and os.path.exists(d['entrypath']):
      os.remove(d['entrypath'])
      self.log.info('Removed entry file - %s' % d['entrypath'])

    # remove items from metadb
    self.metadb.deregister(hashkey)
    return True

  def resolve_fullpath(self, name, meta, pfile=None):
    fileparts = os.path.splitext(os.path.basename(name))

    hashkey   = fileparts[0]
    extension = fileparts[1]

    mime      = meta['mime_type']

    d = self.metadb.describe(hashkey)
    if d is None:
      d = { 'revision' : meta['revision'] }

    revision = d['revision']
    entryexists = True

    if mime.startswith('image'):
      entryexists = 'entrypath' in d
      if 'imgpath' in d:
        return (revision, d['imgpath'], entryexists)

      newpath = "%s/img/p/%s%s" % (self.basepath, revision, extension)
      d['imgpath'] = newpath
      self.metadb.register(hashkey, d)
      return (revision, newpath, entryexists)

    if 'entrypath' in d:
      return (revision, d['entrypath'], True)

    if pfile is None:
      return None

    created = pfile['Creation Date']
    newpath = "%s/_posts/%s-%s.markdown" % (self.basepath, created.strftime("%Y-%m-%d"), revision)

    d['entrypath'] = newpath
    self.metadb.register(hashkey, d)

    return (revision, newpath, True)

  def write(self, entry):
    name = entry['name']
    meta = entry['meta']
    fp   = entry['fp']

    if 'revision' in meta:
      self.lastrevision = meta['revision']

    mime = meta['mime_type']
    payload = fp.read()

    revision = 0
    if mime.startswith('image'):
      (revision, fullpath, entryexists) = self.resolve_fullpath(name, meta)
      self.persist(fullpath, payload)
      return entryexists

    pfile    = plistlib.readPlistFromString(payload)
    (revision, fullpath, entryexists) = self.resolve_fullpath(name, meta, pfile)
    return self.store_entry(fullpath, revision, pfile)

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
    return t.render(basepath=self.basepath, prefixurl=self.prefixurl, revision=revision)

  def unpublish(self, fullpath):
    if os.path.exists(fullpath) and os.path.isfile(fullpath):
      self.log.info("%s is no longer published, removing" % fullpath)
      os.remove(fullpath)
      return True

    # false indicates there was no side effect (therefore no release)
    self.log.debug("Entry not published yet, skipping release")
    return False

  def store_entry(self, fullpath, revision, pfile):
    published = pfile['Starred']

    if not published:
      return self.unpublish(fullpath)

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

    return True

  def persist(self, filename, parts):
    out = open(filename, 'wb')
    for part in parts:
      out.write(part)
    out.close()
