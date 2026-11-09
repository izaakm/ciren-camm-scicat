import pytest
from unittest.mock import Mock, patch, MagicMock
from urllib.parse import quote_plus
import json

from cammcat.client import CAMMClient, get_client
from pyscicat.client import ScicatLoginError


# ========================================================================
# Fixtures
# ========================================================================

@pytest.fixture
def make_client():
    '''Factory for CAMMClient with sensible defaults.'''
    def _make(**overrides):
        kwargs = dict(
            base_url='http://localhost:3000/api/v3',
            token=None,
            username='testuser',
            password='testpass',
            timeout_seconds=30,
            auto_login=False,
            auth_method='ldap',
            verify=True,
        )
        kwargs.update(overrides)
        return CAMMClient(**kwargs)
    return _make


@pytest.fixture
def make_mock_response():
    '''Factory for mock Response objects.'''
    def _make(ok=True, json_data=None, status_code=200, text='', content=b''):
        response = Mock()
        response.ok = ok
        response.status_code = status_code
        response.text = text
        response.content = content
        response.json.return_value = json_data or {}
        response.raise_for_status.side_effect = None if ok else Exception('HTTP Error')
        return response
    return _make


# ========================================================================
# __init__ Tests
# ========================================================================

class TestCAMMClientInit:
    '''Test CAMMClient initialization.'''

    def test_init_with_token_no_login(self, make_client):
        '''Token provided → no login attempt, Authorization header set.'''
        client = make_client(token='mytoken', auto_login=False)
        assert client._token == 'mytoken'
        assert client._headers['Authorization'] == 'Bearer mytoken'

    def test_init_with_token_ignores_credentials(self, make_client):
        '''Token provided → username/password ignored.'''
        client = make_client(token='mytoken', username=None, password=None)
        assert client._token == 'mytoken'

    def test_init_without_token_requires_credentials(self, make_client):
        '''Missing credentials without token → raises ValueError.'''
        with pytest.raises(ValueError, match='SciCat login credentials'):
            make_client(token=None, username=None, password='pass')

    def test_init_without_token_missing_password(self, make_client):
        '''Missing password without token → raises ValueError.'''
        with pytest.raises(ValueError, match='SciCat login credentials'):
            make_client(token=None, username='user', password=None)

    def test_init_strips_trailing_slash_from_base_url(self, make_client):
        '''base_url trailing slash stripped.'''
        client = make_client(base_url='http://localhost:3000/api/v3/')
        assert client._base_url == 'http://localhost:3000/api/v3'

    def test_init_multiple_trailing_slashes_stripped(self, make_client):
        '''Multiple trailing slashes stripped.'''
        client = make_client(base_url='http://localhost:3000/api/v3///')
        assert client._base_url == 'http://localhost:3000/api/v3'

    def test_init_empty_base_url_warns(self, make_client):
        '''Empty base_url → warns but proceeds.'''
        with pytest.warns(UserWarning, match='base_url not specified or empty'):
            client = make_client(base_url='')
        assert client._base_url == ''

    def test_init_none_base_url_warns(self, make_client):
        '''None base_url → warns but proceeds.'''
        with pytest.warns(UserWarning, match='base_url not specified or empty'):
            client = make_client(base_url=None)
        assert client._base_url is None

    def test_init_stores_auth_method(self, make_client):
        '''auth_method stored correctly.'''
        client = make_client(auth_method='login')
        assert client._auth_method == 'login'

    def test_init_stores_verify(self, make_client):
        '''verify parameter stored correctly.'''
        client = make_client(verify=False)
        assert client._verify is False

    def test_init_stores_timeout(self, make_client):
        '''timeout_seconds stored correctly.'''
        client = make_client(timeout_seconds=60)
        assert client._timeout_seconds == 60

    @patch('cammcat.client.CAMMClient.login')
    def test_init_auto_login_true_calls_login(self, mock_login, make_client):
        '''auto_login=True → calls login().'''
        make_client(auto_login=True)
        mock_login.assert_called_once()

    @patch('cammcat.client.CAMMClient.login')
    def test_init_auto_login_false_skips_login(self, mock_login, make_client):
        '''auto_login=False → no login attempt.'''
        make_client(auto_login=False)
        mock_login.assert_not_called()


# ========================================================================
# _make_limits Tests
# ========================================================================

