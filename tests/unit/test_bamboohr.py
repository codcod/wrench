# pylint: disable=C0114,C0115,C0116
from unittest.mock import AsyncMock, MagicMock, patch

import pytest as pt
from multidict import MultiDict

from wrench.core.api.bamboohr import API, APIBase, HTTPError, Method, create_api


class TestHTTPError:
    def test_http_error_inheritance(self):
        error = HTTPError('Test error')
        assert isinstance(error, Exception)
        assert str(error) == 'Test error'


class TestMethod:
    def test_method_enum_values(self):
        assert Method.GET_EMPLOYEES == 'v1/employees/directory'
        assert Method.GET_EMPLOYEE_DETAILS == 'v1/employees/{employee_id}'
        assert Method.GET_TIME_OFF_REQUESTS == 'v1/time_off/requests'
        assert Method.GET_COMPANY_INFO == 'v1/meta/users'
        assert isinstance(Method.GET_EMPLOYEES, str)
        assert isinstance(Method.GET_EMPLOYEE_DETAILS, str)


class TestAPIBase:
    def test_init_with_api_key(self):
        api = APIBase(api_key='test-api-key')

        assert api.api_key == 'test-api-key'
        assert api.headers == {
            'Accept': 'application/json',
            'Authorization': 'Bearer test-api-key',
        }
        assert api._session is None

    @patch('wrench.core.api.bamboohr.read_config')
    def test_base_url_formation(self, mock_read_config):
        mock_read_config.return_value = {'BAMBOOHR_COMPANY_DOMAIN': 'mycompany'}
        api = APIBase(api_key='test-key')

        assert api.base_url == 'https://api.bamboohr.com/api/gateway.php/mycompany'

    @patch('wrench.core.api.bamboohr.read_config')
    def test_url_for_without_params(self, mock_read_config):
        mock_read_config.return_value = {'BAMBOOHR_COMPANY_DOMAIN': 'mycompany'}
        api = APIBase(api_key='test-key')

        url = api.url_for(Method.GET_EMPLOYEES, None)
        assert (
            url
            == 'https://api.bamboohr.com/api/gateway.php/mycompany/v1/employees/directory'
        )

    @patch('wrench.core.api.bamboohr.read_config')
    def test_url_for_with_params(self, mock_read_config):
        mock_read_config.return_value = {'BAMBOOHR_COMPANY_DOMAIN': 'mycompany'}
        api = APIBase(api_key='test-key')

        url = api.url_for(Method.GET_EMPLOYEE_DETAILS, {'employee_id': '123'})
        assert (
            url == 'https://api.bamboohr.com/api/gateway.php/mycompany/v1/employees/123'
        )

    @pt.mark.asyncio
    async def test_aenter_creates_session(self):
        api = APIBase(api_key='test-key')

        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_session = MagicMock()
            mock_session_class.return_value = mock_session

            result = await api.__aenter__()

            assert api._session == mock_session
            assert result is None

    @pt.mark.asyncio
    async def test_aexit_closes_session(self):
        api = APIBase(api_key='test-key')

        mock_session = AsyncMock()
        api._session = mock_session

        await api.__aexit__(None, None, None)

        mock_session.close.assert_called_once()

    @pt.mark.asyncio
    async def test_aexit_no_session(self):
        api = APIBase(api_key='test-key')

        # Should not raise an error when _session is None
        await api.__aexit__(None, None, None)

    @pt.mark.asyncio
    async def test_get_success(self):
        with patch('wrench.core.api.bamboohr.read_config') as mock_read_config:
            mock_read_config.return_value = {'BAMBOOHR_COMPANY_DOMAIN': 'mycompany'}
            api = APIBase(api_key='test-key')

            mock_response = AsyncMock()
            mock_response.ok = True
            mock_response.json.return_value = {'data': 'test'}

            mock_context_manager = MagicMock()
            mock_context_manager.__aenter__ = AsyncMock(return_value=mock_response)
            mock_context_manager.__aexit__ = AsyncMock(return_value=None)

            mock_session = MagicMock()
            mock_session.get = MagicMock(return_value=mock_context_manager)
            api._session = mock_session

            result = await api._get(Method.GET_EMPLOYEES, None)

            assert result == {'data': 'test'}
            mock_session.get.assert_called_once()

    @pt.mark.asyncio
    async def test_get_http_error(self):
        with patch('wrench.core.api.bamboohr.read_config') as mock_read_config:
            mock_read_config.return_value = {'BAMBOOHR_COMPANY_DOMAIN': 'mycompany'}
            api = APIBase(api_key='test-key')

            mock_response = AsyncMock()
            mock_response.ok = False
            mock_response.status = 401

            mock_context_manager = MagicMock()
            mock_context_manager.__aenter__ = AsyncMock(return_value=mock_response)
            mock_context_manager.__aexit__ = AsyncMock(return_value=None)

            mock_session = MagicMock()
            mock_session.get = MagicMock(return_value=mock_context_manager)
            api._session = mock_session

            with pt.raises(HTTPError) as exc_info:
                await api._get(Method.GET_EMPLOYEES, None)

            assert 'Error calling BambooHR API' in str(exc_info.value)
            assert '401' in str(exc_info.value)

    @pt.mark.asyncio
    async def test_mget_with_employees_field(self):
        with patch('wrench.core.api.bamboohr.read_config') as mock_read_config:
            mock_read_config.return_value = {'BAMBOOHR_COMPANY_DOMAIN': 'mycompany'}
            api = APIBase(api_key='test-key')

            mock_response_data = {'employees': [{'id': 1}, {'id': 2}]}

            mock_response = AsyncMock()
            mock_response.ok = True
            mock_response.json.return_value = mock_response_data

            mock_context_manager = MagicMock()
            mock_context_manager.__aenter__ = AsyncMock(return_value=mock_response)
            mock_context_manager.__aexit__ = AsyncMock(return_value=None)

            mock_session = MagicMock()
            mock_session.get = MagicMock(return_value=mock_context_manager)
            api._session = mock_session

            result = await api._mget(Method.GET_EMPLOYEES, None)

            assert result == [{'id': 1}, {'id': 2}]

    @pt.mark.asyncio
    async def test_mget_with_list_response(self):
        with patch('wrench.core.api.bamboohr.read_config') as mock_read_config:
            mock_read_config.return_value = {'BAMBOOHR_COMPANY_DOMAIN': 'mycompany'}
            api = APIBase(api_key='test-key')

            mock_response_data = [{'id': 1}, {'id': 2}]

            mock_response = AsyncMock()
            mock_response.ok = True
            mock_response.json.return_value = mock_response_data

            mock_context_manager = MagicMock()
            mock_context_manager.__aenter__ = AsyncMock(return_value=mock_response)
            mock_context_manager.__aexit__ = AsyncMock(return_value=None)

            mock_session = MagicMock()
            mock_session.get = MagicMock(return_value=mock_context_manager)
            api._session = mock_session

            result = await api._mget(Method.GET_TIME_OFF_REQUESTS, None)

            assert result == [{'id': 1}, {'id': 2}]

    @pt.mark.asyncio
    async def test_mget_with_single_object(self):
        with patch('wrench.core.api.bamboohr.read_config') as mock_read_config:
            mock_read_config.return_value = {'BAMBOOHR_COMPANY_DOMAIN': 'mycompany'}
            api = APIBase(api_key='test-key')

            mock_response_data = {'id': 1, 'name': 'test'}

            mock_response = AsyncMock()
            mock_response.ok = True
            mock_response.json.return_value = mock_response_data

            mock_context_manager = MagicMock()
            mock_context_manager.__aenter__ = AsyncMock(return_value=mock_response)
            mock_context_manager.__aexit__ = AsyncMock(return_value=None)

            mock_session = MagicMock()
            mock_session.get = MagicMock(return_value=mock_context_manager)
            api._session = mock_session

            result = await api._mget(Method.GET_COMPANY_INFO, None)

            assert result == [{'id': 1, 'name': 'test'}]


