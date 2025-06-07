from time import sleep
from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout
import vlc
class AudioPlayer(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        self.list_player = vlc.MediaListPlayer()
        self.media_list = vlc.MediaList()
        self.list_player.set_media_list(self.media_list)

        self.player = vlc.MediaPlayer()  # Regular media player
        self.list_player.set_media_player(self.player)  # Link both players
        self.add_media('test.mp3')
        self.add_media('test2.m4a')
        self.add_media('test3.mp3')

        self.paused = False

    def add_media(self, file_path):
        '''Adds a media file to the list'''
        media = vlc.Media(file_path)
        self.media_list.add_media(media)
        print(f'Added media: {media}')

    def play_audio(self, instance):
        self.paused = False
        self.list_player.play()
        Clock.schedule_interval(self.check_playback, 1)  # Check every second
    
    def check_playback(self, dt):
        if self.player.get_state() != vlc.State.Playing:
            Clock.unschedule(self.check_playback)  # Stop checking when playback finishes

    def stop_audio(self, instance):
        self.paused = False  # Reset pause tracking
        self.list_player.stop()
        Clock.unschedule(self.check_playback)  # Ensure the scheduled check stops

    def pause_audio(self, instance):
        self.paused = True  # Track paused state
        self.list_player.pause()

    def next_track(self, instance):
        '''Skip to the next track'''
        self.list_player.next()
        if self.paused:
            Clock.schedule_once(self.ensure_pause)

    def previous_track(self, instance):
        '''Go back to the previous track'''
        self.list_player.previous()
        if self.paused:
            Clock.schedule_once(self.ensure_pause)

    def ensure_pause(self, instance):
        '''Ensure the player is paused only after it's started playing'''
        if self.player.get_state() == vlc.State.Playing:
            self.pause_audio(None)


class SimultrackApp(App):
    def build(self):
        self.title = 'Simultrack'
        Builder.load_file('audio_player.kv')
        return AudioPlayer()
    
if __name__ == '__main__':
    SimultrackApp().run()