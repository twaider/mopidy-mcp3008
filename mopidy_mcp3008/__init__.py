from __future__ import unicode_literals

import logging
import os

from mopidy import config, ext
from .mcp_3008 import Mcp3008

__version__ = '0.1.0'

# TODO: If you need to log, use loggers named after the current Python module
logger = logging.getLogger(__name__)


class Extension(ext.Extension):

    dist_name = 'Mopidy-MCP3008'
    ext_name = 'mcp3008'
    version = __version__

    def get_default_config(self):
        conf_file = os.path.join(os.path.dirname(__file__), 'ext.conf')
        return config.read(conf_file)

    def get_config_schema(self):
        #schema = super(Extension, self).get_config_schema()
        # TODO: Comment in and edit, or remove entirely
        #schema['username'] = config.String()
        #schema['password'] = config.Secret()
        #return schema
	schema = super(Extension, self).get_config_schema()
        schema['adc_chan_vol'] = config.Integer()
        schema['deadzone_vol_lo'] = config.Integer()
        schema['deadzone_vol_hi'] = config.Integer()
        schema['gpio_spiclk'] = config.Integer()
        schema['gpio_spics'] = config.Integer()
        schema['gpio_spimiso'] = config.Integer()
        schema['gpio_spimosi'] = config.Integer()
        return schema

    def setup(self, registry):
        # You will typically only implement one of the following things
        # in a single extension.

        # TODO: Edit or remove entirely
        #from .frontend import FoobarFrontend
        #registry.add('frontend', FoobarFrontend)

        # TODO: Edit or remove entirely
        #from .backend import FoobarBackend
        #registry.add('backend', FoobarBackend)

        # TODO: Edit or remove entirely
        #registry.add('http:static', {
        #    'name': self.ext_name,
        #    'path': os.path.join(os.path.dirname(__file__), 'static'),
        #})
	registry.add('frontend', Mcp3008)
