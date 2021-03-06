# -*- Mode: Python -*-
# vi:si:et:sw=4:sts=4:ts=4
#
# Flumotion - a streaming media server
# Copyright (C) 2004,2005,2006,2007 Fluendo, S.L. (www.fluendo.com).
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
import gst
from twisted.internet import defer

from flumotion.common import errors, messages, gstreamer
from flumotion.common.i18n import N_, gettexter
from flumotion.component import feedcomponent
from flumotion.component.effects.deinterlace import deinterlace
from flumotion.component.effects.videorate import videorate
from flumotion.component.effects.videoscale import videoscale
from flumotion.component.effects.audioconvert import audioconvert

__version__ = "$Rev$"
T_ = gettexter()


# See comments in gstdvdec.c for details on the dv format.


class DVSource(feedcomponent.ParseLaunchComponent):

    def do_check(self):
        self.debug('running PyGTK/PyGST and configuration checks')
        from flumotion.component.producers import checks
        d1 = checks.checkTicket347()
        d2 = checks.checkTicket348()
        dl = defer.DeferredList([d1, d2])
        dl.addCallback(self._checkCallback)
        return dl

    def check_properties(self, props, addMessage):
        deintMode = props.get('deinterlace-mode', 'auto')
        deintMethod = props.get('deinterlace-method', 'ffmpeg')
        fileName = props.get('filename', None)

        if deintMode not in deinterlace.DEINTERLACE_MODE:
            msg = messages.Error(T_(N_("Configuration error: '%s' " \
                "is not a valid deinterlace mode." % deintMode)))
            addMessage(msg)
            raise errors.ConfigError(msg)

        if deintMethod not in deinterlace.DEINTERLACE_METHOD:
            msg = messages.Error(T_(N_("Configuration error: '%s' " \
                "is not a valid deinterlace method." % deintMethod)))
            self.debug("'%s' is not a valid deinterlace method",
                deintMethod)
            addMessage(msg)
            raise errors.ConfigError(msg)

        if not os.path.exists(fileName):
            msg = messages.Error(T_(N_("Configuration error: '%s' " \
                "is not a valid filename." % fileName)))
            self.debug("'%s' is not a valid filename",
                fileName)
            addMessage(msg)
            raise errors.ConfigError(msg)

    def _checkCallback(self, results):
        for (state, result) in results:
            for m in result.messages:
                self.addMessage(m)

    def get_pipeline_string(self, props):
        if props.get('scaled-width', None) is not None:
            self.warnDeprecatedProperties(['scaled-width'])

        self.is_square = props.get('is-square', False)
        self.width = props.get('width', 0)
        self.height = props.get('height', 0)
        decoder = props.get('decoder', 'dvdec')
        if not self.is_square and not self.height:
            self.height = int(576 * self.width/720.) # assuming PAL
        self.add_borders = props.get('add-borders', True)
        filename = "location=\"%s\"" % props.get('filename', None)
        self.deintMode = props.get('deinterlace-mode', 'auto')
        self.deintMethod = props.get('deinterlace-method', 'ffmpeg')

        fr = props.get('framerate', None)
        if fr is not None:
            self.framerate = gst.Fraction(fr[0], fr[1])
        else:
            self.framerate = None

        # FIXME: might be nice to factor out dv1394src ! dvdec so we can
        # replace it with videotestsrc of the same size and PAR, so we can
        # unittest the pipeline
        # need a queue in case tcpserversink blocks somehow
        template = ('filesrc %s'
                    '    ! queue leaky=2 max-size-time=1000000000'
                    '    ! dvdemux name=demux'
                    '  demux. ! queue ! %s name=decoder'
                    '    ! @feeder:video@'
                    '  demux. ! queue ! audio/x-raw-int '
                    '    ! volume name=setvolume'
                    '    ! level name=volumelevel message=true '
                    '    ! @feeder:audio@' % (filename, decoder))

        return template

    def configure_pipeline(self, pipeline, properties):
        self.volume = pipeline.get_by_name("setvolume")
        from flumotion.component.effects.volume import volume
        comp_level = pipeline.get_by_name('volumelevel')
        vol = volume.Volume('inputVolume', comp_level, pipeline)

        decoder = pipeline.get_by_name("decoder")
        if gstreamer.element_has_property(decoder, 'drop-factor'):
            if self.framerate:
                framerate = float(self.framerate.num / self.framerate.denom)
                if 12.5 < framerate:
                    drop_factor = 1
                elif 6.3 < framerate <= 12.5:
                    drop_factor = 2
                elif 3.2 < framerate <= 6.3:
                    drop_factor = 4
                elif framerate <= 3.2:
                    drop_factor = 8
            else:
                drop_factor = 1
            decoder.set_property('drop-factor', drop_factor)

        vr = videorate.Videorate('videorate',
            decoder.get_pad("src"), pipeline, self.framerate)
        self.addEffect(vr)
        vr.plug()

        deinterlacer = deinterlace.Deinterlace('deinterlace',
            vr.effectBin.get_pad("src"), pipeline,
            self.deintMode, self.deintMethod)
        self.addEffect(deinterlacer)
        deinterlacer.plug()

        videoscaler = videoscale.Videoscale('videoscale', self,
            deinterlacer.effectBin.get_pad("src"), pipeline,
            self.width, self.height, self.is_square, self.add_borders)
        self.addEffect(videoscaler)
        videoscaler.plug()

        # Setting a tolerance of 20ms should be enough (1/2 frame), but
        # we set it to 40ms to be more conservatives
        ar = audioconvert.Audioconvert('audioconvert',
                                       comp_level.get_pad("src"),
                                       pipeline, tolerance=40 * gst.MSECOND)
        self.addEffect(ar)
        ar.plug()

    def getVolume(self):
        return self.volume.get_property('volume')

    def setVolume(self, value):
        """
        @param value: float between 0.0 and 4.0
        """
        self.debug("Setting volume to %f" % (value))
        self.volume.set_property('volume', value)