class TestMakeLimits:
    '''Test _make_limits filter construction.'''

    def test_make_limits_all_none(self, make_client):
        '''All None → empty dict.'''
        client = make_client()
        limits = client._make_limits()
        assert limits == {}

    def test_make_limits_skip_only(self, make_client):
        '''skip only → dict with skip.'''
        client = make_client()
        limits = client._make_limits(skip=10)
        assert limits == {'skip': 10}

    def test_make_limits_limit_only(self, make_client):
        '''limit only → dict with limit + default order.'''
        client = make_client()
        limits = client._make_limits(limit=20)
        assert limits == {'limit': 20, 'order': 'createdAt:desc'}

    def test_make_limits_skip_and_limit(self, make_client):
        '''skip and limit → both included with default order.'''
        client = make_client()
        limits = client._make_limits(skip=5, limit=10)
        assert limits == {'skip': 5, 'limit': 10, 'order': 'createdAt:desc'}

    def test_make_limits_order_by_only(self, make_client):
        '''order_by only → dict with order_by.'''
        client = make_client()
        limits = client._make_limits(order_by='name:asc')
        assert limits == {'order': 'name:asc'}

    def test_make_limits_limit_and_order_by(self, make_client):
        '''limit + order_by → order_by takes precedence.'''
        client = make_client()
        limits = client._make_limits(limit=10, order_by='name:asc')
        assert limits == {'limit': 10, 'order': 'name:asc'}

    def test_make_limits_all_parameters(self, make_client):
        '''skip + limit + order_by → all included, order_by wins.'''
        client = make_client()
        limits = client._make_limits(skip=5, limit=10, order_by='updatedAt:desc')
        assert limits == {'skip': 5, 'limit': 10, 'order': 'updatedAt:desc'}


# ========================================================================
# datasets_create Tests
# ========================================================================

class TestDatasetsCreate:
    '''Test datasets_create method.'''

    @patch('cammcat.client.requests.post')
    def test_datasets_create_success(self, mock_post, make_client, make_mock_response):
        '''Successful POST returns response dict.'''
        response_data = {'pid': 'dataset-123', 'name': 'test'}
        mock_post.return_value = make_mock_response(ok=True, json_data=response_data)
        
        client = make_client(token='mytoken')
        mock_dataset = Mock()
        mock_dataset.model_dump.return_value = {
            'name': 'test',
            'createdBy': 'user',
            'updatedBy': 'user',
            'createdAt': '2024-01-01',
            'updatedAt': '2024-01-01',
            'history': [],
            'size': 100,
        }
        
        result = client.datasets_create(mock_dataset)
        assert result == response_data

    @patch('cammcat.client.requests.post')
    def test_datasets_create_excludes_readonly_fields(self, mock_post, make_client, make_mock_response):
        '''Excludes readonly fields from payload.'''
        mock_post.return_value = make_mock_response(ok=True, json_data={'pid': '123'})
        
        client = make_client(token='mytoken')
        mock_dataset = Mock()
        mock_dataset.model_dump.return_value = {
            'name': 'test',
            'createdBy': 'user',
            'updatedBy': 'user',
            'createdAt': '2024-01-01',
            'updatedAt': '2024-01-01',
            'history': [],
        }
        
        client.datasets_create(mock_dataset)
        
        # Verify model_dump was called with correct exclusions
        mock_dataset.model_dump.assert_called_once()
        call_kwargs = mock_dataset.model_dump.call_args[1]
        assert 'createdBy' in call_kwargs.get('exclude', set())
        assert 'updatedBy' in call_kwargs.get('exclude', set())
        assert 'createdAt' in call_kwargs.get('exclude', set())
        assert 'updatedAt' in call_kwargs.get('exclude', set())
        assert 'history' in call_kwargs.get('exclude', set())

    @patch('cammcat.client.requests.post')
    def test_datasets_create_uses_correct_url(self, mock_post, make_client, make_mock_response):
        '''POST to correct endpoint.'''
        mock_post.return_value = make_mock_response(ok=True, json_data={'pid': '123'})
        
        client = make_client(base_url='http://localhost:3000/api/v3', token='mytoken')
        mock_dataset = Mock()
        mock_dataset.model_dump.return_value = {}
        
        client.datasets_create(mock_dataset)
        
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert call_args[1]['url'] == 'http://localhost:3000/api/v3/datasets'

    @patch('cammcat.client.requests.post')
    def test_datasets_create_uses_correct_headers(self, mock_post, make_client, make_mock_response):
        '''Uses Authorization header.'''
        mock_post.return_value = make_mock_response(ok=True, json_data={'pid': '123'})
        
        client = make_client(token='mytoken')
        mock_dataset = Mock()
        mock_dataset.model_dump.return_value = {}
        
        client.datasets_create(mock_dataset)
        
        call_args = mock_post.call_args
        assert call_args[1]['headers']['Authorization'] == 'Bearer mytoken'

    @patch('cammcat.client.requests.post')
    def test_datasets_create_uses_timeout(self, mock_post, make_client, make_mock_response):
        '''Passes timeout to requests.'''
        mock_post.return_value = make_mock_response(ok=True, json_data={'pid': '123'})
        
        client = make_client(timeout_seconds=45, token='mytoken')
        mock_dataset = Mock()
        mock_dataset.model_dump.return_value = {}
        
        client.datasets_create(mock_dataset)
        
        call_args = mock_post.call_args
        assert call_args[1]['timeout'] == 45

    @patch('cammcat.client.requests.post')
    def test_datasets_create_uses_verify(self, mock_post, make_client, make_mock_response):
        '''Passes verify parameter to requests.'''
        mock_post.return_value = make_mock_response(ok=True, json_data={'pid': '123'})
        
        client = make_client(verify=False, token='mytoken')
        mock_dataset = Mock()
        mock_dataset.model_dump.return_value = {}
        
        client.datasets_create(mock_dataset)
        
        call_args = mock_post.call_args
        assert call_args[1]['verify'] is False

    @patch('cammcat.client.requests.post')
    def test_datasets_create_raises_on_error(self, mock_post, make_client, make_mock_response):
        '''Non-2xx response → raises.'''
        response = make_mock_response(ok=False, status_code=400)
        response.raise_for_status.side_effect = Exception('400 Bad Request')
        mock_post.return_value = response
        
        client = make_client(token='mytoken')
        mock_dataset = Mock()
        mock_dataset.model_dump.return_value = {}
        
        with pytest.raises(Exception):
            client.datasets_create(mock_dataset)


