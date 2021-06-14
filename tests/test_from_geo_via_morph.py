from elmada import from_geo_via_morph, paths


def test_download_database(mocker):
    mock = mocker.patch("elmada.helper.get_api_key", return_value="123")
    mock = mocker.patch("requests.get")
    type(mock.return_value).content = mocker.PropertyMock(return_value="xx".encode())
    fp = paths.CACHE_DIR / "test_file.csv"
    from_geo_via_morph.download_database(fp=fp)
    assert fp.exists()
    fp.unlink()
    mock.assert_called_once()
