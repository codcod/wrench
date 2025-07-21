"""Tool: Print components."""

import asyncio
import json
import os
from functools import partial
from pprint import pprint

# from dotenv import load_dotenv

from wrench.core.api import sonarcloud

# load_dotenv()

create_api = partial(sonarcloud.create_api, token=str(os.getenv('SONAR_TOKEN')))


def get_repos():
    # import httpx

    # url = (
    #     'http://127.0.0.1:8000/api/repo/search?layer=backend&org=baas-devops-reference'
    # )
    # repos = httpx.get(url)
    # # print(f'{repos.json()=}')
    # names = [(r['org'], r['reponame']) for r in repos.json()]
    # print(f'{names=}')
    # return names
    return []


async def print_metrics(org: str, sep: str = ',', header: bool = False):
    """Print component name and lead for components in `key` project."""
    api: sonarcloud.API = create_api()
    async with api:
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(None, get_repos)
        components = []
        for _org, name in result:
            components.append(
                await api.get_all_components(org=_org, q=f'{_org}_{name}')
            )
        pprint(components)

    if header:
        print('-- header --')
    with open('data/out/metrics.json', 'w') as f:
        json.dump(components, f)


if __name__ == '__main__':
    from wrench.config.log import setup_logging

    setup_logging()

    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument(
        'org',
        help='Key of the project for which components will be listed.',
        type=str,
    )
    parser.add_argument('--sep', help='Separator.', type=str, default=',')
    parser.add_argument('--header', help='Print header', type=bool, default=True)
    args = parser.parse_args()
    asyncio.run(print_metrics(org=args.org, sep=args.sep))