# ========================================================================
# datasets_get_one Tests
# ========================================================================

class TestDatasetsGetOne:
    '''Test datasets_get_one method.'''

    @patch('cammcat.client.requests.request')
    def test_datasets_get_one_success(self, mock_request, make_client, make_mock_response):
        '''Successful GET returns dataset dict.'''
        response_data = {'pid': 'dataset-123', 'name': 'test'}
        mock_request.return_value = make_mock_response(ok=True, json_data=response_data)
        
        client = make_client(token='mytoken')
        result = client.datasets_get_one('dataset-123')
        
        assert result == response_data

    @patch('cammcat.client.requests.request')
    def test_datasets_get_one_url_encodes_pid(self, mock_request, make_client, make_mock_response):
        '''pid URL-encoded with quote_plus.'''
        mock_request.return_value = make_mock_response(ok=True, json_data={})
        
        client = make_client(base_url='http://localhost:3000/api/v3', token='mytoken')
        pid = 'dataset/with spaces'
        client.datasets_get_one(pid)
        
        call_args = mock_request.call_args
        expected_url = f'http://localhost:3000/api/v3/datasets/{quote_plus(pid)}'
        assert call_args[1]['url'] == expected_url

    @patch('cammcat.client.requests.request')
    def test_datasets_get_one_uses_correct_method(self, mock_request, make_client, make_mock_response):
        '''Uses GET method.'''
        mock_request.return_value = make_mock_response(ok=True, json_data={})
        
        client = make_client(token='mytoken')
        client.datasets_get_one('dataset-123')
        
        call_args = mock_request.call_args
        assert call_args[1]['method'] == 'GET'

    @patch('cammcat.client.requests.request')
    def test_datasets_get_one_uses_correct_headers(self, mock_request, make_client, make_mock_response):
        '''Uses Authorization header.'''
        mock_request.return_value = make_mock_response(ok=True, json_data={})
        
        client = make_client(token='mytoken')
        client.datasets_get_one('dataset-123')
        
        call_args = mock_request.call_args
        assert call_args[1]['headers']['Authorization'] == 'Bearer mytoken'

    @patch('cammcat.client.requests.request')
    def test_datasets_get_one_uses_timeout(self, mock_request, make_client, make_mock_response):
        '''Passes timeout to requests.'''
        mock_request.return_value = make_mock_response(ok=True, json_data={})
        
        client = make_client(timeout_seconds=50, token='mytoken')
        client.datasets_get_one('dataset-123')
        
        call_args = mock_request.call_args
        assert call_args[1]['timeout'] == 50

    @patch('cammcat.client.requests.request')
    def test_datasets_get_one_uses_verify(self, mock_request, make_client, make_mock_response):
        '''Passes verify parameter to requests.'''
        mock_request.return_value = make_mock_response(ok=True, json_data={})
        
        client = make_client(verify=False, token='mytoken')
        client.datasets_get_one('dataset-123')
        
        call_args = mock_request.call_args
        assert call_args[1]['verify'] is False

    @patch('cammcat.client.requests.request')
    def test_datasets_get_one_raises_on_error(self, mock_request, make_client, make_mock_response):
        '''Non-2xx response → raises.'''
        response = make_mock_response(ok=False, status_code=404)
        response.raise_for_status.side_effect = Exception('404 Not Found')
        mock_request.return_value = response
        
        client = make_client(token='mytoken')
        
        with pytest.raises(Exception):
            client.datasets_get_one('nonexistent')


