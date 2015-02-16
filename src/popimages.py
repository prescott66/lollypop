#!/usr/bin/python
# Copyright (c) 2014-2015 Cedric Bellegarde <gnumdk@gmail.com>
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

from gettext import gettext as _, ngettext 
from gi.repository import Gtk, GLib, Gio, GdkPixbuf
import urllib.request
import urllib.parse
import os
from _thread import start_new_thread

from lollypop.define import *

class PopImages(Gtk.Popover):

    """
        Init Popover ui with a text entry and a scrolled treeview
    """
    def __init__(self, album_id):
        Gtk.Popover.__init__(self)
        
        self._album_id = album_id

        self._view = Gtk.FlowBox()
        self._view.set_selection_mode(Gtk.SelectionMode.NONE)
        self._view.connect("child-activated", self._on_activate)
        self._view.show()
        if Objects.settings.get_value('dark-view'):
            self._view.get_style_context().add_class('black')

        self.set_property('width-request', 700)
        self.set_property('height-request', 400)

        viewport = Gtk.Viewport()
        viewport.add(self._view)
        viewport.set_property("valign", Gtk.Align.START)
        self._scroll = Gtk.ScrolledWindow()
        self._scroll.set_hexpand(True)
        self._scroll.set_vexpand(True)
        self._scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self._scroll.add(viewport)

        grid = Gtk.Grid()
        grid.set_orientation(Gtk.Orientation.VERTICAL)
        self._scroll.show()
        self.connect("closed", self._stop_thread)
        label = Gtk.Label()
        label.set_text(_("Select a cover art for this album"))
        grid.add(label)
        grid.add(self._scroll)
        grid.show_all()
        self.add(grid)

    """
        Populate view
        @param searched words as string
    """
    def populate(self, string):
        self._thread = True
        start_new_thread(self._populate, (string,))

#######################
# PRIVATE             #
#######################        

    """
        Same as populate()
    """
    def _populate(self, string):
        self._urls = Objects.art.get_google_arts(string)
        self._add_pixbufs()
        
    """
        On hide, stop thread
    """
    def _stop_thread(self, widget):
        self._thread = False

    """
        Add urls to the view
    """
    def _add_pixbufs(self):
        if self._urls and len(self._urls) > 0:
            url = self._urls.pop()
            stream = None
            try:
                response = urllib.request.urlopen(url)
                stream = Gio.MemoryInputStream.new_from_data(response.read(), None)
            except:
                if self._thread:
                    self._add_pixbufs()
            if stream:
                GLib.idle_add(self._add_pixbuf, stream)
            if self._thread:                
                self._add_pixbufs()
                
    """
        Add stream to the view
    """
    def _add_pixbuf(self, stream):
        try:
            pixbuf = GdkPixbuf.Pixbuf.new_from_stream_at_scale(stream, ART_SIZE_MONSTER,
                                                                      ART_SIZE_MONSTER,
                                                                      False,
                                                                      None)
            image = Gtk.Image()
            image.set_from_pixbuf(pixbuf.scale_simple(ART_SIZE_BIG, ART_SIZE_BIG, 2))
            image.show()
            self._view.add(image)
        except Exception as e:
            print(e)
            pass
        
    """
        Use pixbuf as cover
        Reset cache and use player object to announce cover change
    """
    def _on_activate(self, flowbox, child):
        album_path = Objects.albums.get_path(self._album_id)
        path_count = Objects.albums.get_path_count(album_path)
        album_name = Objects.albums.get_name(self._album_id)
        artist_name = Objects.albums.get_artist_name(self._album_id)
        try:
            # Many albums with same path, suffix with artist_album name
            if path_count > 1:
                artpath = album_path+"/folder_"+artist_name+"_"+album_name+".jpg"
                if os.path.exists(album_path+"/folder.jpg"):
                    os.remove(album_path+"/folder.jpg")
            else:
                artpath = album_path+"/folder.jpg"
            # Flowboxitem => image =>  pixbuf
            pixbuf = child.get_child().get_pixbuf()
            try: # Gdk < 3.15 was missing save method, > 3.15 is missing savev method :(
                pixbuf.save(artpath, "jpeg", ["quality"], ["90"])
            except:
                pixbuf.savev(artpath, "jpeg", ["quality"], ["90"])
            Objects.art.clean_cache(self._album_id, ART_SIZE_SMALL)
            Objects.art.clean_cache(self._album_id, ART_SIZE_MEDIUM)
            Objects.art.clean_cache(self._album_id, ART_SIZE_BIG)
            Objects.player.announce_cover_update(self._album_id)
        except Exception as e:
            print("Check rights on ", album_path)
            print(e)
            pass
        self.hide()
        self._streams = {}
        
        
