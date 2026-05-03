import numpy as np
from core.inpainting import remove_watermark

def test_remove_watermark_mocked(mocker):
    mock_cap = mocker.MagicMock()
    mock_cap.isOpened.side_effect = [True, False]
    mock_cap.read.return_value = (True, np.zeros((720, 1280, 3), dtype=np.uint8))
    mock_cap.get.side_effect = lambda prop: {
        3: 1280, # CAP_PROP_FRAME_WIDTH
        4: 720,  # CAP_PROP_FRAME_HEIGHT
        5: 30.0, # CAP_PROP_FPS
        7: 1     # CAP_PROP_FRAME_COUNT
    }.get(prop, 0)
    
    mocker.patch('cv2.VideoCapture', return_value=mock_cap)
    mock_writer = mocker.MagicMock()
    mocker.patch('cv2.VideoWriter', return_value=mock_writer)
    mock_inpaint = mocker.patch('cv2.inpaint', return_value=np.zeros((720, 1280, 3), dtype=np.uint8))
    
    cb_called = []
    remove_watermark("in.mp4", "out.mp4", lambda c, t: cb_called.append((c, t)))
    
    assert mock_inpaint.called
    assert mock_writer.write.called
    assert cb_called == [(1, 1)]