# ========================================================================
# datasets_get_many Tests
# ========================================================================

class TestDatasetsGetMany:
    '''Test datasets_get_many method.'''

    @patch('cammcat.client.requests.request')
    def test_datasets_get_many_success(self, mock_request, make_client, make_mock_response):
        '''Successful GET returns list of datasets.'''
        response_data = [{'pid': 'ds1'}, {'pid': 'ds2'}]
        mock_request.return_value = make_mock_response(ok=True, json_data=response_data)
        
        client = make_client(token='mytoken')
        result = client.datasets_get_many()
        
        assert result == response_data

    @patch('cammcat.client.requests.request')
    def test_datasets_get_many_with_filter_fields(self, mock_request, make_client, make_mock_response):
        '''filter_fields → wrapped in "where" clause.'''
        mock_request.return_value = make_mock_response(ok=True, json_data=[])
        
        client = make_client(token='mytoken')
        client.datasets_get_many(filter_fields={'proposalId': '123'})
        
        call_args = mock_request.call_args
        params = call_args[1]['params']
        assert 'where' in params
        assert params['where'] == {'proposalId': '123'}

    @patch('cammcat.client.requests.request')
    def test_datasets_get_many_with_include_fields(self, mock_request, make_client, make_mock_response):
        '''include_fields → wrapped in "relation" objects.'''
        mock_request.return_value = make_mock_response(ok=True, json_data=[])
        
        client = make_client(token='mytoken')
        client.datasets_get_many(include_fields=['owner', 'instrument'])
        
        call_args = mock_request.call_args
        params = call_args[1]['params']
        assert 'include' in params
        assert params['include'] == [{'relation': 'owner'}, {'relation': 'instrument'}]

    @patch('cammcat.client.requests.request')
    def test_datasets_get_many_with_skip_limit(self, mock_request, make_client, make_mock_response):
        '''skip and limit → passed via limits.'''
        mock_request.return_value = make_mock_response(ok=True, json_data=[])
        
        client = make_client(token='mytoken')
        client.datasets_get_many(skip=10, limit=20)
        
        call_args = mock_request.call_args
        params = call_args[1]['params']
        assert params['limits']['skip'] == 10
        assert params['limits']['limit'] == 20

    @patch('cammcat.client.requests.request')
    def test_datasets_get_many_with_order_by(self, mock_request, make_client, make_mock_response):
        '''order_by → passed via limits.'''
        mock_request.return_value = make_mock_response(ok=True, json_data=[])
        
        client = make_client(token='mytoken')
        client.datasets_get_many(order_by='name:asc')
        
        call_args = mock_request.call_args
        params = call_args[1]['params']
        assert params['limits']['order'] == 'name:asc'

    @patch('cammcat.client.requests.request')
    def test_datasets_get_many_uses_correct_url(self, mock_request, make_client, make_mock_response):
        '''GET to correct endpoint.'''
        mock_request.return_value = make_mock_response(ok=True, json_data=[])
        
        client = make_client(base_url='http://localhost:3000/api/v3', token='mytoken')
        client.datasets_get_many()
        
        call_args = mock_request.call_args
        assert call_args[1]['url'] == 'http://localhost:3000/api/v3/datasets'

    @patch('cammcat.client.requests.request')
    def test_datasets_get_many_uses_correct_method(self, mock_request, make_client, make_mock_response):
        '''Uses GET method.'''
        mock_request.return_value = make_mock_response(ok=True, json_data=[])
        
        client = make_client(token='mytoken')
        client.datasets_get_many()
        
        call_args = mock_request.call_args
        assert call_args[1]['method'] == 'GET'

    @patch('cammcat.client.requests.request')
    def test_datasets_get_many_uses_correct_headers(self, mock_request, make_client, make_mock_response):
        '''Uses Authorization header.'''
        mock_request.return_value = make_mock_response(ok=True, json_data=[])
        
        client = make_client(token='mytoken')
        client.datasets_get_many()
        
        call_args = mock_request.call_args
        assert call_args[1]['headers']['Authorization'] == 'Bearer mytoken'

    @patch('cammcat.client.requests.request')
    def test_datasets_get_many_raises_on_error(self, mock_request, make_client, make_mock_response):
        '''Non-2xx response → raises.'''
        response = make_mock_response(ok=False, status_code=500)
        response.raise_for_status.side_effect = Exception('500 Server Error')
        mock_request.return_value = response
        
        client = make_client(token='mytoken')
        
        with pytest.raises(Exception):
            client.datasets_get_many()


