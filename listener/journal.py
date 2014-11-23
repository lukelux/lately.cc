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

  def getRevision(self, hashkey, meta):
    # first look for it in metadb
    revision = self.metadb.revision(hashkey)
    if revision is None:
      # must be first record with this hashkey
      # resort to current revision in meta info
      revision = meta['revision']

      # all subsequent changes to this hashkey
      # will be identified by this revision
      self.metadb.register(hashkey, revision)

    return revision

  def write(self, entry):
    name = entry['name']
    meta = entry['meta']
    fp   = entry['fp']

    hashkey   = os.path.splitext(os.path.basename(name))[0]
    extension = os.path.splitext(os.path.basename(name))[1]
    revision  = self.getRevision(hashkey, meta)

    if meta['mime_type'].startswith('image'):
      self.store_photo(fp, revision, extension)
    else:
      self.store_entry(fp, revision)

    return True

  def store_photo(self, fp, revision, extension):
    fullpath = '%s/img/p/%s%s' % (self.basepath, revision, extension)
    out = open(fullpath, 'wb')
    out.write(fp.read())
    out.close()

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
    self.log.info("%s is no longer published, removing" % fullpath)
    if os.path.isfile(fullpath):
      os.remove(fullpath)

  def store_entry(self, fp, revision):
    pfile = plistlib.readPlist(fp)
    published = pfile['Starred']
    created = pfile['Creation Date']

    fullpath = '%s/_posts/%s-%s.markdown' % (self.basepath, created.strftime("%Y-%m-%d"), revision)

    if not published:
      self.unpublish(fullpath)
      return

    entrytext = pfile['Entry Text'].encode('utf8').split("\n",1)

    content = entrytext[1]
    title   = entrytext[0]

    frontmatter = {}
    frontmatter['layout'] = 'post'
    frontmatter['title'] = title

    header = self.get_header(frontmatter)
    syntax = self.get_image_pull_syntax(revision)

    out = open(fullpath, 'wb')
    out.write("%s\n" % header)
    out.write("%s\n" % syntax)
    out.write("%s\n" % content)
    out.close()

    self.log.info("Processed changes to %s" % title)
