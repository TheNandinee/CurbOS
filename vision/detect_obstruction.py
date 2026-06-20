"""
detect_obstruction.py — REAL computer vision. This is the credibility anchor.

It takes a video of a road (a phone clip of a real Bengaluru choke point works
best) and measures OBSTRUCTION-MINUTES: it finds vehicles, tracks them, and flags
any that stay stationary on the carriageway longer than a threshold as an
obstruction, accumulating how long each blocks the lane. Output:
  - <video>_events.json  : obstruction events (start, dwell, bbox, size-class)
  - <video>_annotated.mp4: the clip with a live dwell timer on each blocked vehicle
  - prints total obstruction-minutes

MVP method: MOG2 background subtraction + centroid tracking + a stationarity test.
This is classical CV — it always runs, no model download, no GPU. Production swaps
the detector for YOLOv8 + ByteTrack to add precise vehicle-class attribution
(delivery LCV vs car vs auto); the event shape and obstruction-minute metric are
identical, which is the whole point.

Usage:
  python vision/detect_obstruction.py --video clip.mp4 --segment seg_mall_1
  python vision/detect_obstruction.py --video clip.mp4 --no-annotate   # JSON only
"""
import argparse, json, os
import cv2
import numpy as np

MIN_AREA = 1200            # ignore tiny blobs (px^2)
STATIONARY_PX = 14         # max centroid movement to count as "stopped"
MIN_OBSTRUCTION_S = 3.0    # must block at least this long to count
MATCH_DIST = 60            # px, to match a detection to an existing track


def size_class(area):
    if area < 4000:   return "two_wheeler"   # likely a delivery two-wheeler
    if area < 12000:  return "car_auto"
    return "lcv"                              # larger commercial vehicle


def run(video, segment_id, annotate=True):
    cap = cv2.VideoCapture(video)
    if not cap.isOpened():
        raise SystemExit(f"Could not open video: {video}")
    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    W = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)); Hh = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    bg = cv2.createBackgroundSubtractorMOG2(history=300, varThreshold=40, detectShadows=False)

    writer = None
    if annotate:
        out_path = os.path.splitext(video)[0] + "_annotated.mp4"
        writer = cv2.VideoWriter(out_path, cv2.VideoWriter_fourcc(*"mp4v"), fps, (W, Hh))

    tracks = {}          # id -> {cx,cy,first_frame,last_frame,still_frames,area,start_pos}
    next_id = 0
    events = []
    frame_idx = 0

    while True:
        ok, frame = cap.read()
        if not ok:
            break
        fg = bg.apply(frame, learningRate=0.0008)  # slow: keep stopped vehicles in FG
        fg = cv2.medianBlur(fg, 5)
        _, fg = cv2.threshold(fg, 200, 255, cv2.THRESH_BINARY)
        fg = cv2.morphologyEx(fg, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
        fg = cv2.dilate(fg, np.ones((7, 7), np.uint8), iterations=2)
        cnts, _ = cv2.findContours(fg, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        dets = []
        for c in cnts:
            area = cv2.contourArea(c)
            if area < MIN_AREA:
                continue
            x, y, w, h = cv2.boundingRect(c)
            dets.append((x + w / 2, y + h / 2, area, (x, y, w, h)))

        # greedy match dets -> tracks
        used = set()
        for tid, t in list(tracks.items()):
            best, bd = None, MATCH_DIST
            for i, (cx, cy, area, box) in enumerate(dets):
                if i in used:
                    continue
                d = ((cx - t["cx"]) ** 2 + (cy - t["cy"]) ** 2) ** 0.5
                if d < bd:
                    best, bd = i, d
            if best is not None:
                cx, cy, area, box = dets[best]; used.add(best)
                disp = ((cx - t["anchor"][0]) ** 2 + (cy - t["anchor"][1]) ** 2) ** 0.5
                if disp < STATIONARY_PX:
                    t["still_frames"] += 1; t["move_frames"] = 0
                elif disp > 2 * STATIONARY_PX:
                    # only reset after sustained movement, so a transient merge/jump
                    # from passing traffic doesn't wipe an accumulated dwell
                    t["move_frames"] += 1
                    if t["move_frames"] >= max(2, int(fps * 0.4)):
                        t["still_frames"] = 0; t["anchor"] = (cx, cy); t["move_frames"] = 0
                else:
                    t["move_frames"] = 0  # jitter band: neither count nor reset
                t.update(cx=cx, cy=cy, last_frame=frame_idx, area=area, box=box, missing=0)
            else:
                t["missing"] = t.get("missing", 0) + 1

        # new tracks for unmatched detections
        for i, (cx, cy, area, box) in enumerate(dets):
            if i in used:
                continue
            tracks[next_id] = {"cx": cx, "cy": cy, "first_frame": frame_idx,
                               "last_frame": frame_idx, "still_frames": 0, "move_frames": 0,
                               "area": area, "box": box, "anchor": (cx, cy), "missing": 0}
            next_id += 1

        # close stale tracks -> emit obstruction events
        for tid in [k for k, t in tracks.items() if t.get("missing", 0) > fps]:
            t = tracks.pop(tid)
            dwell = t["still_frames"] / fps
            if dwell >= MIN_OBSTRUCTION_S:
                events.append({"segment_id": segment_id, "track_id": tid,
                               "start_s": round(t["first_frame"] / fps, 1),
                               "dwell_s": round(dwell, 1),
                               "vehicle_class": size_class(t["area"]),
                               "bbox": [int(v) for v in t["box"]], "source": "cctv"})

        if writer is not None:
            for tid, t in tracks.items():
                x, y, w, h = t["box"]
                blocking = t["still_frames"] / fps >= MIN_OBSTRUCTION_S
                col = (60, 80, 255) if blocking else (160, 200, 80)  # BGR: red / teal
                cv2.rectangle(frame, (x, y), (x + w, y + h), col, 2)
                if blocking:
                    cv2.putText(frame, f"BLOCKING {t['still_frames']/fps:0.1f}s",
                                (x, max(15, y - 6)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, col, 2)
            cv2.putText(frame, "ClearLane | obstruction detection",
                        (10, Hh - 12), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (230, 230, 230), 2)
            writer.write(frame)
        frame_idx += 1

    # flush remaining tracks
    for tid, t in tracks.items():
        dwell = t["still_frames"] / fps
        if dwell >= MIN_OBSTRUCTION_S:
            events.append({"segment_id": segment_id, "track_id": tid,
                           "start_s": round(t["first_frame"] / fps, 1),
                           "dwell_s": round(dwell, 1),
                           "vehicle_class": size_class(t["area"]),
                           "bbox": [int(v) for v in t["box"]], "source": "cctv"})
    cap.release()
    if writer is not None:
        writer.release()

    total_min = round(sum(e["dwell_s"] for e in events) / 60.0, 2)
    out_json = os.path.splitext(video)[0] + "_events.json"
    json.dump({"video": video, "segment_id": segment_id, "fps": fps,
               "obstruction_minutes": total_min, "events": events},
              open(out_json, "w"), indent=2)
    print(f"OK: {len(events)} obstruction events | {total_min} obstruction-minutes")
    print(f"     events -> {out_json}")
    if annotate:
        print(f"     annotated video -> {os.path.splitext(video)[0]}_annotated.mp4")
    return total_min, events


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--video", required=True)
    ap.add_argument("--segment", default="seg_mall_1")
    ap.add_argument("--no-annotate", action="store_true")
    a = ap.parse_args()
    run(a.video, a.segment, annotate=not a.no_annotate)