# ========================================================================
# login Tests
# ========================================================================

class TestLogin:
    '''Test login method.'''

    @patch('cammcat.client.CAMMClient.get_token')
    def test_login_calls_get_token(self, mock_get_token, make_client):
        '''login calls get_token with stored credentials.'''
        mock_get_token.return_value = 'newtoken'
        
        client = make_client(
            base_url='http://localhost:3000/api/v3',
            username='user',
            password='pass',
            auto_login=False,
        )
        client.login()
        
        mock_get_token.assert_called_once()
        call_args = mock_get_token.call_args
        assert call_args[0][0] == 'http://localhost:3000/api/v3'
        assert call_args[0][1] == 'user'
        assert call_args[0][2] == 'pass'

    @patch('cammcat.client.CAMMClient.get_token')
    def test_login_sets_authorization_header(self, mock_get_token, make_client):
        '''login sets Authorization header with returned token.'''
        mock_get_token.return_value = 'newtoken'
        
        client = make_client(auto_login=False)
        client.login()
        
        assert client._headers['Authorization'] == 'Bearer newtoken'

    @patch('cammcat.client.CAMMClient.get_token')
    def test_login_stores_token(self, mock_get_token, make_client):
        '''login stores token in _token.'''
        mock_get_token.return_value = 'newtoken'
        
        client = make_client(auto_login=False)
        client.login()
        
        assert client._token == 'newtoken'


# ========================================================================
# get_token Tests
# ========================================================================

class TestGetToken:
    '''Test get_token method.'''

    @patch('cammcat.client.CAMMClient._log_in_via_users_login')
    def test_get_token_success(self, mock_login, make_client, make_mock_response):
        '''Successful response → returns token.'''
        response = make_mock_response(ok=True, json_data={'id': 'token123'})
        mock_login.return_value = response
        
        client = make_client()
        token = client.get_token('http://localhost:3000/api/v3', 'user', 'pass')
        
        assert token == 'token123'

    @patch('cammcat.client.CAMMClient._log_in_via_users_login')
    def test_get_token_calls_login_method(self, mock_login, make_client, make_mock_response):
        '''get_token calls _log_in_via_users_login.'''
        response = make_mock_response(ok=True, json_data={'id': 'token123'})
        mock_login.return_value = response
        
        client = make_client()
        client.get_token('http://localhost:3000/api/v3', 'user', 'pass', headers={'X-Custom': 'header'})
        
        mock_login.assert_called_once()
        call_args = mock_login.call_args
        assert call_args[0][0] == 'http://localhost:3000/api/v3'
        assert call_args[0][1] == 'user'
        assert call_args[0][2] == 'pass'

    @patch('cammcat.client.CAMMClient._log_in_via_users_login')
    def test_get_token_failure_raises_login_error(self, mock_login, make_client, make_mock_response):
        '''Failed response → raises ScicatLoginError.'''
        response = make_mock_response(ok=False, status_code=401, content=b'Unauthorized')
        response.json.side_effect = json.JSONDecodeError('msg', 'doc', 0)
        mock_login.return_value = response
        
        client = make_client()
        
        with pytest.raises(ScicatLoginError):
            client.get_token('http://localhost:3000/api/v3', 'user', 'pass')

    @patch('cammcat.client.CAMMClient._log_in_via_users_login')
    def test_get_token_failure_with_json_error_response(self, mock_login, make_client, make_mock_response):
        '''Failed response with JSON error → raises ScicatLoginError.'''
        response = make_mock_response(ok=False, status_code=401, json_data={'error': 'Invalid credentials'})
        mock_login.return_value = response
        
        client = make_client()
        
        with pytest.raises(ScicatLoginError):
            client.get_token('http://localhost:3000/api/v3', 'user', 'pass')

    @patch('cammcat.client.CAMMClient._log_in_via_users_login')
    def test_get_token_failure_json_decode_error(self, mock_login, make_client, make_mock_response):
        '''Failed response with unparseable JSON → raises ScicatLoginError.'''
        response = make_mock_response(ok=False, status_code=500, text='Internal Server Error')
        response.json.side_effect = json.JSONDecodeError('msg', 'doc', 0)
        mock_login.return_value = response
        
        client = make_client()
        
        with pytest.raises(ScicatLoginError):
            client.get_token('http://localhost:3000/api/v3', 'user', 'pass')


