from gi.repository import Gtk, GObject, Gdk
from gettext import gettext as _

from yaelle.database import Database
from yaelle.widgets import *

class LoadingView(Gtk.Grid):
	def __init__(self):
		Gtk.Grid.__init__(self)
		self._ui = Gtk.Builder()
		self._ui.add_from_resource('/org/gnome/Yaelle/Loading.ui')
		self.set_property('halign', Gtk.Align.CENTER)
		self.set_property('valign', Gtk.Align.CENTER)
		self.set_vexpand(True)
		self.set_hexpand(True)
		self._label = self._ui.get_object('label')
		self._label.set_label(_("Loading please wait..."))
		self.add(self._ui.get_object('image'))
		self.add(self._label)
		self.show_all()
		

	def set_label(self, str):
		self._label.set_label(str)
		

class ArtistView(Gtk.Grid):

	def __init__(self, db, artist_id):
		Gtk.Grid.__init__(self)
		self._ui = Gtk.Builder()
		self._ui.add_from_resource('/org/gnome/Yaelle/ArtistView.ui')
		self.set_border_width(0)
		
		self._artist_id = artist_id
		self._db = db

		artist_name = self._db.get_artist_by_id(artist_id)
		self._ui.get_object('artist').set_label(artist_name)

		self._albumbox = Gtk.VBox()
		
		self._scrolledWindow = Gtk.ScrolledWindow()
		self._scrolledWindow.set_policy(
										Gtk.PolicyType.NEVER,
										Gtk.PolicyType.AUTOMATIC)
		self._scrolledWindow.add(self._albumbox)
		self.add(self._ui.get_object('ArtistView'))
		self.add(self._scrolledWindow)
		self.show_all()
        
	def _add_album(self, album_id):
		widget = AlbumWidgetSongs(self._db, album_id)
		self._albumbox.add(widget)
		widget.show()		

	def populate(self):
		for (id, name) in self._db.get_albums_by_artist(self._artist_id):
			self._add_album(id)
			
class AlbumView(Gtk.ScrolledWindow):

	def __init__(self, db, genre_id):
		Gtk.ScrolledWindow.__init__(self)
		self.set_border_width(0)
		
		self._genre_id = genre_id
		self._db = db

		self._widgets = []
		self._albumbox = Gtk.FlowBox()
		self._albumbox.set_homogeneous(True)
		self._albumbox.set_selection_mode(Gtk.SelectionMode.NONE)
		self.set_vexpand(True)
		self.set_hexpand(True)
		self.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
		self.add(self._albumbox)
		self.show_all()
        
	def _add_albums(self):
		for (id, name) in self._db.get_albums_by_genre(self._genre_id):
			widget = AlbumWidget(self._db, id)
			widget.show()
			self._albumbox.insert(widget, -1)		

	def populate(self):
		GLib.idle_add(self._add_albums)
