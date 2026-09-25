#!/usr/bin/env python3
"""
Testmottagare för UDP-broadcast från pose_logger.
Kan köras på godtycklig dator i samma lokala nätverk (eller lokalt).
"""

import argparse
import json
import socket
import sys


def main():
    parser = argparse.ArgumentParser(description="Lyssna på UDP pose broadcast-data.")
    parser.add_argument(
        "--port",
        "-p",
        type=int,
        default=5005,
        help="UDP-port att lyssna på (standard: 5005).",
    )
    parser.add_argument(
        "--compact",
        action="store_true",
        default=False,
        help="Kompakt utskrift (en rad sammanfattning per bildruta).",
    )
    args = parser.parse_args()

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # SO_REUSEPORT / SO_REUSEADDR gör att flera oberoende klienter kan lyssna samtidigt
    if hasattr(socket, "SO_REUSEPORT"):
        try:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        except OSError:
            pass
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    # Bind till alla interface på angiven port
    sock.bind(("", args.port))

    print(f"==================================================")
    print(f" Lyssnar på UDP pose-broadcast på port {args.port}...")
    print(f" Tryck Ctrl+C för att avsluta.")
    print(f"==================================================")

    try:
        while True:
            data, (sender_ip, sender_port) = sock.recvfrom(65535)
            try:
                pose_frame = json.loads(data.decode("utf-8"))
            except json.JSONDecodeError:
                print(f"Mottog ogiltig JSON från {sender_ip}:{sender_port}")
                continue

            frame_id = pose_frame.get("frame_count", 0)
            persons = pose_frame.get("persons", [])

            if args.compact:
                print(
                    f"[{sender_ip}] Frame {frame_id:06d}: {len(persons)} person(er)"
                )
            else:
                print(f"\n--- [{sender_ip}] Frame {frame_id} | {len(persons)} person(er) ---")
                for p in persons:
                    track_str = f"ID: {p['track_id']}, " if p.get("track_id") is not None else ""
                    b = p["bbox"]["pixels"]
                    print(
                        f"  Person [{track_str}Konfidens: {p['confidence']:.2f}, Box: ({b['xmin']},{b['ymin']})-({b['xmax']},{b['ymax']})]"
                    )
                    kp = p.get("keypoints", {})
                    # Visa t.ex. näsa och axlar som snabb referens
                    for joint in ["nose", "left_shoulder", "right_shoulder"]:
                        if joint in kp:
                            j = kp[joint]
                            print(
                                f"    {joint:<16}: ({j['pixel_x']:>4}px, {j['pixel_y']:>4}px) [conf: {j['confidence']:.2f}]"
                            )
    except KeyboardInterrupt:
        print("\nAvslutar mottagaren...")
    finally:
        sock.close()


if __name__ == "__main__":
    main()
