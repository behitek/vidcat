import cv2
import numpy as np

def remove_watermark(input_path, output_path, progress_callback=None):
    cap = cv2.VideoCapture(input_path)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
    
    frame_idx = 0
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
            
        mask = np.zeros((height, width), dtype=np.uint8)
        # 200x50 px at bottom right
        h_start = max(0, height - 50)
        w_start = max(0, width - 200)
        mask[h_start:height, w_start:width] = 255
        
        inpainted = cv2.inpaint(frame, mask, 3, cv2.INPAINT_TELEA)
        out.write(inpainted)
        
        frame_idx += 1
        if progress_callback:
            progress_callback(frame_idx, total_frames)
            
    cap.release()
    out.release()
