# pylint: disable=C0114,C0115,C0116
from unittest.mock import AsyncMock, MagicMock, patch

import pytest as pt
from multidict import MultiDict

from wrench.core.api.backstage import API, APIBase, HTTPError, Method, create_api


class TestHTTPError:
    def test_http_error_inheritance(self):
        error = HTTPError('Test error')
        assert isinstance(error, Exception)
        assert str(error) == 'Test error'


class TestMethod:
    def test_method_enum_values(self):
        assert Method.GET_ENTITIES_BY_QUERY == 'entities/by-query'
        assert Method.GET_ENTITIES == 'entities'
        assert isinstance(Method.GET_ENTITIES_BY_QUERY, str)
        assert isinstance(Method.GET_ENTITIES, str)


class TestAPIBase:
    @patch('wrench.core.api.backstage.read_config')
    def test_init(self, mock_read_config):
        mock_read_config.return_value = {
            'BACKSTAGE_BASE_URL': 'https://api.example.com/'
        }
        api = APIBase()

        assert api.headers == {'Accept': 'application/json'}
        assert api._session is None

    @patch('wrench.core.api.backstage.read_config')
    def test_base_url_strips_trailing_slash(self, mock_read_config):
        mock_read_config.return_value = {
            'BACKSTAGE_BASE_URL': 'https://api.example.com/'
        }
        api = APIBase()

        assert api.base_url == 'https://api.example.com'

    @patch('wrench.core.api.backstage.read_config')
    def test_base_url_no_trailing_slash(self, mock_read_config):
        mock_read_config.return_value = {
            'BACKSTAGE_BASE_URL': 'https://api.example.com'
        }
        api = APIBase()

        assert api.base_url == 'https://api.example.com'

    @patch('wrench.core.api.backstage.read_config')
    def test_url_for_without_params(self, mock_read_config):
        mock_read_config.return_value = {
            'BACKSTAGE_BASE_URL': 'https://api.example.com'
        }
        api = APIBase()

        url = api.url_for(Method.GET_ENTITIES_BY_QUERY, None)
        assert url == 'https://api.example.com/entities/by-query'

    @patch('wrench.core.api.backstage.read_config')
    def test_url_for_with_params(self, mock_read_config):
        mock_read_config.return_value = {
            'BACKSTAGE_BASE_URL': 'https://api.example.com'
        }
        api = APIBase()

        # Note: Current implementation doesn't use string formatting for this method
        # but the test shows how it would work if params were used
        url = api.url_for(Method.GET_ENTITIES_BY_QUERY, {'param': 'value'})
        assert url == 'https://api.example.com/entities/by-query'

    @pt.mark.asyncio
    async def test_aenter_creates_session(self):
        with patch('wrench.core.api.backstage.read_config') as mock_read_config:
            mock_read_config.return_value = {
                'BACKSTAGE_BASE_URL': 'https://api.example.com'
            }
            api = APIBase()

            with patch('aiohttp.ClientSession') as mock_session_class:
                mock_session = MagicMock()
                mock_session_class.return_value = mock_session

                result = await api.__aenter__()

                assert api._session == mock_session
                assert result is None

    @pt.mark.asyncio
    async def test_aexit_closes_session(self):
        with patch('wrench.core.api.backstage.read_config') as mock_read_config:
            mock_read_config.return_value = {
                'BACKSTAGE_BASE_URL': 'https://api.example.com'
            }
            api = APIBase()

            mock_session = AsyncMock()
            api._session = mock_session

            await api.__aexit__(None, None, None)

            mock_session.close.assert_called_once()

    @pt.mark.asyncio
    async def test_aexit_no_session(self):
        with patch('wrench.core.api.backstage.read_config') as mock_read_config:
            mock_read_config.return_value = {
                'BACKSTAGE_BASE_URL': 'https://api.example.com'
            }
            api = APIBase()

            # Should not raise an error when _session is None
            await api.__aexit__(None, None, None)

    @pt.mark.asyncio
    async def test_get_success(self):
        with patch('wrench.core.api.backstage.read_config') as mock_read_config:
            mock_read_config.return_value = {
                'BACKSTAGE_BASE_URL': 'https://api.example.com'
            }
            api = APIBase()

            mock_response = AsyncMock()
            mock_response.ok = True
            mock_response.json.return_value = {'data': 'test'}

            mock_context_manager = MagicMock()
            mock_context_manager.__aenter__ = AsyncMock(return_value=mock_response)
            mock_context_manager.__aexit__ = AsyncMock(return_value=None)

            mock_session = MagicMock()
            mock_session.get = MagicMock(return_value=mock_context_manager)
            api._session = mock_session

            result = await api._get(
                Method.GET_ENTITIES_BY_QUERY, None, {'param': 'value'}
            )

            assert result == {'data': 'test'}
            mock_session.get.assert_called_once_with(
                'https://api.example.com/entities/by-query', params={'param': 'value'}
            )

    @pt.mark.asyncio
    async def test_get_http_error(self):
        with patch('wrench.core.api.backstage.read_config') as mock_read_config:
            mock_read_config.return_value = {
                'BACKSTAGE_BASE_URL': 'https://api.example.com'
            }
            api = APIBase()

            mock_response = AsyncMock()
            mock_response.ok = False
            mock_response.status = 404

            mock_context_manager = MagicMock()
            mock_context_manager.__aenter__ = AsyncMock(return_value=mock_response)
            mock_context_manager.__aexit__ = AsyncMock(return_value=None)

            mock_session = MagicMock()
            mock_session.get = MagicMock(return_value=mock_context_manager)
            api._session = mock_session

            with pt.raises(HTTPError) as exc_info:
                await api._get(Method.GET_ENTITIES_BY_QUERY, None, None)

            assert 'Error calling API method' in str(exc_info.value)
            assert '404' in str(exc_info.value)

    @pt.mark.asyncio
    async def test_mget_single_page(self):
        with patch('wrench.core.api.backstage.read_config') as mock_read_config:
            mock_read_config.return_value = {
                'BACKSTAGE_BASE_URL': 'https://api.example.com'
            }
            api = APIBase()

            mock_response_data = {'items': [{'id': 1}, {'id': 2}], 'pageInfo': {}}

            mock_response = AsyncMock()
            mock_response.ok = True
            mock_response.json.return_value = mock_response_data

            mock_context_manager = MagicMock()
            mock_context_manager.__aenter__ = AsyncMock(return_value=mock_response)
            mock_context_manager.__aexit__ = AsyncMock(return_value=None)

            mock_session = MagicMock()
            mock_session.get = MagicMock(return_value=mock_context_manager)
            api._session = mock_session

            query_params = MultiDict([('filter', 'test')])
            result = await api._mget(Method.GET_ENTITIES_BY_QUERY, None, query_params)

            assert result == [{'id': 1}, {'id': 2}]
            mock_session.get.assert_called_once()

    @pt.mark.asyncio
    async def test_mget_multiple_pages(self):
        with patch('wrench.core.api.backstage.read_config') as mock_read_config:
            mock_read_config.return_value = {
                'BACKSTAGE_BASE_URL': 'https://api.example.com'
            }
            api = APIBase()

            # First page response
            first_response_data = {
                'items': [{'id': 1}, {'id': 2}],
                'pageInfo': {'nextCursor': 'cursor123'},
            }

            # Second page response
            second_response_data = {'items': [{'id': 3}, {'id': 4}], 'pageInfo': {}}

            mock_response_1 = AsyncMock()
            mock_response_1.ok = True
            mock_response_1.json.return_value = first_response_data

            mock_response_2 = AsyncMock()
            mock_response_2.ok = True
            mock_response_2.json.return_value = second_response_data

            mock_context_manager_1 = MagicMock()
            mock_context_manager_1.__aenter__ = AsyncMock(return_value=mock_response_1)
            mock_context_manager_1.__aexit__ = AsyncMock(return_value=None)

            mock_context_manager_2 = MagicMock()
            mock_context_manager_2.__aenter__ = AsyncMock(return_value=mock_response_2)
            mock_context_manager_2.__aexit__ = AsyncMock(return_value=None)

            mock_session = MagicMock()
            mock_session.get = MagicMock(
                side_effect=[mock_context_manager_1, mock_context_manager_2]
            )
            api._session = mock_session

            query_params = MultiDict([('filter', 'test')])
            result = await api._mget(Method.GET_ENTITIES_BY_QUERY, None, query_params)

            assert result == [{'id': 1}, {'id': 2}, {'id': 3}, {'id': 4}]
            assert mock_session.get.call_count == 2
            # Check that cursor was added to second request
            assert 'cursor' in query_params

    @pt.mark.asyncio
    async def test_mget_http_error(self):
        with patch('wrench.core.api.backstage.read_config') as mock_read_config:
            mock_read_config.return_value = {
                'BACKSTAGE_BASE_URL': 'https://api.example.com'
            }
            api = APIBase()

            mock_response = AsyncMock()
            mock_response.ok = False

            mock_context_manager = MagicMock()
            mock_context_manager.__aenter__ = AsyncMock(return_value=mock_response)
            mock_context_manager.__aexit__ = AsyncMock(return_value=None)

            mock_session = MagicMock()
            mock_session.get = MagicMock(return_value=mock_context_manager)
            api._session = mock_session

            query_params = MultiDict([('filter', 'test')])

            with pt.raises(HTTPError):
                await api._mget(Method.GET_ENTITIES_BY_QUERY, None, query_params)


