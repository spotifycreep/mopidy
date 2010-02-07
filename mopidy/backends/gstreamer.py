import logging

import gst

from mopidy.models import Track, Playlist
from mopidy.backends import (BaseBackend,
                             BasePlaybackController,
                             BaseCurrentPlaylistController)

logger = logging.getLogger(u'backends.gstreamer')

class GStreamerBackend(BaseBackend):
    def __init__(self, *args, **kwargs):
        super(GStreamerBackend, self).__init__(*args, **kwargs)

        self.playback = GStreamerPlaybackController(self)
        self.current_playlist = GStreamerCurrentPlaylistController(self)

class GStreamerCurrentPlaylistController(BaseCurrentPlaylistController):
    def add(self, uri, at_position=None):
        tracks = self.playlist.tracks

        if at_position is None:
            tracks.append(Track(uri))
        else:
            tracks.insert(at_position, Track(uri))

        self.playlist = Playlist(tracks=tracks)

class GStreamerPlaybackController(BasePlaybackController):
    STATE_MAPPING = {
        gst.STATE_PAUSED: BasePlaybackController.PAUSED,
        gst.STATE_PLAYING: BasePlaybackController.PLAYING,
        gst.STATE_NULL: BasePlaybackController.STOPPED,
    }

    def __init__(self, backend):
        super(GStreamerPlaybackController, self).__init__(backend)

        bin = gst.element_factory_make("playbin", "player")
        sink = gst.element_factory_make("fakesink", "fakesink")

        bin.set_property("video-sink", sink)

        self.bin = bin

    @property
    def state(self):
        gststate = type(gst.STATE_NULL)

        for state in self.bin.get_state():
            if type(state) == gststate and state in self.STATE_MAPPING:
                return self.STATE_MAPPING[state]

        return self.STOPPED

    def play(self, id=None, position=None):
        playlist = self.backend.current_playlist.playlist

        if not self.current_track and not playlist.tracks:
            return False
        elif playlist.tracks:
            self.current_track = playlist.tracks[self.playlist_position]

        self.bin.set_property("uri", self.current_track.uri)
        self.bin.set_state(gst.STATE_PLAYING)

        return True

    def stop(self):
        self.bin.set_state(gst.STATE_NULL)

    def next(self):
        playlist = self.backend.current_playlist.playlist

        self.playlist_position += 1
        self.current_track = playlist.tracks[self.playlist_position]

        self.play()
