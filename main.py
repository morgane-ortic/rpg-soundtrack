from time import sleep
from kivy.app import App
from kivy.clock import Clock
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
import vlc

class AudioPlayer(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        
        self.player = vlc.MediaPlayer()
        media = vlc.Media('test.mp3')
        self.player.set_media(media)

        self.play_button = Button(text="Play", size_hint=(1, 0.3))
        self.play_button.bind(on_press=self.play_audio)
        
        self.stop_button = Button(text="Stop", size_hint=(1, 0.3))
        self.stop_button.bind(on_press=self.stop_audio)

        self.add_widget(self.play_button)
        self.add_widget(self.stop_button)

    def play_audio(self, instance):
        self.player.play()
        Clock.schedule_interval(self.check_playback, 1)  # Check every second
    
    def check_playback(self, dt):
        if self.player.get_state() != vlc.State.Playing:
            Clock.unschedule(self.check_playback)  # Stop checking when playback finishes

    def stop_audio(self, instance):
        self.player.stop()
        Clock.unschedule(self.check_playback)  # Ensure the scheduled check stops

    def stop_audio(self, instance):
        self.player.stop()


class MyApp(App):
    def build(self):
        return AudioPlayer()
    
if __name__ == "__main__":
    MyApp().run()