class TestAPI:
    @pt.mark.asyncio
    async def test_get_entities_by_query_success(self):
        with patch('wrench.core.api.backstage.read_config') as mock_read_config:
            mock_read_config.return_value = {
                'BACKSTAGE_BASE_URL': 'https://api.example.com'
            }
            api = API()

            expected_result = [{'id': 1}, {'id': 2}]

            with patch.object(api, '_mget', return_value=expected_result) as mock_mget:
                query_params = MultiDict([('filter', 'test')])
                result = await api.get_entities_by_query(query_params=query_params)

                assert result == expected_result
                mock_mget.assert_called_once_with(
                    Method.GET_ENTITIES_BY_QUERY, params=None, query_params=query_params
                )

    @pt.mark.asyncio
    async def test_get_entities_by_query_with_params(self):
        with patch('wrench.core.api.backstage.read_config') as mock_read_config:
            mock_read_config.return_value = {
                'BACKSTAGE_BASE_URL': 'https://api.example.com'
            }
            api = API()

            expected_result = [{'id': 1}]
            params = {'namespace': 'default'}

            with patch.object(api, '_mget', return_value=expected_result) as mock_mget:
                query_params = MultiDict([('filter', 'test')])
                result = await api.get_entities_by_query(
                    params=params, query_params=query_params
                )

                assert result == expected_result
                mock_mget.assert_called_once_with(
                    Method.GET_ENTITIES_BY_QUERY,
                    params=params,
                    query_params=query_params,
                )

    @pt.mark.asyncio
    async def test_get_entities_by_query_http_error_returns_empty_list(self):
        with patch('wrench.core.api.backstage.read_config') as mock_read_config:
            mock_read_config.return_value = {
                'BACKSTAGE_BASE_URL': 'https://api.example.com'
            }
            api = API()

            with patch.object(
                api, '_mget', side_effect=HTTPError('API Error')
            ) as mock_mget:
                query_params = MultiDict([('filter', 'test')])
                result = await api.get_entities_by_query(query_params=query_params)

                assert result == []
                mock_mget.assert_called_once()

    @pt.mark.asyncio
    async def test_get_entities_success(self):
        with patch('wrench.core.api.backstage.read_config') as mock_read_config:
            mock_read_config.return_value = {
                'BACKSTAGE_BASE_URL': 'https://api.example.com'
            }
            api = API()

            expected_result = [{'id': 1}, {'id': 2}]

            with patch.object(api, '_mget', return_value=expected_result) as mock_mget:
                result = await api.get_entities()

                assert result == expected_result
                mock_mget.assert_called_once_with(
                    Method.GET_ENTITIES, params=None, query_params=MultiDict()
                )

    @pt.mark.asyncio
    async def test_get_entities_with_params_and_query_params(self):
        with patch('wrench.core.api.backstage.read_config') as mock_read_config:
            mock_read_config.return_value = {
                'BACKSTAGE_BASE_URL': 'https://api.example.com'
            }
            api = API()

            expected_result = [{'id': 1}]
            params = {'namespace': 'default'}
            query_params = MultiDict([('kind', 'Component')])

            with patch.object(api, '_mget', return_value=expected_result) as mock_mget:
                result = await api.get_entities(
                    params=params, query_params=query_params
                )

                assert result == expected_result
                mock_mget.assert_called_once_with(
                    Method.GET_ENTITIES, params=params, query_params=query_params
                )

    @pt.mark.asyncio
    async def test_get_entities_http_error_returns_empty_list(self):
        with patch('wrench.core.api.backstage.read_config') as mock_read_config:
            mock_read_config.return_value = {
                'BACKSTAGE_BASE_URL': 'https://api.example.com'
            }
            api = API()

            with patch.object(
                api, '_mget', side_effect=HTTPError('API Error')
            ) as mock_mget:
                result = await api.get_entities()

                assert result == []
                mock_mget.assert_called_once()


