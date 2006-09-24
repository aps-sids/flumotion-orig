# -*- Mode: Python -*-
# vi:si:et:sw=4:sts=4:ts=4
#
# Flumotion - a streaming media server
# Copyright (C) 2004,2005,2006 Fluendo, S.L. (www.fluendo.com).
# All rights reserved.

# This file may be distributed and/or modified under the terms of
# the GNU General Public License version 2 as published by
# the Free Software Foundation.
# This file is distributed without any warranty; without even the implied
# warranty of merchantability or fitness for a particular purpose.
# See "LICENSE.GPL" in the source distribution for more information.

# Licensees having purchased or holding a valid Flumotion Advanced
# Streaming Server license may use this file in accordance with the
# Flumotion Advanced Streaming Server Commercial License Agreement.
# See "LICENSE.Flumotion" in the source distribution for more information.

# Headers in this file shall remain intact.

import os
import gtk

from flumotion.common import errors

from flumotion.component.base.admin_gtk import BaseAdminGtk, BaseAdminGtkNode

class FilenameNode(BaseAdminGtkNode):
    glade_file = os.path.join('flumotion', 'component', 'consumers',
                              'disker', 'disker.glade')

    def haveWidgetTree(self):
        self.labels = {}
        self.widget = self.wtree.get_widget('filename-widget')
        self.currentFilenameLabel = self.wtree.get_widget('label-current')
        button = self.wtree.get_widget('button-new')
        button.connect('clicked',self.cb_button_clicked)
        self.shown = False

    def cb_button_clicked(self, button):
        d = self.callRemote("changeFilename")
        d.addErrback(self.changeFilenameErrback)

    def changeFilenameErrback(self,failure):
        self.warning("Failure %s changing filename: %s" % (
            failure.type, failure.getErrorMessage()))
        return None

    def setUIState(self, state):
        super(FilenameNode, self).setUIState(state)
        self.stateSet(state, 'filename', state.get('filename'))

    def stateSet(self, state, key, value):
        if key == 'filename':
            self.currentFilenameLabel.set_text(value or '<waiting>')
    
class DiskerAdminGtk(BaseAdminGtk):
    def setup(self):
        filename = FilenameNode(self.state, self.admin)
        self._nodes = {'Filename' : filename}
        return BaseAdminGtk.setup(self)

    def getNodes(self):
        return self._nodes

    def setUIState(self, state):
        super(DiskerAdminGtk, self).setUIState(state)
        self._nodes['Filename'].setUIState(state)

GUIClass = DiskerAdminGtk
