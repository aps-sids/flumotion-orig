# -*- Mode: Python -*-
# vi:si:et:sw=4:sts=4:ts=4

# Flumotion - a streaming media server
# Copyright (C) 2004,2005,2006,2007,2008,2009 Fluendo, S.L.
# Copyright (C) 2010,2011 Flumotion Services, S.A.
# All rights reserved.
#
# This file may be distributed and/or modified under the terms of
# the GNU Lesser General Public License version 2.1 as published by
# the Free Software Foundation.
# This file is distributed without any warranty; without even the implied
# warranty of merchantability or fitness for a particular purpose.
# See "LICENSE.LGPL" in the source distribution for more information.
#
# Headers in this file shall remain intact.

from gi.repository import Gst

from twisted.internet import defer

from flumotion.common import errors, gstreamer, messages
from flumotion.common.i18n import N_, gettexter
from flumotion.component import feedcomponent
from flumotion.component.effects.volume import volume
from flumotion.worker.checks import check

__version__ = "$Rev$"
T_ = gettexter()


class AudioTestMedium(feedcomponent.FeedComponentMedium):

    def remote_setFrequency(self, frequency):
        """
        @type frequency: int
        """
        return self.comp.setFrequency(frequency)

    def remote_setWave(self, wave):
        """
        @type wave: int
        """
        return self.comp.setWave(wave)


class AudioTest(feedcomponent.ParseLaunchComponent):
    componentMediumClass = AudioTestMedium

    def init(self):
        self.uiState.addKey('wave', 0)
        self.uiState.addKey('frequency', 440)
        self.uiState.addKey('samplerate', 44100)

    def do_check(self):
        levelD = check.do_check(self, check.checkPlugin, 'level', 'level')
        audiotestD = check.do_check(self, check.checkPlugin, 'audiotestsrc',
            'audiotestsrc')
        volumeD = check.do_check(self, check.checkPlugin, 'volume', 'volume')
        dl = defer.DeferredList([levelD, audiotestD, volumeD])
        return dl

    def get_pipeline_string(self, properties):
        samplerate = properties.get('samplerate', 44100)
        wave = properties.get('wave', 0)
        self.samplerate = samplerate
        volume = properties.get('volume', 1.0)

        is_live = 'is-live=true'
        source = 'audiotestsrc'

        if not gstreamer.element_factory_exists(source):
            raise errors.MissingElementError(source)

        return ('%s name=source wave=%s %s ! ' \
            'identity name=identity silent=TRUE ! ' \
            'audio/x-raw,rate=%d ! ' \
            'volume name=volume volume=%f ! level name=level'
                % (source, wave, is_live, samplerate, volume))

    def configure_pipeline(self, pipeline, properties):

        self.fixRenamedProperties(properties, [
             ('freq', 'frequency'),
             ])

        element = self.get_element('source')
        if 'frequency' in properties:
            element.set_property('freq', properties['frequency'])
            self.uiState.set('frequency', properties['frequency'])

        if 'drop-probability' in properties:
            vt = gstreamer.get_plugin_version('coreelements')
            if not vt:
                raise errors.MissingElementError('identity')
            if not vt > (0, 10, 12, 0):
                self.addMessage(
                    messages.Warning(T_(N_(
                        "The 'drop-probability' property is specified, but "
                        "it only works with GStreamer core newer than 0.10.12."
                        " You should update your version of GStreamer."))))
            else:
                drop_probability = properties['drop-probability']
                if drop_probability < 0.0 or drop_probability > 1.0:
                    self.addMessage(
                        messages.Warning(T_(N_(
                            "The 'drop-probability' property can only be "
                            "between 0.0 and 1.0."))))
                else:
                    identity = self.get_element('identity')
                    identity.set_property('drop-probability',
                        drop_probability)

        self.uiState.set('samplerate', self.samplerate)
        self.uiState.set('wave', int(element.get_property('wave')))

        level = pipeline.get_by_name('level')
        vol = volume.Volume('volume', level, pipeline)
        self.addEffect(vol)

    def setVolume(self, value):
        self.debug("Volume set to %d" % value)
        element = self.get_element('volume')
        element.set_property('volume', value)

    def getVolume(self):
        element = self.get_element('volume')
        return element.get_property('volume')

    def setFrequency(self, frequency):
        element = self.get_element('source')
        element.set_property('freq', frequency)
        self.uiState.set('frequency', frequency)

    def setWave(self, wave):
        element = self.get_element('source')
        element.set_property('wave', wave)
        self.uiState.set('wave', wave)