# ========================================================================
# _log_in_via_users_login Tests
# ========================================================================

class TestLogInViaUsersLogin:
    '''Test _log_in_via_users_login method.'''

    @patch('cammcat.client.requests.post')
    def test_log_in_via_users_login_ldap(self, mock_post, make_client, make_mock_response):
        '''auth_method="ldap" → uses /auth/ldap endpoint.'''
        mock_post.return_value = make_mock_response(ok=True, json_data={'id': 'token'})
        
        client = make_client(auth_method='ldap')
        response = client._log_in_via_users_login('http://localhost:3000/api/v3', 'user', 'pass')
        
        call_args = mock_post.call_args
        assert call_args[0][0] == 'http://localhost:3000/api/v3/auth/ldap'

    @patch('cammcat.client.requests.post')
    def test_log_in_via_users_login_ldap_case_insensitive(self, mock_post, make_client, make_mock_response):
        '''auth_method case-insensitive for ldap.'''
        mock_post.return_value = make_mock_response(ok=True, json_data={'id': 'token'})
        
        client = make_client(auth_method='LDAP')
        response = client._log_in_via_users_login('http://localhost:3000/api/v3', 'user', 'pass')
        
        call_args = mock_post.call_args
        assert call_args[0][0] == 'http://localhost:3000/api/v3/auth/ldap'

    @patch('cammcat.client.requests.post')
    def test_log_in_via_users_login_login_method(self, mock_post, make_client, make_mock_response):
        '''auth_method="login" → uses /auth/login endpoint.'''
        mock_post.return_value = make_mock_response(ok=True, json_data={'id': 'token'})
        
        client = make_client(auth_method='login')
        response = client._log_in_via_users_login('http://localhost:3000/api/v3', 'user', 'pass')
        
        call_args = mock_post.call_args
        assert call_args[0][0] == 'http://localhost:3000/api/v3/auth/login'

    @patch('cammcat.client.requests.post')
    def test_log_in_via_users_login_posts_credentials(self, mock_post, make_client, make_mock_response):
        '''POSTs credentials as JSON.'''
        mock_post.return_value = make_mock_response(ok=True, json_data={'id': 'token'})
        
        client = make_client()
        client._log_in_via_users_login('http://localhost:3000/api/v3', 'testuser', 'testpass')
        
        call_args = mock_post.call_args
        assert call_args[1]['json'] == {'username': 'testuser', 'password': 'testpass'}

    @patch('cammcat.client.requests.post')
    def test_log_in_via_users_login_success(self, mock_post, make_client, make_mock_response):
        '''Successful response → returns response object.'''
        response = make_mock_response(ok=True, json_data={'id': 'token'})
        mock_post.return_value = response
        
        client = make_client()
        result = client._log_in_via_users_login('http://localhost:3000/api/v3', 'user', 'pass')
        
        assert result == response

    @patch('cammcat.client.requests.post')
    def test_log_in_via_users_login_uses_verify(self, mock_post, make_client, make_mock_response):
        '''Passes verify parameter to requests.'''
        mock_post.return_value = make_mock_response(ok=True, json_data={'id': 'token'})
        
        client = make_client(verify=False)
        client._log_in_via_users_login('http://localhost:3000/api/v3', 'user', 'pass')
        
        call_args = mock_post.call_args
        assert call_args[1]['verify'] is False

    @patch('cammcat.client.requests.post')
    def test_log_in_via_users_login_failure_raises(self, mock_post, make_client, make_mock_response):
        '''Non-2xx response → raises.'''
        response = make_mock_response(ok=False, status_code=401)
        response.raise_for_status.side_effect = Exception('401 Unauthorized')
        mock_post.return_value = response
        
        client = make_client()
        
        with pytest.raises(Exception):
            client._log_in_via_users_login('http://localhost:3000/api/v3', 'user', 'pass')

    @patch('cammcat.client.requests.post')
    def test_log_in_via_users_login_failure_json_error(self, mock_post, make_client, make_mock_response):
        '''Failed response with JSON decode error → logs and raises.'''
        response = make_mock_response(ok=False, status_code=500, text='Server Error')
        response.json.side_effect = json.JSONDecodeError('msg', 'doc', 0)
        response.raise_for_status.side_effect = Exception('500 Server Error')
        mock_post.return_value = response
        
        client = make_client()
        
        with pytest.raises(Exception):
            client._log_in_via_users_login('http://localhost:3000/api/v3', 'user', 'pass')


