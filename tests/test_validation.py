import pytest
import sys
from folder_archaeologist.cli import main
from unittest.mock import patch

def test_validation_top_n_error(capsys):
    with patch.object(sys, 'argv', ['folder_archaeologist', '.', '--top-n', '0']):
        with pytest.raises(SystemExit) as e:
            main()
        assert e.value.code == 1
        captured = capsys.readouterr()
        assert "Error: --top-n must be greater than 0." in captured.out

def test_validation_max_depth_error(capsys):
    with patch.object(sys, 'argv', ['folder_archaeologist', '.', '--max-depth', '-1']):
        with pytest.raises(SystemExit) as e:
            main()
        assert e.value.code == 1
        captured = capsys.readouterr()
        assert "Error: --max-depth must be 0 or greater." in captured.out

def test_validation_min_size_error(capsys):
    with patch.object(sys, 'argv', ['folder_archaeologist', '.', '--min-size', '-100']):
        with pytest.raises(SystemExit) as e:
            main()
        assert e.value.code == 1
        captured = capsys.readouterr()
        assert "Error: --min-size must be 0 or greater." in captured.out
