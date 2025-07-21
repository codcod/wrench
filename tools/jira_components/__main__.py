"""Tool: Print components."""

import os

# from dotenv import load_dotenv

from wrench.core.api.jira import Jira, get_components_for_project

# load_dotenv()

jira = Jira(
    base_url=os.getenv('JIRA_URL'),
    username=os.getenv('JIRA_USERNAME'),
    password=os.getenv('JIRA_TOKEN'),
)


def print_components(key: str, sep: str = ',', header: bool = True):
    """Print component name and lead for components in `key` project."""
    components = get_components_for_project(jira, key)
    if header and components:
        print(f'COMPONENT{sep}LEAD')
    for c in components:
        if c.get('lead'):
            print(f'{key}{sep}{c["name"]}{sep}{c["lead"]["displayName"]}')
        else:
            print(f'{key}{sep}{c["name"]}{sep}(lead: missing)')


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument(
        'project',
        help='Key of the project for which components will be listed.',
        type=str,
    )
    parser.add_argument('--sep', help='Separator.', type=str, default=',')
    parser.add_argument('--header', help='Print header', type=bool, default=True)
    args = parser.parse_args()
    print_components(key=args.project, sep=args.sep)
