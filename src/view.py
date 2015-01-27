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

from gi.repository import Gtk, GObject, Gdk
from gettext import gettext as _
from time import sleep
from _thread import start_new_thread

from lollypop.define import Objects
from lollypop.database import Database
from lollypop.playlists import PlaylistsManagePopup
from lollypop.view_widgets import *
from lollypop.utils import translate_artist_name

"""
	Loading view used on db update
"""
class LoadingView(Gtk.Bin):
	def __init__(self):
		Gtk.Bin.__init__(self)
		self.set_property('halign', Gtk.Align.CENTER)
		self.set_property('valign', Gtk.Align.CENTER)
		label = Gtk.Label()
		label.set_label(_("Loading please wait..."))
		label.show()
		self.add(label)
		self.show()
		
	def remove_signals(self):
		pass
	def stop(self):
		pass


"""
	PlaylistsView view used to manage playlists
"""
class PlaylistsView(Gtk.Bin):
	def __init__(self):
		Gtk.Bin.__init__(self)
		self.set_property('halign', Gtk.Align.CENTER)
		self.set_property('valign', Gtk.Align.CENTER)
		button = Gtk.Button(_("Manage playlists"))
		button.connect('clicked', self._on_button_clicked)
		button.show()
		self.add(button)
		self.show()
		
	def remove_signals(self):
		pass
	def stop(self):
		pass
		
#######################
# PRIVATE             #
#######################	
	"""
		Show playlists management dialog
		@param button as Gtk.Button
	"""
	def _on_button_clicked(self, button):
		popup = PlaylistsManagePopup(-1, False)
		popup.show()

"""
	Generic view
"""
class View(Gtk.Grid):
	__gsignals__ = {
        'finished': (GObject.SIGNAL_RUN_FIRST, None, ())
    }
    
	def __init__(self):
		Gtk.Grid.__init__(self)
		self.set_property("orientation", Gtk.Orientation.VERTICAL)
		self.set_border_width(0)
		if Objects.settings.get_value('dark-view'):
			self.get_style_context().add_class('black')
		Objects.player.connect("current-changed", self._on_current_changed)
		Objects.player.connect("cover-changed", self._on_cover_changed)
		self._stop = False # Stop populate thread
		
	"""
		Remove signals on player object
	"""
	def remove_signals(self):
		Objects.player.disconnect_by_func(self._on_current_changed)
		Objects.player.disconnect_by_func(self._on_cover_changed)
		
#######################
# PRIVATE             #
#######################

	"""
		Current song changed
		Update context and content
		@param player as Player
	"""
	def _on_current_changed(self, player):
		self._update_content(player)
		self._update_context(player)

	"""
		Update album cover in view
		Do nothing here
	"""
	def _on_cover_changed(self, widget, album_id):
		pass

	"""
		Update content view
		Do nothing here
	"""
	def _update_content(self, player):
		pass

	"""
		Update context view
		Do nothing here
	"""
	def _update_context(self, player):
		pass

	"""
		Stop populate thread
	"""
	def stop(self):
		self._stop = True
		

"""
	Artist view is a vertical grid with album songs widgets
"""
class ArtistView(View):
	"""
		Init ArtistView ui with a scrolled grid of AlbumDetailedWidget
		@param: artist id as int
		@param: genre id as int
		@param: show_artist_details as bool
	"""
	def __init__(self, artist_id, genre_id, show_artist_details):
		View.__init__(self)
		
		if show_artist_details:
			self._ui = Gtk.Builder()
			self._ui.add_from_resource('/org/gnome/Lollypop/ArtistView.ui')
			self.add(self._ui.get_object('ArtistView'))
			artist_name = Objects.artists.get_name(artist_id)
			artist_name = translate_artist_name(artist_name)
			self._ui.get_object('artist').set_label(artist_name)

		self._artist_id = artist_id
		self._genre_id = genre_id
		self._show_menu = show_artist_details

		self._albumbox = Gtk.Grid()
		self._albumbox.set_property("orientation", Gtk.Orientation.VERTICAL)
		self._scrolledWindow = Gtk.ScrolledWindow()
		self._scrolledWindow.set_vexpand(True)
		self._scrolledWindow.set_policy(Gtk.PolicyType.AUTOMATIC,
										Gtk.PolicyType.AUTOMATIC)
		self._scrolledWindow.add(self._albumbox)

		self.add(self._scrolledWindow)
		self.show_all()

	"""
		Populate the view, can be threaded
	"""
	def populate(self):
		sql = Objects.db.get_cursor()
		if self._artist_id == COMPILATIONS:
			albums = Objects.albums.get_compilations(self._genre_id, sql)
		elif self._genre_id == ALL:
			albums = Objects.albums.get_ids(self._artist_id, None, sql)
		else:
			albums = Objects.albums.get_ids(self._artist_id, self._genre_id, sql)
		GLib.idle_add(self._add_albums, albums)
		sql.close()
		
