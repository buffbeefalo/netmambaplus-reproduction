"""Verify the immutable published v4 edition and its unchanged release bytes.

This historical check does not claim that the video explains newer repository
files. Run verify_repository_guide.py for current individual-file entries, or
--current to require the course coverage itself to describe today's full tree.
"""

from verify_video_course_v3 import main


if __name__ == "__main__":
    raise SystemExit(main(version=4))
