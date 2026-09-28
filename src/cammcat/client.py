import logging
import requests

from pyscicat.client import ScicatClient, encode_thumbnail

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
        
        login
          -> calls self.get_token (instead of pyscicat.client.get_token)
        get_token
          -> moved pyscicat.client.get_token to self.get_token
          -> call self._log_in_via_users_login instead of pyscicat.client.*
        _log_in_via_users_login
          -> enable ldap login
    '''

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
        self._headers["Authorization"] = "Bearer {}".format(self._token)

    def get_token(self, base_url, username, password, headers={}):
        """
        logs in using the provided username / password combination
        and receives token for further communication use
        """
        # Users/login only works for functional accounts and auth/msad for regular users.
        # Try both and see what works. This is not nice but seems to be the only
        # feasible solution right now.

        logger.info(" Getting new token")

        response = self._log_in_via_users_login(base_url, username, password, headers)
        if response.ok:
            return response.json()["id"]  # not sure if semantically correct

        try:
            response_text = response.json()
        except json.decoder.JSONDecodeError:
            response_text = response.text
        logger.error(f" Failed log in:  {response_text}")
        raise ScicatLoginError(response.content)

    def _log_in_via_users_login(self, base_url, username, password, headers={}):
        # login_url = "/".join(s.strip("/") for s in [base_url, "auth/ldap"])
        # login_url = f'{base_url.strip("/")}/auth/msad'
        login_url = 'https://scicat-ciren.cn.isaac.utk.edu/api/v3/auth/ldap'
        print(f'login_url="{login_url}"')
        response = requests.post(
            login_url,
            json={"username": username, "password": password},
            headers=headers,
            stream=False,
            verify=True,
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