# ========================================================================
# get_client Function Tests
# ========================================================================

class TestGetClientFunction:
    '''Test get_client factory function.'''

    def test_get_client_returns_camm_client(self):
        '''get_client returns CAMMClient instance.'''
        client = get_client(
            token='mytoken',
            base_url='http://localhost:3000/api/v3'
        )
        assert isinstance(client, CAMMClient)

    def test_get_client_passes_parameters(self):
        '''get_client passes parameters to CAMMClient.'''
        client = get_client(
            token='mytoken',
            username='user',
            password='pass',
            base_url='http://localhost:3000/api/v3'
        )
        assert client._token == 'mytoken'
        assert client._username == 'user'
        assert client._password == 'pass'
        assert client._base_url == 'http://localhost:3000/api/v3'

    def test_get_client_default_base_url(self):
        '''get_client uses empty string as default base_url.'''
        with pytest.warns(UserWarning):
            client = get_client(token='mytoken')
        assert client._base_url == ''


# ========================================================================
# Backwards Compatibility Aliases
# ========================================================================

class TestBackwardsCompatibilityAliases:
    '''Test that old method names still work.'''

    @patch('cammcat.client.requests.post')
    def test_upload_new_dataset_alias(self, mock_post, make_client, make_mock_response):
        '''upload_new_dataset is an alias for datasets_create.'''
        mock_post.return_value = make_mock_response(ok=True, json_data={'pid': '123'})
        
        client = make_client(token='mytoken')
        mock_dataset = Mock()
        mock_dataset.model_dump.return_value = {}
        
        result = client.upload_new_dataset(mock_dataset)
        assert result == {'pid': '123'}

    @patch('cammcat.client.requests.post')
    def test_create_dataset_alias(self, mock_post, make_client, make_mock_response):
        '''create_dataset is an alias for datasets_create.'''
        mock_post.return_value = make_mock_response(ok=True, json_data={'pid': '123'})
        
        client = make_client(token='mytoken')
        mock_dataset = Mock()
        mock_dataset.model_dump.return_value = {}
        
        result = client.create_dataset(mock_dataset)
        assert result == {'pid': '123'}

    @patch('cammcat.client.requests.request')
    def test_get_dataset_by_pid_alias(self, mock_request, make_client, make_mock_response):
        '''get_dataset_by_pid is an alias for datasets_get_one.'''
        mock_request.return_value = make_mock_response(ok=True, json_data={'pid': '123'})
        
        client = make_client(token='mytoken')
        result = client.get_dataset_by_pid('123')
        
        assert result == {'pid': '123'}

    @patch('cammcat.client.requests.request')
    def test_get_datasets_alias(self, mock_request, make_client, make_mock_response):
        '''get_datasets is an alias for datasets_get_many.'''
        mock_request.return_value = make_mock_response(ok=True, json_data=[{'pid': '123'}])
        
        client = make_client(token='mytoken')
        result = client.get_datasets()
        
        assert result == [{'pid': '123'}]
