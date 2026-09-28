import logging
import requests

from pyscicat.client import *

from pyscicat.model import (
    Attachment,
    CreateDatasetOrigDatablockDto,
    DataFile,
    DatasetType,
    Ownable,
    RawDataset,
)

logger = logging.getLogger(__name__)

# ========================================================================
# Client
# ========================================================================
# I'm not sure if the "client" should be a subclass of ScicatClient or just a fxn.
class CAMMClient(ScicatClient):
    '''
    Difference from ScicatClient:
        
        __init__
            -> add "auth method"
        login
            -> calls self.get_token (instead of pyscicat.client.get_token)
        get_token
            -> moved pyscicat.client.get_token to self.get_token
            -> call self._log_in_via_users_login instead of pyscicat.client.*
        _log_in_via_users_login
            -> enable ldap login
    '''

    def __init__(
            self,
            base_url: str,
            token: Optional[str] = None,
            username: Optional[str] = None,
            password: Optional[str] = None,
            timeout_seconds: Optional[int] = None,
            auto_login=True,
            auth_method="ldap",
            verify=True
        ):
        """Initialize a new instance. This method attempts to create a token
        from the provided username and password

        Parameters
        ----------
        base_url : str
            Base url. e.g. `http://localhost:3000/api/v3`
        username : str
            username to login with
        password : str
            password to login with
        timeout_seconds : [int], optional
            timeout in seconds to wait for http connections to return, by default None
        """
        self._base_url = base_url
        self._timeout_seconds = (
            timeout_seconds  # we are hitting a transmission timeout...
        )
        self._username = username  # default username
        self._password = password  # default password
        self._token = token  # store token here
        self._headers = {}  # store headers
        self._auth_method = auth_method
        self._verify = verify

        if not self._token:
            if not self._username or not self._password:
                raise ValueError("SciCat login credentials (username, password) must be provided if token is not provided")
            if auto_login:
                self.login()
        else:
            self._headers["Authorization"] = f"Bearer {self._token}"

    def _make_limits(
            self,
            skip: Optional[int] = None,
            limit: Optional[int] = None,
            order_by: Optional[str] = None,
        ) -> str:
        """
        Given the optional components, return a ~~string~~ [dict]
        representation of the standard limit filter JSON for a query.
        """
        limits = {}
        if skip is not None:
            limits["skip"] = skip
        if limit is not None:
            limits["limit"] = limit
            limits["order"] = "createdAt:desc"
        if order_by is not None:
            limits["order"] = order_by
        # return json.dumps(limits)
        return limits

    def datasets_get_many(
            self,
            filter_fields: Optional[dict] = None,
            include_fields: Optional[list] = None,
            skip: Optional[int] = None,
            limit: Optional[int] = None,
            order_by: Optional[str] = None,
        ) -> Optional[list[dict]]:
        """
        Gets datasets using the simple filter mechanism.
        You should favor this call when your search is not complex.
        (For resource-intensive queries use datasets_find instead.)
        This function has been renamed and the old name has been mantained for backward compatibility
        The previous names are find_datasets and get_datasets

        For example, a search for Datasets of a given proposalId would have
        ```python
        filter_fields = {"proposalId": "1234"}
        ```
        A search for Datasets  with no proposalId would be:
        ```python
        filter_fields = {"proposalId": ""}
        ```
        If you want to search on partial strings, you can use "like":
        ```python
        filter_fields = {"proposalId": {"like":"123"}}
        ```

        Parameters
        ----------
        filter_fields : dict
            Dictionary of filtering fields. Must be json serializable.

        skip : int
            number of items to skip

        limit : int
            number of items to return
            if this is set, and "order_by" is not, "order_by" gets the default "createdAt:desc"

        order_by : str
            The field to use when sorting results, and the sort direction.
            Composed of a string "field:direction" , where "direction" is "asc" or "desc".
        """
        filter = {}

        filter["limits"] = self._make_limits(skip, limit, order_by)

        if filter_fields is not None:
            filter["where"] = filter_fields
        if include_fields is not None:
            # When we switch to the v4 API, there will be no need to wrap these
            # in "relation" objects like this.
            filter["include"] = [{"relation": r} for r in include_fields]
        # filter_str = json.dumps(filter)

        # endpoint = f"Datasets?filter={filter_str}"
        # return cast(
        #     Optional[list[dict]],
        #     self._call_endpoint(
        #         cmd="get", endpoint=endpoint, operation="datasets_get_many"
        #     ),
        # )
        url = f'{self._base_url.strip("/")}/datasets'
        res = requests.request(
            method='GET',
            url=url,
            params=filter,
            headers=self._headers,
            timeout=self._timeout_seconds,
            stream=False,
            verify=self._verify,
        )
        return res.json()

    # Alias for backwards compatibility.
    get_datasets = datasets_get_many

    def login(self):
        """
        Attempts to authenticate using the stored username and password.
        Does not check if authentication has already occured.
        """
        self._token = self.get_token(
            self._base_url,
            self._username,
            self._password,
            headers=self._headers
        )
        self._headers["Authorization"] = f"Bearer {self._token}"

    def get_token(self, base_url, username, password, headers={}):
        """
        logs in using the provided username / password combination
        and receives token for further communication use
        """
        # Users/login only works for functional accounts and auth/msad for regular users.
        # Try both and see what works. This is not nice but seems to be the only
        # feasible solution right now.

        logger.info("Getting new token")

        response = self._log_in_via_users_login(base_url, username, password, headers)
        if response.ok:
            return response.json()["id"]  # not sure if semantically correct

        try:
            response_text = response.json()
        except json.decoder.JSONDecodeError:
            response_text = response.text
        logger.error(f"Failed log in:  {response_text}")
        raise ScicatLoginError(response.content)

    def _log_in_via_users_login(self, base_url, username, password, headers={}):
        # EG: 'https://scicat-ciren.cn.isaac.utk.edu/api/v3/auth/ldap'
        if self._auth_method.casefold() == "ldap":
            login_url = f'{base_url.strip("/")}/auth/ldap'
        else:
            login_url = f'{base_url.strip("/")}/auth/login'

        logger.debug(f'login_url="{login_url}"')
        response = requests.post(
            login_url,
            json={"username": username, "password": password},
            headers=headers,
            stream=False,
            verify=self._verify,
        )
        if not response.ok:
            try:
                response_text = response.json()
            except json.decoder.JSONDecodeError:
                response_text = response.text
            logger.info(f" Failed to log in via endpoint Users/login: {response_text}")
        return response

    # def add_dataset(self, *args, **kwargs):
    #     # Create an Ownable that will get reused for several other Model objects
    #     # ownable = Ownable(ownerGroup="magrathea", accessGroups=["deep_thought"])
    #     ownable = Ownable(
    #         ownerGroup=kwargs.get('ownerGroup'),
    #         accessGroups=kwargs.get('accessGroups')
    #     )
    #
    #     # Create a RawDataset object with settings for your choosing. Notice how
    #     # we pass the `ownable` instance.
    #     dataset = RawDataset(
    #         size=42,
    #         owner="slartibartfast",
    #         contactEmail="slartibartfast@magrathea.org",
    #         creationLocation="magrathea",
    #         creationTime=str(datetime.now().isoformat()),
    #         type=DatasetType.raw,
    #         instrumentId="earth",
    #         proposalId="deepthought",
    #         dataFormat="planet",
    #         datasetName="Douglas' Dataset",
    #         principalInvestigator="A. Mouse",
    #         sourceFolder="/foo/bar",
    #         scientificMetadata={"a": "field"},
    #         sampleId="gargleblaster",
    #         **ownable.model_dump(),
    #     )
    #     dataset_id = scicat.datasets_create(dataset)
    #
    #     # Create Datablock with DataFiles
    #     data_file = DataFile(path="file.h5", size=42)
    #     data_block = CreateDatasetOrigDatablockDto(
    #         size=42,
    #         dataFileList=[data_file],
    #         **ownable.model_dump(),
    #     )
    #     scicat.datasets_origdatablock_create(dataset_id, data_block)
    #
    #     # Create Attachment
    #     thumb_path = Path(__file__).parent.parent / "test/data/SciCatLogo.png"
    #     attachment = Attachment(
    #         datasetId=dataset_id,
    #         thumbnail=encode_thumbnail(thumb_path),
    #         caption="scattering image",
    #         **ownable.model_dump(),
    #     )
    #     scicat.upload_attachment(attachment)

def get_client(token=None, username=None, password=None, base_url=''):
    return CAMMClient(base_url=base_url, token=token, username=username, password=password)


