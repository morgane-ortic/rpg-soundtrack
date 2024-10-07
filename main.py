from kivy.core.audio import SoundLoader

class SoundtrackPlayer:
    def __init__(self):
        self.track = None

    def load_track(self, file_path):
        self.track = SoundLoader.load(file_path)
        if self.track
            print(f'Track {file_path} loaded successfully :)')
        else:
            print(f'Failed to load soundtrack {file_path} :(')

    def play(self):
        if self.track:
            self.track.play()

    def pause(self):
        if self.track:
            self.track.stop()

    def stop(self):
        if self.track:
            self.track.stop()
            # resets playing position to file start for next playing
            self.track.seek(0)