class TestAPI:
    @pt.mark.asyncio
    async def test_get_employees_success(self):
        api = API(api_key='test-key')

        expected_result = [{'id': 1}, {'id': 2}]

        with patch.object(api, '_mget', return_value=expected_result) as mock_mget:
            result = await api.get_employees()

            assert result == expected_result
            mock_mget.assert_called_once_with(
                Method.GET_EMPLOYEES, params=None, query_params=None
            )

    @pt.mark.asyncio
    async def test_get_employees_with_query_params(self):
        api = API(api_key='test-key')

        expected_result = [{'id': 1}]
        query_params = MultiDict([('displayName', 'John Doe')])

        with patch.object(api, '_mget', return_value=expected_result) as mock_mget:
            result = await api.get_employees(query_params=query_params)

            assert result == expected_result
            mock_mget.assert_called_once_with(
                Method.GET_EMPLOYEES, params=None, query_params=query_params
            )

    @pt.mark.asyncio
    async def test_get_employees_http_error_returns_empty_list(self):
        api = API(api_key='test-key')

        with patch.object(
            api, '_mget', side_effect=HTTPError('API Error')
        ) as mock_mget:
            result = await api.get_employees()

            assert result == []
            mock_mget.assert_called_once()

    @pt.mark.asyncio
    async def test_get_employee_details_success(self):
        api = API(api_key='test-key')

        expected_result = {'id': 123, 'name': 'John Doe'}

        with patch.object(api, '_get', return_value=expected_result) as mock_get:
            result = await api.get_employee_details('123')

            assert result == expected_result
            mock_get.assert_called_once_with(
                Method.GET_EMPLOYEE_DETAILS,
                params={'employee_id': '123'},
                query_params=None,
            )

    @pt.mark.asyncio
    async def test_get_employee_details_with_params(self):
        api = API(api_key='test-key')

        expected_result = {'id': 123, 'name': 'John Doe'}
        params = {'fields': 'firstName,lastName'}

        with patch.object(api, '_get', return_value=expected_result) as mock_get:
            result = await api.get_employee_details('123', params=params)

            assert result == expected_result
            # params should include both original params and employee_id
            expected_params = {'fields': 'firstName,lastName', 'employee_id': '123'}
            mock_get.assert_called_once_with(
                Method.GET_EMPLOYEE_DETAILS, params=expected_params, query_params=None
            )

    @pt.mark.asyncio
    async def test_get_employee_details_http_error_returns_empty_dict(self):
        api = API(api_key='test-key')

        with patch.object(api, '_get', side_effect=HTTPError('API Error')) as mock_get:
            result = await api.get_employee_details('123')

            assert result == {}
            mock_get.assert_called_once()

    @pt.mark.asyncio
    async def test_get_time_off_requests_success(self):
        api = API(api_key='test-key')

        expected_result = [{'id': 1, 'type': 'vacation'}, {'id': 2, 'type': 'sick'}]

        with patch.object(api, '_mget', return_value=expected_result) as mock_mget:
            result = await api.get_time_off_requests()

            assert result == expected_result
            mock_mget.assert_called_once_with(
                Method.GET_TIME_OFF_REQUESTS, params=None, query_params=None
            )

    @pt.mark.asyncio
    async def test_get_company_info_success(self):
        api = API(api_key='test-key')

        expected_result = {'company': 'Test Corp', 'users': []}

        with patch.object(api, '_get', return_value=expected_result) as mock_get:
            result = await api.get_company_info()

            assert result == expected_result
            mock_get.assert_called_once_with(
                Method.GET_COMPANY_INFO, params=None, query_params=None
            )


