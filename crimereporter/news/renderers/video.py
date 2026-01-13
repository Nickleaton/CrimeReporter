import logging
from pathlib import Path

import numpy as np
from moviepy import VideoClip
from moviepy.audio.AudioClip import AudioArrayClip, concatenate_audioclips
from moviepy.audio.io.AudioFileClip import AudioFileClip
from moviepy.video.compositing.CompositeVideoClip import concatenate_videoclips

import crimereporter.news.segments  # noqa: F401
from crimereporter.news.renderers.renderer import Renderer
from crimereporter.news.script import Script
from crimereporter.news.segments.audio import AudioSegment
from crimereporter.news.segments.segment import SegmentMeta
from crimereporter.news.segments.video import VideoSegment
from crimereporter.utils.config import FormatsConfig

logger = logging.getLogger(__name__)


class VideoRenderer(Renderer):
    logger = logging.getLogger(__name__)

    @staticmethod
    def create_audio_clip(idx: int, segment: dict, fmt, output_path: Path, default_text) -> AudioFileClip:
        """
        Return an audio clip for a segment, validating file existence.

        Args:
            idx: Segment index (used for TTS filenames)
            segment: Dictionary containing segment data
            fmt: FormatsConfig object for sizing, banner, and logo.
            output_path: Path where TTS files are stored
            default_text: banner text
        Returns:
            AudioFileClip: MoviePy audio clip

        Raises:
            FileNotFoundError: if the expected audio file does not exist
            ValueError: if segment has neither 'audio' nor 'text'

        """
        for key in segment:
            cls = SegmentMeta.registry.get(key)
            if cls and issubclass(cls, AudioSegment):
                instance = cls(idx, segment, fmt, output_path, default_text)
                return instance.load()

        raise ValueError(f"Segment {idx} has no registered audio provider")

    @staticmethod
    def create_visual_clip(idx: int, segment: dict, fmt, output_path: Path, default_text: str) -> VideoClip:
        """
        Create a visual clip from a segment (image, video, or slide in the future).

        Args:
            idx: index of segment
            segment: Segment dictionary
            fmt: FormatsConfig
            output_path: Path to directory containing video file.
            default_text: Banner text if segment text missing

        Returns:
            MoviePy VideoClip without audio
        """
        for key in segment:
            cls = SegmentMeta.registry.get(key)
            if cls and issubclass(cls, VideoSegment):
                instance = cls(idx, segment, fmt, output_path, default_text)
                return instance.load()
        raise ValueError(f"Segment {idx} has no registered video provider")

    @staticmethod
    def create_segment(idx: int, segment: dict, fmt, output_path: Path, default_text: str):
        """
        Create a single segment clip (video or image) with attached audio.
        """
        audio_clip = VideoRenderer.create_audio_clip(idx, segment, fmt, output_path, default_text)
        clip = VideoRenderer.create_visual_clip(idx, segment, fmt, output_path, default_text)

        # Adjust duration to match audio (padding if needed)
        if clip.duration < audio_clip.duration:
            pad_duration = audio_clip.duration - clip.duration
            logger.info(f"Segment {idx}: padding video with {pad_duration:.2f}s to match audio duration")
            # Extend visual clip with last frame
            last_frame = clip.to_ImageClip().with_duration(pad_duration)
            clip = concatenate_videoclips([clip, last_frame])
        elif clip.duration > audio_clip.duration:
            pad_duration = clip.duration - audio_clip.duration
            logger.info(f"Segment {idx}: padding audio with {pad_duration:.2f}s to match video duration")
            # Extend audio with silence
            silence_array = np.zeros((int(audio_clip.fps * pad_duration), audio_clip.nchannels))
            silence = AudioArrayClip(silence_array, fps=audio_clip.fps)
            audio_clip = concatenate_audioclips([audio_clip, silence])

        # Attach audio
        clip = clip.with_audio(audio_clip)
        return clip

    def render(self, script: Script, orientation: str, output_path: Path):
        """
        Render the script into a video using image/video + text/audio segments.
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)
        fmt = FormatsConfig(orientation, script.parsed["Type"])
        segments = list(script.segments)
        segment_clips = []

        for idx, seg in enumerate(segments, start=1):
            VideoRenderer.logger.info(f"Processing segment {idx}/{len(segments)}")

            try:
                clip = VideoRenderer.create_segment(
                    idx=idx,
                    segment=seg,
                    fmt=fmt,
                    output_path=output_path,
                    default_text=script.parsed["Title"],
                )
                segment_clips.append(clip)
            except FileNotFoundError as e:
                VideoRenderer.logger.warning(f"Skipping segment {idx} due to missing file: {e}")
            except ValueError as e:
                VideoRenderer.logger.warning(f"Skipping segment {idx} due to error: {e}")

        if not segment_clips:
            VideoRenderer.logger.error("No valid segments to render.")
            return

        VideoRenderer.logger.info("Composing final video from segments...")
        final_video = concatenate_videoclips(segment_clips)
        final_video.write_videofile(str(output_path), fps=24, logger=None)

        # Clean up
        for clip in segment_clips:
            clip.close()
        final_video.close()

        VideoRenderer.logger.info(f"Video rendering completed: {output_path}")
