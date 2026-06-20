"""
make_sample_clip.py — generate a tiny synthetic "CCTV" clip so the detector runs
out of the box. THIS IS A SMOKE-TEST ASSET, NOT THE DEMO. For the real demo, run
detect_obstruction.py on a phone clip of an actual Bengaluru choke point — a real
bounding box with a ticking dwell timer is worth more than any synthetic clip.

Through-traffic flows in the upper lane; two vehicles stop in the lower kerb band
(a delivery LCV and a car) for several seconds = obstruction.
"""
import cv2
import numpy as np

W, H, FPS, SECONDS = 640, 360, 20, 14
OUT = "vision/sample_clip.mp4"


def main():
    vw = cv2.VideoWriter(OUT, cv2.VideoWriter_fourcc(*"mp4v"), FPS, (W, H))
    n = FPS * SECONDS
    through = [(-60, 150, 4.2, 46, 24), (-260, 150, 4.2, 52, 26),
               (-460, 150, 3.8, 44, 24), (-150, 150, 5.0, 48, 24)]
    # stopped vehicles in kerb band y=225: (x, y, w, h, start_f, end_f)
    stopped = [(400, 225, 74, 36, 30, 230),   # large -> 'lcv'
               (150, 230, 58, 30, 55, 250)]   # car
    for f in range(n):
        frame = np.full((H, W, 3), 30, np.uint8)
        cv2.rectangle(frame, (0, 128), (W, 250), (46, 46, 50), -1)   # carriageway
        cv2.line(frame, (0, 190), (W, 190), (92, 92, 98), 1)         # lane divider
        for (sx, y, sp, w, h) in through:                            # moving traffic
            x = int((sx + sp * f) % (W + 160)) - 80
            cv2.rectangle(frame, (x, y - h // 2), (x + w, y + h // 2), (200, 175, 115), -1)
        for (x, y, w, h, sf, ef) in stopped:                        # parked obstructions
            if sf <= f <= ef:
                cv2.rectangle(frame, (x, y - h // 2), (x + w, y + h // 2), (120, 160, 235), -1)
                cv2.rectangle(frame, (x, y - h // 2), (x + w, y + h // 2), (160, 200, 250), 1)
        vw.write(frame)
    vw.release()
    print(f"OK: wrote {OUT} ({SECONDS}s @ {FPS}fps)")


if __name__ == "__main__":
    main()
