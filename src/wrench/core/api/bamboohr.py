# pylint: disable=C0114,C0115,C0116
import asyncio
import enum
import logging
import typing as tp

import aiohttp
from multidict import MultiDict

from ...config.config import read_config

Params = dict[str, str] | None
ClientSession = aiohttp.ClientSession | None


class HTTPError(Exception):
    pass


class Method(enum.StrEnum):
    GET_EMPLOYEES = 'v1/employees/directory'
    GET_EMPLOYEE_DETAILS = 'v1/employees/{employee_id}'
    GET_TIME_OFF_REQUESTS = 'v1/time_off/requests'
    GET_COMPANY_INFO = 'v1/meta/users'


class APIBase:
    def __init__(self, *, api_key: str):
        self.api_key = api_key
        self.headers = {
            'Accept': 'application/json',
            'Authorization': f'Bearer {api_key}',
        }
        self._session: ClientSession = None

    @property
    def base_url(self) -> str:
        # BambooHR API uses company subdomain format
        company_domain = str(read_config('.env').get('BAMBOOHR_COMPANY_DOMAIN'))
        return f'https://api.bamboohr.com/api/gateway.php/{company_domain}'

    def url_for(self, method: Method, params: Params) -> str:
        m = method
        if params:
            m = method.format(**params)
        return f'{self.base_url}/{m}'

    async def _get(
        self, method: Method, params: Params, query_params: Params = None
    ) -> dict[str, tp.Any]:
        assert method is not None
        assert self._session is not None

        url = self.url_for(method, params)

        async with self._session.get(url, params=query_params) as response:
            if response.ok:
                r = await response.json()
                return r
            else:
                raise HTTPError(
                    f'Error calling BambooHR API: {url}, status: {response.status}'
                )

    async def _mget(
        self, method: Method, params: Params, query_params: MultiDict | None = None
    ) -> list[dict[str, tp.Any]]:
        """
        BambooHR API typically returns data directly without pagination,
        but this method provides consistency with other API clients.
        """
        assert method is not None
        assert self._session is not None

        url = self.url_for(method, params)
        logging.debug('get url: %s', url)

        if query_params is None:
            query_params = MultiDict()

        async with self._session.get(url, params=query_params) as response:
            if response.ok:
                r = await response.json()
            else:
                raise HTTPError(f'Error calling BambooHR API: {url}')

        # BambooHR typically returns data in 'employees' field for employee endpoints
        if isinstance(r, dict) and 'employees' in r:
            return r['employees']
        elif isinstance(r, list):
            return r
        else:
            # For single objects, wrap in list for consistency
            return [r] if r else []

    async def __aenter__(self):
        self._session = aiohttp.ClientSession(
            headers=self.headers, loop=asyncio.get_event_loop()
        )

    async def __aexit__(self, *args):
        if self._session:
            await self._session.close()


class API(APIBase):
    async def get_employees(
        self, *, params: Params = None, query_params: MultiDict | None = None
    ) -> list[dict[str, tp.Any]]:
        """Get employee directory listing."""
        method = Method.GET_EMPLOYEES
        logging.debug('call: get_employees')

        try:
            r = await self._mget(method, params=params, query_params=query_params)
        except HTTPError:
            logging.debug(
                'Error calling %s with %s and query %s', method, params, query_params
            )
            r = []
        return r

    async def get_employee_details(
        self,
        employee_id: str,
        *,
        params: Params = None,
        query_params: dict[str, str] | None = None,
    ) -> dict[str, tp.Any]:
        """Get detailed information for a specific employee."""
        method = Method.GET_EMPLOYEE_DETAILS
        logging.debug('call: get_employee_details for employee_id=%s', employee_id)

        if params is None:
            params = {}
        params['employee_id'] = employee_id

        try:
            r = await self._get(method, params=params, query_params=query_params)
        except HTTPError:
            logging.debug(
                'Error calling %s with %s and query %s', method, params, query_params
            )
            r = {}
        return r

    async def get_time_off_requests(
        self, *, params: Params = None, query_params: MultiDict | None = None
    ) -> list[dict[str, tp.Any]]:
        """Get time off requests."""
        method = Method.GET_TIME_OFF_REQUESTS
        logging.debug('call: get_time_off_requests')

        try:
            r = await self._mget(method, params=params, query_params=query_params)
        except HTTPError:
            logging.debug(
                'Error calling %s with %s and query %s', method, params, query_params
            )
            r = []
        return r

    async def get_company_info(
        self, *, params: Params = None, query_params: dict[str, str] | None = None
    ) -> dict[str, tp.Any]:
        """Get company information and users."""
        method = Method.GET_COMPANY_INFO
        logging.debug('call: get_company_info')

        try:
            r = await self._get(method, params=params, query_params=query_params)
        except HTTPError:
            logging.debug(
                'Error calling %s with %s and query %s', method, params, query_params
            )
            r = {}
        return r


def create_api(*, api_key: str) -> API:
    """Create a BambooHR API client instance."""
    return API(api_key=api_key)