#######################
# PRIVATE             #
#######################

	"""
		Update album cover in view
		@param album id as int
	"""
	def _on_cover_changed(self, widget, album_id):
		for widget in self._albumbox.get_children():
			widget.update_cover(album_id)

	"""
		Update the content view
		@param player as Player
	"""
	def _update_content(self, player):
		if self._albumbox:
			for widget in self._albumbox.get_children():
				widget.update_playing_track(player.current.id)

	"""
		Pop an album and add it to the view,
		repeat operation until album list is empty
		@param [album ids as int]
	"""
	def _add_albums(self, albums):
		size_group = Gtk.SizeGroup(mode=Gtk.SizeGroupMode.HORIZONTAL)
		if len(albums) > 0 and not self._stop:
			widget = AlbumDetailedWidget(albums.pop(0), self._genre_id, True, self._show_menu, size_group)
			widget.show()
			self._albumbox.add(widget)
			if widget.eventbox:
				widget.eventbox.get_window().set_cursor(Gdk.Cursor(Gdk.CursorType.HAND1))
			GLib.idle_add(self._add_albums, albums, priority=GLib.PRIORITY_LOW)
		else:
			self._stop = False
			self.emit('finished')

"""
	Album view is a flowbox of albums widgets with album name and artist name
"""
class AlbumView(View):

	"""
		Init album view ui with a scrolled flow box and a scrolled context view
	"""
	def __init__(self, genre_id):
		View.__init__(self)
		self._genre_id = genre_id
		self._artist_id = None
		self._albumsongs = None
		self._context_widget = None

		self._albumbox = Gtk.FlowBox()
		self._albumbox.set_selection_mode(Gtk.SelectionMode.NONE)
		self._albumbox.connect("child-activated", self._on_album_activated)
		self._albumbox.set_max_children_per_line(100)

		self._scrolledWindow = Gtk.ScrolledWindow()
		self._scrolledWindow.set_vexpand(True)
		self._scrolledWindow.set_hexpand(True)
		viewport = Gtk.Viewport()
		viewport.add(self._albumbox)
		viewport.set_property("valign", Gtk.Align.START)
		self._scrolledWindow.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
		self._scrolledWindow.add(viewport)
		self._scrolledWindow.show_all()
		
		self._stack = Gtk.Stack()
		self._stack.set_transition_duration(500)
		self._stack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)

		separator = Gtk.Separator()
		separator.show()
		
		self.add(self._scrolledWindow)
		self.add(separator)
		self.add(self._stack)
		self.show()

	"""
		Populate albums, thread safe
	"""	
	def populate(self):
		sql = Objects.db.get_cursor()
		if self._genre_id == ALL:
			albums = Objects.albums.get_ids(None, None, sql)
		elif self._genre_id == POPULARS:
			albums = Objects.albums.get_populars(sql)
		else:
			albums = Objects.albums.get_compilations(self._genre_id, sql)
			albums += Objects.albums.get_ids(None, self._genre_id, sql)

		GLib.idle_add(self._add_albums, albums)
		sql.close()

