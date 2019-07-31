# -*- coding: utf-8 -*-
#
# export.py -- export plugin for eog
#
# Copyright (c) 2012  Jendrik Seipp (jendrikseipp@web.de)
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2, or (at your option)
# any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.

import os
import shutil
import glob

from gi.repository import GObject, GLib, Eog, Gio, Gtk, PeasGtk

_MENU_ID = 'Export'
_ACTION_NAME = 'export-to-folder'

EXPORT_DIR = os.path.join(os.path.expanduser('~'), 'exported-images')


class ExportPlugin(GObject.Object, Eog.WindowActivatable):
    window = GObject.property(type=Eog.Window)

    def __init__(self):
        GObject.Object.__init__(self)

    @property
    def export_dir(self):
        return EXPORT_DIR

    def do_activate(self):
        model = self.window.get_gear_menu_section('plugins-section')
        action = Gio.SimpleAction.new(_ACTION_NAME)
        action.connect('activate', self.export_cb, self.window)

        self.window.add_action(action)
        menu = Gio.Menu()
        menu.append('_Export with src', 'win.' + _ACTION_NAME)
        item = Gio.MenuItem.new_section(None, menu)
        item.set_attribute([('id', 's', _MENU_ID)])
        model.append_item(item)

        thumbview = self.window.get_thumb_view()
        self.selection_changed_handler_id = \
            thumbview.connect('selection-changed', self.update_action_state)
        self.update_action_state(thumbview)

        # Add accelerator key
        app = Eog.Application.get_instance()
        app.set_accels_for_action('win.' + _ACTION_NAME, ['E', None])

    def do_deactivate(self):
        menu = self.window.get_gear_menu_section('plugins-section')
        for i in range(0, menu.get_n_items()):
            value = menu.get_item_attribute_value(i, 'id',
                                                  GLib.VariantType.new('s'))

            if value and value.get_string() == _MENU_ID:
                menu.remove(i)
                break

        # Disable accelerator key
        app = Eog.Application.get_instance()
        app.set_accels_for_action('win.' + _ACTION_NAME, ['E', None])

        if self.selection_changed_handler_id is not None:
            thumbview = self.window.get_thumb_view()
            thumbview.disconnect(self.selection_changed_handler_id)
            self.selection_changed_handler_id = None

        self.window.remove_action(_ACTION_NAME)

    def export_cb(self, action, parameter, window):
        # Get path to current image.
        image = window.get_image()
        if not image:
            print('No image can be exported')
            return
        src = image.get_file().get_path()
        src_dir = os.path.dirname(src)

        name = os.path.basename(src)
        dest = os.path.join(self.export_dir, name)

        short_name = os.path.splitext(name)[0]
        # Create directory if it doesn't exist.
        try:
            os.makedirs(self.export_dir)
        except OSError:
            pass

        for f in glob.glob('{}/{}*'.format(src_dir, short_name)):
            file_name = os.path.basename(f)
            file_ext = os.path.splitext(f)[1]
            file_dest = os.path.join(self.export_dir, file_name)

            if not os.path.isfile(file_dest):
                shutil.copy2(f, file_dest)
                pass
            else:
                ii = 2
                while True:
                    new_name = os.path.join(self.export_dir, short_name + "_" + str(ii) + file_ext)
                    if not os.path.exists(new_name):
                        shutil.copy(f, new_name)
                        break
                    ii += 1

            print(f)
            #shutil.copy2(f, file_dest)
        #print('Copied %s into %s' % (name, self.export_dir))

    def update_action_state(self, thumbview=None):
        action = self.window.lookup_action(_ACTION_NAME)
        enable = False
        if thumbview is None:
            thumbview = self.window.get_thumb_view()

        if thumbview is not None:
            enable = (thumbview.get_n_selected() > 0)

        action.set_enabled(enable)

