# -*- Mode: Python; test-case-name: flumotion.test.test_enum -*-
# vi:si:et:sw=4:sts=4:ts=4
#
# flumotion/wizard/enums.py: python enum implementation
#
# Flumotion - a streaming media server
# Copyright (C) 2004 Fluendo, S.L. (www.fluendo.com). All rights reserved.

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




class EnumMetaClass(type):
    def __len__(self):
        return len(self.__enums__)

    def __getitem__(self, value):
        try:
            return self.__enums__[value]
        except KeyError:
            raise StopIteration

    def __setitem__(self, value, enum):
        self.__enums__[value] = enum
        setattr(self, enum.name, enum)


class Enum(object):
    __metaclass__ = EnumMetaClass
    def __init__(self, value, name, nick=None):
        self.value = value
        self.name = name
        
        if nick is None:
            nick = name
            
        self.nick = nick

    def __repr__(self):
        return '<enum %s of type %s>' % (self.name,
                                         self.__class__.__name__)

    def get(self, value):
        return self.__enums__[value]
    get = classmethod(get)

    def set(self, value, item):
        self[value] = item
    set = classmethod(set)


    
class EnumClass(object):
    def __new__(self, type_name, names=(), nicks=(), **extras):
        if nicks:
            if len(names) != len(nicks):
                raise TypeError("nicks must have the same length as names")
        else:
            nicks = names

        for extra in extras.values():
            if not isinstance(extra, tuple):
                raise TypeError('extra must be a tuple, not %s' % type(extra))
                
            if len(extra) != len(names):
                raise TypeError("extra items must have a length of %d" %
                                len(names))
            
        etype = EnumMetaClass(type_name, (Enum,), dict(__enums__={}))
        for value, name in enumerate(names):
            enum = etype(value, name, nicks[value])
            for extra_key, extra_values in extras.items():
                assert not hasattr(enum, extra_key)
                setattr(enum, extra_key, extra_values[value])
            etype[value] = enum
            
        return etype


# Sources
VideoDevice = EnumClass('VideoDevice',
                        ('Webcam', 'TVCard', 'Firewire', 'Test'),
                        ('Web camera',
                         'TV card',
                         'Firewire video',
                         'Test video source'),
                        step=('Webcam',
                              'TV Card',
                              'Firewire',
                              'Test Video Source'),
                        component_type=('web-camera',
                                        'tv-card',
                                        'firewire',
                                        'videotest'),
                        element_names=(('v4lsrc',),
                                       ('v4lsrc',),
                                       ('videotestsrc',),
                                       ('dvdec', 'gst1394src')))
AudioDevice = EnumClass('AudioDevice',
                        ('Soundcard', 'Firewire', 'Test'),
                        ('Sound card', 'Firewire audio', 'Test audio source'),
                        step=('Soundcard', 'Unused', 'Test Audio Source'),
                        component_type=('soundcard',
                                        'firewire',
                                        'audiotest'))
# TVCard
TVCardDevice = EnumClass('TVCardDevice', ('/dev/video0',
                                          '/dev/video1',
                                          '/dev/video2'))
TVCardSignal = EnumClass('TVCardSignal', ('Composite', 'RCA'))

# Videotestsrc, order is important here, since it maps to
#               GstVideotestsrcPattern
VideoTestPattern = EnumClass('VideoTestPattern',
                             ('Bars', 'Snow', 'Black'),
                             ('SMPTE Color bars',
                              'Random (television snow)',
                              'Totally black'))

VideoTestFormat = EnumClass('VideoTestFormat', ('YUV', 'RGB'))

# Sound card
SoundcardSource = EnumClass('SoundcardSource', ('OSS',
                                                'Alsa'),
                            element=('osssrc', 'alsasrc'))

SoundcardOSSDevice = EnumClass('SoundcardOSSDevice', ('/dev/dsp',
                                                      '/dev/dsp1',
                                                      '/dev/dsp2'))
SoundcardAlsaDevice = EnumClass('SoundcardAlsaDevice', ('hw:0',
                                                        'hw:1',
                                                        'hw:2'))
SoundcardInput = EnumClass('SoundcardInput',
                           ('Line in', 'Microphone', 'CD'))
SoundcardChannels = EnumClass('SoundcardChannels', ('Stereo', 'Mono'))
SoundcardSamplerate = EnumClass('SoundcardSamplerate', ('44100',
                                                        '22050',
                                                        '11025',
                                                        '8000'))
SoundcardBitdepth = EnumClass('SoundcardBitdepth', ('16', '8'),
                              ('16-bit', '8-bit'))

# Encoding format
EncodingFormat = EnumClass('EncodingFormat', ('Ogg', 'Multipart'),
                           component_type=('ogg-muxer',
                                           'multipart-muxer'))
EncodingVideo = EnumClass('EncodingVideo',
                          ('Theora', 'Smoke', 'JPEG'),
                          component_type=('theora-encoder',
                                          'smoke-encoder',
                                          'jpeg-encoder'),
                          step=('Theora', 'Smoke', 'JPEG'))
EncodingAudio = EnumClass('EncodingAudio', ('Vorbis', 'Speex', 'Mulaw'),
                          component_type=('vorbis-encoder',
                                          'speex-encoder',
                                          'mulaw-encoder'),
                          step=('Vorbis', 'Speex', 'Mulaw'))

# Disk writer
RotateTime = EnumClass('RotateTime',
                       ('Minutes', 'Hours', 'Days', 'Weeks'),
                       ('minute(s)', 'hour(s)', 'day(s)', 'week(s)'),
                       unit=(60,
                              60*60,
                              60*60*24,
                              60*60*25*7))
RotateSize = EnumClass('RotateSize',
                      ('kB', 'MB', 'GB', 'TB'),
                       unit=(1 << 10L,
                              1 << 20L,
                              1 << 30L,
                              1 << 40L))
 
LicenseType = EnumClass('LicenseType',
                        ('CC', 'Commercial'),
                        ('Creative Commons', 'Commercial'))
