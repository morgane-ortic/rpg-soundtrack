from time import sleep
import os
import threading
from dotenv import load_dotenv
from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout
import vlc

class AudioPlayer(BoxLayout):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.load_env()

        self.repeat = {}
        self.default = (0.25, 0.25, 0.25, 1)
        self.highlight = (0.5, 0.5, 0.5, 1)
        
        self.list_player = vlc.MediaListPlayer()
        self.media_list = vlc.MediaList()
        #Empty list to fill and display track list on Kivy GUI
        self.text_tracklist = []
        self.list_player.set_media_list(self.media_list)

        self.player = vlc.MediaPlayer()  # Regular media player
        self.list_player.set_media_player(self.player)  # Link both players

        self.current_index = 0

        em = self.player.event_manager()
        em.event_attach(vlc.EventType.MediaPlayerEndReached, self._on_track_end)

        self.add_media(self.MEDIA_1)
        self.add_media(self.MEDIA_2)
        self.add_media(self.MEDIA_3)

        self.show_tracklist()

        self.paused = False

    def load_env(self):
        load_dotenv()
        self.MEDIA_1 = os.getenv('MEDIA_1')
        self.MEDIA_2 = os.getenv('MEDIA_2')
        self.MEDIA_3 = os.getenv('MEDIA_3')

    def add_media(self, file_path):
        '''Adds a media file to the list'''
        # Create vlc Media from file
        media = vlc.Media(file_path)
        # Add media to our vlc media list
        self.media_list.add_media(media)
        # Add track name filename to text list
        self.text_tracklist.append(file_path)
        self.update_track_highlight()
        print(f'Added media: {file_path} - {media}')

    def play_audio(self, instance=None, index=None):
        count = self.media_list.count()
        if count == 0:
            return

        # if caller requested a specific index, use it; otherwise keep current_index
        if index is not None:
            index = max(0, min(index, count - 1))
            self.current_index = index

        self.current_index = max(0, min(self.current_index, count - 1))
        self.update_track_highlight()
        # Check if track is paused
        if getattr(self, 'paused', False) and index is None:
            # If yes keep playing at same point
            self.list_player.play()
        else:
            # if not (for instance stopped) play at index from track start
            self.list_player.play_item_at_index(self.current_index)
        self.paused = False
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
        count = self.media_list.count()
        if count == 0:
            return
        self.list_player.next()
        self.current_index = (self.current_index + 1) % count
        self.update_track_highlight()
        if self.paused:
            Clock.schedule_once(self.ensure_pause)

    def previous_track(self, instance):
        '''Go back to the previous track'''
        count = self.media_list.count()
        if count == 0:
            return
        self.list_player.previous()
        self.current_index = (self.current_index - 1) % count
        self.update_track_highlight()
        if self.paused:
            Clock.schedule_once(self.ensure_pause)

    def ensure_pause(self, instance):
        '''Ensure the player is paused only after it's started playing'''
        if self.player.get_state() == vlc.State.Playing:
            self.pause_audio(None)

    def _on_track_end(self, event):
        """VLC event callback when a track finishes naturally."""

        # schedule to main thread if called from VLC thread
        if threading.current_thread() is not threading.main_thread():
            Clock.schedule_once(lambda dt: self._on_track_end(event))
            return

        count = self.media_list.count()
        if count == 0:
            return

        # Check if current track is set on repeat
        if self.repeat.get(self.current_index):
            # prevent duplicate timers and race conditions
            Clock.unschedule(self.check_playback)
            try:
                self.list_player.stop()
            except Exception:
                pass

            self.play_audio(index=self.current_index)
            return

        self.current_index = (self.current_index + 1) % count
        self.update_track_highlight()
        self.play_audio(index=self.current_index)

    def show_tracklist(self):
        # refering to RecycleView id in kv file
        rv = self.ids.tracklist
        # Assigning track names from text_tracklist to recycleview
        rv.data = [
            {
                'text': name,
                'bg_color': self.highlight if i == self.current_index else self.default,
                'index': i,
                'checked': getattr(self, 'repeat', {}).get(i, False)
            } for i, name in enumerate(self.text_tracklist) ]
        print(rv.data)

    def update_track_highlight(self):
        rv = self.ids.tracklist
        for i, item in enumerate(rv.data):
            item['bg_color'] = self.highlight if i == self.current_index else self.default
            item['checked'] = self.repeat.get(i, item.get('checked', False))
        rv.refresh_from_data()

    def on_row_checkbox(self, index, active):
        self.repeat[index] = bool(active)
        print(f'self.repeat: {self.repeat}\nself.repeat[index]: {self.repeat[index]}\n')




class SimultrackApp(App):
    def build(self):
        self.title = 'Simultrack'
        Builder.load_file('audio_player.kv')
        return AudioPlayer()
    
if __name__ == '__main__':
    SimultrackApp().run()