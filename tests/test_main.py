import sys
from unittest.mock import patch
from main import main

def test_main_runs(mocker):
    mock_app = mocker.patch('main.QApplication')
    mock_app.return_value.exec.return_value = 0
    with patch.object(sys, 'argv', ['main.py']):
        sys.exit = mocker.MagicMock()
        main()
        assert mock_app.return_value.exec.called
