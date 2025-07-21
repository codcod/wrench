# pylint: disable=C0114,C0115,C0116
from functools import partial

import pytest as pt
from wrench.core.api import sonarcloud
from wrench.config.config import read_config

cfg = read_config('.env')

# DOMAIN = cfg.get('DOMAIN')
TOKEN = str(cfg.get('SONAR_TOKEN'))

create_api = partial(sonarcloud.create_api, token=TOKEN)


@pt.mark.asyncio
async def test_get_component_search() -> None:
    api: sonarcloud.API = create_api()
    async with api:
        # fields = 'components'
        c = await api.get_components_search(org='xxx-rnd')
        assert c is not None
        print(c)


@pt.mark.asyncio
async def test_get_measures_component() -> None:
    api: sonarcloud.API = create_api()
    async with api:
        measures = await api.get_measures_component(
            component='xxx-rnd_fic-account-verification',
            additional_fields='metrics',
        )
        assert measures is not None
        print(measures)
