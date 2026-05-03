import sys
from unittest.mock import patch
from main import main

def test_main_runs(mocker):
    mock_exec = mocker.patch('PyQt6.QtWidgets.QApplication.exec', return_value=0)
    with patch.object(sys, 'argv', ['main.py']):
        sys.exit = mocker.MagicMock()
        main()
        assert mock_exec.called
