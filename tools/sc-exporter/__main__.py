import argparse
import asyncio
import logging

import uvloop
from multidict import MultiDict

from wrench.config.log import setup_logging

from . import entity

FIELDS = (
    'metadata.name,'
    'metadata.title,'
    'metadata.description,'
    'spec.owner,'
    'spec.type,'
    'spec.lifecycle,'
    'spec.subcomponentOf,'
    'kind,'
    'metadata.annotations.backstage.io/view-url,'
    'metadata.annotations.jira/maint-component,'
    'metadata.annotations.jira/maint-subcomponent,'
    'metadata.annotations.jira/project-key,'
    'metadata.annotations.jira/project-component,'
    'metadata.annotations.slack/conversation-id,'
)

parser = argparse.ArgumentParser()
parser.add_argument('action', help='Help', type=str, default=None)
parser.add_argument(
    '--format', help='Output data format (json, csv, txt).', type=str, default='txt'
)
parser.add_argument('--filename', help='Output file.', type=str, default=None)
parser.add_argument(
    '-v', '--verbose', action='store_true', help='explain what is being done'
)

args = parser.parse_args()

level = logging.DEBUG if args.verbose else logging.INFO
setup_logging(level=level)
logging.getLogger('root').setLevel(level=level)


async def main(args):
    ent = entity.Entity()
    params = MultiDict(
        [
            ('filter', 'spec.owner=dl-titane'),
            ('filter', 'spec.owner=dl-platinum'),
            ('filter', 'spec.owner=dl-iron'),
            ('filter', 'spec.owner=dl-vectron'),
            ('filter', 'spec.owner=dl-krypton'),
            ('filter', 'spec.owner=do-maplepower'),
            ('filter', 'spec.owner=do-helium'),
            ('filter', 'spec.owner=do-xenon'),
            ('filter', 'spec.owner=do-lithium'),
            # ('fields', FIELDS),
        ]
    )
    await ent.ingest(query_params=params)
    ent.clean_description_field()
    match args.action:
        case 'export':
            fn = args.filename
            fmt = args.format
            match fmt:
                case 'csv':
                    ent.export_csv(fn)
                case 'json':
                    ent.export_json(fn)
                case _:
                    ent.export_txt(fn)
        case 'validate':
            pass


uvloop.install()
asyncio.run(main(args))
