from pyscicat.client import ScicatClient, encode_thumbnail

from pyscicat.model import (
    Attachment,
    CreateDatasetOrigDatablockDto,
    DataFile,
    DatasetType,
    Ownable,
    RawDataset,
)

# ========================================================================
# Client
# ========================================================================
# I'm not sure if the "client" should be a subclass of ScicatClient or just a fxn.
class CAMMClient(ScicatClient):
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

    pass

def get_client(username=None, password=None, base_url=''):
    return CAMMClient(base_url=base_url, username=username, password=password)


