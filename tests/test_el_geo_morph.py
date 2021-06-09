import pytest
from elmada import el_geo_morph as gm
from elmada import paths


def test_download_database(mocker):
    mock = mocker.patch("elmada.helper.get_api_key", return_value="123")
    mock = mocker.patch("requests.get")
    type(mock.return_value).content = mocker.PropertyMock(return_value="xx".encode())
    fp = paths.CACHE_DIR / "test_file.csv"
    gm.download_database(fp=fp)
    assert fp.exists()
    fp.unlink()
    mock.assert_called_once()
