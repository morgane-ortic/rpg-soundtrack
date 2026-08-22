from time import sleep
import os
import threading
from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout
from pathlib import Path
from tkinter import Tk, filedialog
import vlc
from utils import format_duration

APP_DIR = Path(__file__).resolve().parent

class AudioPlayer(BoxLayout):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.default = (0.25, 0.25, 0.25, 1)
        self.highlight = (0.5, 0.5, 0.5, 1)
        
        #Empty list to fill and display track list on Kivy GUI
        self.playlist = []

        self.player = vlc.MediaPlayer()  # Regular media player

        self.current_index = 0      # currently highlighted track
        self.playing_index = None   # currently playing track

        em = self.player.event_manager()
        em.event_attach(vlc.EventType.MediaPlayerEndReached, self._on_track_end)

        self.paused = False
        self.last_file_path = ''

        # Set up keyboard listener
        Window.bind(on_key_down=self.on_key_down)

    def get_media(self):
        root = Tk()
        root.withdraw()              # Hide the Tk root window
        root.attributes('-topmost', True)

        file_paths = filedialog.askopenfilenames(
            title='Select media files',
            initialdir = self.last_file_path,
            filetypes=[
                ('Media files', '*.mp3 *.wav *.flac *.ogg *.m4a *.aac *.mp4 *.mkv *.avi *webm'),
                ('All files', '*.*')
            ]
        )

        root.destroy()
        if file_paths:
            for file_path in file_paths:
                filename = os.path.basename(file_path)
                self.add_media(file_path, os.path.basename(file_path))
            self.last_file_path = os.path.dirname(file_paths[-1])
            # Update tracklist to see every new media
            self.show_tracklist()


    def add_media(self, file_path, filename):
        '''Adds a media file to the list'''
        # Create vlc Media from file
        media = vlc.Media(file_path)
        # Define metadata for this media
        media.parse()
        # Get the duration in SECONDS as INT
        duration = media.get_duration()
        track = {
            'file_path': file_path,
            'filename': filename,
            'duration': duration,
            'repeat': False
        }
        # Add track info to playlist
        self.playlist.append(track)
        self.update_track_highlight()


    def remove_media(self, instance):
        if not self.playlist:
            return

        removed_index = self.current_index  # we keep track of the current index BEFORE the track deletion that will change it

        self.playlist.pop(self.current_index)

        # Fix current selection
        if self.current_index >= len(self.playlist):
            self.current_index = max(0, len(self.playlist) - 1)

        if removed_index == self.playing_index:
            self.stop_audio(None)
        self.show_tracklist()
        self.update_track_highlight()


    def move_track_up(self, instance):
        if self.current_index <= 0:
            return

        i = self.current_index

        # Swap tracks
        self.playlist[i], self.playlist[i - 1] = (
            self.playlist[i - 1],
            self.playlist[i]
        )

        self.current_index -= 1

        self.show_tracklist()
        self.update_track_highlight()


    def move_track_down(self, instance):
        if self.current_index >= len(self.playlist) - 1:
            return

        i = self.current_index

        # Swap tracks
        self.playlist[i], self.playlist[i + 1] = (
            self.playlist[i + 1],
            self.playlist[i]
        )

        self.current_index += 1

        self.show_tracklist()
        self.update_track_highlight()


    def play_audio(self, instance=None, index=None):
        count = len(self.playlist)
        
        if count == 0:
            return

        if index is not None:
            self.current_index = index

        self.current_index = max(0, min(self.current_index, count - 1))
        self.update_track_highlight()
        # Check if track is paused
        if getattr(self, 'paused', False) and index is None:
            # If yes keep playing at same point
            self.player.play()
        else:
            # if not (for instance stopped) play at index from track start
            track = self.playlist[self.current_index]
            media = vlc.Media(track['file_path'])
            self.player.set_media(media)
            self.player.play()
        self.playing_index = self.current_index # define which track is playing (the one selected right now)
        self.paused = False
        Clock.schedule_interval(self.check_playback, 1)  # Check every second
    
    def check_playback(self, dt):
        if self.player.get_state() != vlc.State.Playing:
            Clock.unschedule(self.check_playback)  # Stop checking when playback finishes

    def stop_audio(self, instance):
        self.paused = False  # Reset pause tracking
        self.player.stop()
        self.playing_index = None
        Clock.unschedule(self.check_playback)  # Ensure the scheduled check stops

    def pause_audio(self, instance):
        self.paused = True  # Track paused state
        self.player.pause()

    def next_track(self, instance):
        '''Skip to the next track'''
        count = len(self.playlist)
        if count == 0:
            return
        # If last track in playlist, don't go to next
        if self.current_index >= count - 1:
            return

        self.current_index += 1
        self.play_audio()

    def previous_track(self, instance):
        '''Go back to the previous track'''
        count = len(self.playlist)
        if count == 0:
            return
        # If first track in playlist, don't go to previous                
        if self.current_index <= 0:
            return

        self.current_index -= 1
        self.play_audio()

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

        count = len(self.playlist)
        if count == 0:
            return

        # Check if current track is set on repeat
        if self.playlist[self.current_index]['repeat']:
            # prevent duplicate timers and race conditions
            Clock.unschedule(self.check_playback)
            try:
                self.player.stop()
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
        # Assigning track names from tracklist to recycleview
        rv.data = [
            {
                'text': item['filename'],
                'duration': format_duration(item['duration']),
                'bg_color': self.highlight if i == self.current_index else self.default,
                'index': i,
                'checked': item['repeat']
            } for i, item in enumerate(self.playlist) ]

    def update_track_highlight(self):
        rv = self.ids.tracklist
        for i, item in enumerate(rv.data):
            item['bg_color'] = self.highlight if i == self.current_index else self.default
            item['checked'] = self.playlist[i]['repeat']
        rv.refresh_from_data()

    def on_row_checkbox(self, index, active):
        self.playlist[index]['repeat'] = active

    def row_pressed(self, index, touch):
        '''Behaviour when media row is (double-)clicked on playlist'''
        self.current_index = index
        self.update_track_highlight()

        if touch.is_double_tap:
            self.play_audio(None, index=index)


    ### KEYBOARD COMMANDS ###

    def on_key_down(self, window, key, *args):

        if key == 32:
            if self.paused:
                self.player.play()
                self.paused = False
            else:
                self.player.pause()
                self.paused = True
            return True

        elif key == 115:
            self.stop_audio(None)

        elif key == 127:
            self.remove_media(None)

        elif key == 273:
            self.move_track_up(None)
            return True

        elif key == 274:
            self.move_track_down(None)
            return True

        elif key == 275:
            self.next_track(None)
            return True

        elif key == 276:
            self.previous_track(None)
            return True

        return False

class RPGSoundtrackApp(App):
    def build(self):
        self.title = 'RPG Soundtrack'
        Builder.load_file(str(APP_DIR / 'audio_player.kv'))
        return AudioPlayer()

def main():
    RPGSoundtrackApp().run()
    
if __name__ == '__main__':
    main()