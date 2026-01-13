from crimereporter.news.commands.commands import config, logger
from crimereporter.news.commands.simple import SimpleCommand
from crimereporter.news.renderers.gcp_text_to_speech import GCPTextToSpeechRenderer
from crimereporter.news.renderers.gtts_audio import GTTSAudioRenderer
from crimereporter.news.renderers.pyttsx3_audio import PYTTSX3AudioRenderer


class AudioCommand(SimpleCommand):

    def run(self) -> None:
        filename = self.input_file.parent / "output/audio.mp3"
        if not self.should_run(filename):
            logger.info("Audio already exists, skipping")
            return
        engine = config.audio.engine
        if engine == "GTTS":
            renderer = GTTSAudioRenderer()
        elif engine == "PYTTSX3":
            renderer = PYTTSX3AudioRenderer()
        elif engine == "GCPTextToSpeech":
            renderer = GCPTextToSpeechRenderer()
        else:
            raise ValueError(f"Unknown engine: {engine}")
        renderer.render(self.script, self.orientation, filename)