class TestCreateAPI:
    def test_create_api_returns_api_instance(self):
        api = create_api(api_key='test-key')

        assert isinstance(api, API)
        assert isinstance(api, APIBase)
        assert api.api_key == 'test-key'


class TestIntegration:
    @pt.mark.asyncio
    async def test_context_manager_usage(self):
        mock_session = AsyncMock()

        with patch('aiohttp.ClientSession', return_value=mock_session):
            api = create_api(api_key='test-key')

            async with api:
                assert api._session == mock_session

            mock_session.close.assert_called_once()

    @pt.mark.asyncio
    async def test_full_workflow_with_mocked_responses(self):
        with patch('wrench.core.api.bamboohr.read_config') as mock_read_config:
            mock_read_config.return_value = {'BAMBOOHR_COMPANY_DOMAIN': 'testcompany'}

            # Mock response data
            response_data = {
                'employees': [
                    {'id': 1, 'displayName': 'John Doe', 'workEmail': 'john@test.com'},
                    {
                        'id': 2,
                        'displayName': 'Jane Smith',
                        'workEmail': 'jane@test.com',
                    },
                ]
            }

            mock_response = AsyncMock()
            mock_response.ok = True
            mock_response.json.return_value = response_data

            mock_context_manager = MagicMock()
            mock_context_manager.__aenter__ = AsyncMock(return_value=mock_response)
            mock_context_manager.__aexit__ = AsyncMock(return_value=None)

            mock_session = MagicMock()
            mock_session.get = MagicMock(return_value=mock_context_manager)
            mock_session.close = AsyncMock()

            with patch('aiohttp.ClientSession', return_value=mock_session):
                api = create_api(api_key='test-api-key')

                async with api:
                    result = await api.get_employees()

                    assert len(result) == 2
                    assert result[0]['displayName'] == 'John Doe'
                    assert result[1]['displayName'] == 'Jane Smith'

                    # Verify the correct URL was called
                    mock_session.get.assert_called_with(
                        'https://api.bamboohr.com/api/gateway.php/testcompany/v1/employees/directory',
                        params=MultiDict(),
                    )
