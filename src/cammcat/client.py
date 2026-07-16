from pyscicat.client import ScicatClient

# ========================================================================
# Client
# ========================================================================
# I'm not sure if the "client" should be a subclass of ScicatClient or just a fxn.
class CAMMClient:
    pass


def get_client(username=None, password=None, base_url=''):
    return ScicatClient(base_url=base_url, username=username, password=password)


