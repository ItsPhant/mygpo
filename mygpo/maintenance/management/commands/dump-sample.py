from base64 import b64decode
from optparse import make_option
import sys

from couchdb import json
from couchdb.multipart import write_multipart

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from mygpo import migrate
from mygpo.core.models import Podcast
from mygpo.users.models import PodcastUserState, Suggestions
from mygpo.directory.models import Category


class Command(BaseCommand):
    """
    Dumps a Sample of the whole Database that can be used for
    testing/development. All objects that are (indirectly) referenced
    be the users specified by --user args are dumped.

    The dump is similar to a dump of couchdb-python's couchdb-dump and
    can be imported by its couchdb-load
    """


    option_list = BaseCommand.option_list + (
        make_option('--user', action='append', type="string", dest='users',
            help="User for which related data should be dumped"),
    )


    def handle(self, *args, **options):

        docs = set()

        for user in options.get('users', []):
            old_u = User.objects.get(username=user)

            # User
            new_u = migrate.get_or_migrate_user(old_u)
            docs.add(new_u._id)

            # Suggestions
            suggestions = Suggestions.for_user_oldid(old_u.id)
            docs.add(suggestions._id)

            # Podcast States
            for p_state in PodcastUserState.for_user(old_u):
                docs.add(p_state._id)

                # Categories
                for tag in p_state.tags:
                    c = Category.for_tag(tag)
                    if c: docs.add(c._id)

                # Podcast
                podcast = Podcast.for_id(p_state.podcast)
                docs.add(podcast._id)

                # Categories
                for s in podcast.tags:
                    for tag in podcast.tags[s]:
                        c = Category.for_tag(tag)
                        if c: docs.add(c._id)

                # Episodes
                for episode in podcast.get_episodes():
                    docs.add(episode._id)

        db = Podcast.get_db()
        self.dump(docs, db)


    def dump(self, docs, db):

        output = sys.stdout
        boundary = None
        envelope = write_multipart(output, boundary=boundary)

        for docid in docs:

            doc = db.get(docid, attachments=True)
            print >> sys.stderr, 'Dumping document %r' % doc['_id']
            attachments = doc.pop('_attachments', {})
            jsondoc = json.encode(doc)

            if attachments:
                parts = envelope.open({
                    'Content-ID': doc['_id'],
                    'ETag': '"%s"' % doc['_rev']
                })
                parts.add('application/json', jsondoc)

                for name, info in attachments.items():
                    content_type = info.get('content_type')
                    if content_type is None: # CouchDB < 0.8
                        content_type = info.get('content-type')
                    parts.add(content_type, b64decode(info['data']), {
                        'Content-ID': name
                    })
                parts.close()

            else:
                envelope.add('application/json', jsondoc, {
                    'Content-ID': doc['_id'],
                    'ETag': '"%s"' % doc['_rev']
                })

        envelope.close()