class TestCreateAPI:
    def test_create_api_returns_api_instance(self):
        with patch('wrench.core.api.backstage.read_config') as mock_read_config:
            mock_read_config.return_value = {
                'BACKSTAGE_BASE_URL': 'https://api.example.com'
            }
            api = create_api()

            assert isinstance(api, API)
            assert isinstance(api, APIBase)


class TestIntegration:
    @pt.mark.asyncio
    async def test_context_manager_usage(self):
        with patch('wrench.core.api.backstage.read_config') as mock_read_config:
            mock_read_config.return_value = {
                'BACKSTAGE_BASE_URL': 'https://api.example.com'
            }

            mock_session = AsyncMock()

            with patch('aiohttp.ClientSession', return_value=mock_session):
                api = create_api()

                async with api:
                    assert api._session == mock_session

                mock_session.close.assert_called_once()

    @pt.mark.asyncio
    async def test_full_workflow_with_mocked_responses(self):
        with patch('wrench.core.api.backstage.read_config') as mock_read_config:
            mock_read_config.return_value = {
                'BACKSTAGE_BASE_URL': 'https://api.example.com'
            }

            # Mock response data
            response_data = {
                'items': [
                    {'kind': 'Component', 'metadata': {'name': 'service-1'}},
                    {'kind': 'Component', 'metadata': {'name': 'service-2'}},
                ],
                'pageInfo': {},
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
                api = create_api()

                async with api:
                    query_params = MultiDict([('filter', 'kind=component')])
                    result = await api.get_entities_by_query(query_params=query_params)

                    assert len(result) == 2
                    assert result[0]['metadata']['name'] == 'service-1'
                    assert result[1]['metadata']['name'] == 'service-2'

                    # Verify the correct URL was called
                    mock_session.get.assert_called_with(
                        'https://api.example.com/entities/by-query', params=query_params
                    )