#######################
# PRIVATE             #
#######################
	
	"""
		Update album cover in view
		@param widget as unused, album id as int
	"""
	def _on_cover_changed(self, widget, album_id):
		if self._context_widget:
			self._context_widget.update_cover(album_id)
		for child in self._albumbox.get_children():
			for widget in child.get_children():
				widget.update_cover(album_id)

	"""
		Return next view
	"""
	def _get_next_view(self):
		for child in self._stack.get_children():
			if child != self._stack.get_visible_child():
				return child
		return None

	"""
		Update the context view
		@param player as Player
	"""
	def _update_context(self, player):
		if self._context_widget:
			self._context_widget.update_playing_track(player.current.id)

	"""
		populate context view
		@param album id as int
	"""
	def _populate_context(self, album_id):
		size_group = Gtk.SizeGroup(mode=Gtk.SizeGroupMode.HORIZONTAL)
		old_view = self._get_next_view()
		if old_view:
			self._stack.remove(old_view)
		self._context_widget = AlbumDetailedWidget(album_id, self._genre_id, False, True, size_group)
		self._context_widget.show()			
		view = Gtk.ScrolledWindow()
		view.set_min_content_height(250)
		view.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
		view.add(self._context_widget)
		view.show()
		self._stack.add(view)
		self._stack.set_visible_child(view)
			
	"""
		Show Context view for activated album
		@param flowbox, children
	"""
	def _on_album_activated(self, flowbox, child):
		if self._artist_id == child.get_child().get_id():
			self._artist_id = None
			self._stack.hide()
		else:
			self._artist_id = child.get_child().get_id()
			self._populate_context(self._artist_id)
			self._stack.show()
			self._context_widget.eventbox.get_window().set_cursor(Gdk.Cursor(Gdk.CursorType.HAND1))
	
	"""
		Pop an album and add it to the view,
		repeat operation until album list is empty
		@param [album ids as int]
	"""
	def _add_albums(self, albums):
		if len(albums) > 0 and not self._stop:
			widget = AlbumWidget(albums.pop(0))
			widget.show()
			self._albumbox.insert(widget, -1)
			GLib.idle_add(self._add_albums, albums, priority=GLib.PRIORITY_LOW)
		else:
			self._stop = False
			self.emit('finished')


"""
	Playlist view is a vertical grid with album's covers
"""
class PlaylistView(View):
	"""
		Init PlaylistView ui with a scrolled grid of PlaylistWidgets
		@param playlist name as str
	"""
	def __init__(self, name):
		View.__init__(self)
		self._name = name

		self._scrolledWindow = Gtk.ScrolledWindow()
		self._scrolledWindow.set_vexpand(True)
		self._scrolledWindow.set_policy(Gtk.PolicyType.AUTOMATIC,
										Gtk.PolicyType.AUTOMATIC)
		self._scrolledWindow.show()
		self.add(self._scrolledWindow)
		self._widget = PlaylistWidget(name)
		self._widget.show()
		self._scrolledWindow.add(self._widget)
		self.show()


	"""
		On show, connect signals
	"""
	def do_show(self):
		Objects.playlists.connect("playlist-changed", self._on_playlist_changed)
		View.do_show(self)
		
	"""
		On hide, delete signals
	"""
	def do_hide(self):
		Objects.playlists.disconnect_by_func(self._on_playlist_changed)
		View.do_hide(self)
		
	"""
		Populate view with tracks from playlist
	"""
	def populate(self):
		sql = Objects.db.get_cursor()
		tracks = Objects.playlists.get_tracks_id(self._name, sql)
		mid_tracks = int(0.5+len(tracks)/2)
		GLib.idle_add(self._widget.add_tracks, tracks, 1, mid_tracks)

#######################
# PRIVATE             #
#######################

	"""
		Update all tracks if signal is for us
		@param manager as PlaylistPopup
		@param playlist name as str
	"""
	def _on_playlist_changed(self, manager, playlist_name):
		if playlist_name != self._name:
			return
		self._widget.clear()		
		self.populate()

	"""
		Update the content view
		@param player as Player
	"""
	def _update_content(self, player):
		self._widget.update_playing_track(player.current.id)
