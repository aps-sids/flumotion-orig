include $(top_srcdir)/common/python.mk

component_PYTHON = __init__.py voaac.py wizard_gtk.py
componentdir = $(libdir)/flumotion/python/flumotion/component/encoders/voaac
component_DATA = voaac.xml

clean-local:
	rm -rf *.pyc *.pyo

EXTRA_DIST = $(component_DATA)
