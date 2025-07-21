"""Provide basic access to Jira API."""

import dataclasses as dtc
import logging

import requests


@dtc.dataclass
class Jira:
    """JIRA details."""

    username: str | None
    password: str | None
    base_url: str | None


def get_components_for_project(jira: Jira, key: str, timeout: int = 10) -> list[dict]:
    """List components defined in Jira project indicated by `key`."""
    try:
        r = requests.get(
            f'{jira.base_url}/rest/api/2/project/{key}/components',
            auth=(jira.username, jira.password),  # pyright: ignore
            timeout=timeout,
        )
        r.raise_for_status()
    except requests.exceptions.HTTPError as e:
        logging.warning(
            'Error calling JIRA API: %s.'
            'Most likely the project with specified key (%s) does not exist.',
            e,
            key,
        )
        return []
    return r.json()
