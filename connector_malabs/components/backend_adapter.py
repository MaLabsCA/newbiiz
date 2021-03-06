# -*- coding: utf-8 -*-
#
#
#    Tech-Receptives Solutions Pvt. Ltd.
#    Copyright (C) 2009-TODAY Tech-Receptives(<http://www.techreceptives.com>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#
import base64
import csv
import logging

from odoo.addons.component.core import AbstractComponent

try:
    from xmlrpc import client as xmlrpclib
except ImportError:
    import xmlrpclib

_logger = logging.getLogger(__name__)

recorder = {}

PACKAGE = [('retail', 'RETAIL'), ('bulk', 'BULK')]

def call_to_key(method, arguments):
    """ Used to 'freeze' the method and arguments of a call to MalabsCommerce
    so they can be hashable; they will be stored in a dict.

    Used in both the recorder and the tests.
    """
    def freeze(arg):
        if isinstance(arg, dict):
            items = dict((key, freeze(value)) for key, value
                         in arg.iteritems())
            return frozenset(items.iteritems())
        elif isinstance(arg, list):
            return tuple([freeze(item) for item in arg])
        else:
            return arg

    new_args = []
    for arg in arguments:
        new_args.append(freeze(arg))
    return (method, tuple(new_args))


def record(method, arguments, result):
    """ Utility function which can be used to record test data
    during synchronisations. Call it from WooCRUDAdapter._call

    Then ``output_recorder`` can be used to write the data recorded
    to a file.
    """
    recorder[call_to_key(method, arguments)] = result


def output_recorder(filename):
    import pprint
    with open(filename, 'w') as f:
        pprint.pprint(recorder, f)
    _logger.debug('recorder written to file %s', filename)


class Malabs_CSV(object):

    def __init__(self, cvs_files):
        self._cvs_files = cvs_files

    @property
    def location(self):
        location = self._cvs_files
        return location


class WooCRUDAdapter(AbstractComponent):
    """ External Records Adapter for woo """

    _name = 'malabs.crud.adapter'
    _inherit = ['base.backend.adapter']
    _usage = 'backend.adapter'

    def __init__(self, connector_env):
        """

        :param connector_env: current environment (backend, session, ...)
        :type connector_env: :class:`connector.connector.ConnectorEnvironment`
        """
        super(WooCRUDAdapter, self).__init__(connector_env)
        backend = self.backend_record
        malabs = Malabs_CSV(
            backend.csv_file
        )
        self.malabs = malabs

    def search(self, filters=None):
        """ Search records according to some criterias
        and returns a list of ids """
        raise NotImplementedError

    def read(self, id, attributes=None):
        """ Returns the information of a record """
        raise NotImplementedError

    def search_read(self, filters=None):
        """ Search records according to some criterias
        and returns their information"""
        raise NotImplementedError

    def create(self, data):
        """ Create a record on the external system """
        raise NotImplementedError

    def write(self, id, data):
        """ Update records on the external system """
        raise NotImplementedError

    def delete(self, id):
        """ Delete a record on the external system """
        raise NotImplementedError

    def _call(self, csv_files):

        # TODO 1. 与odoo-edi中处理CSV的方法作对比。 2. Linux一平台也要试一下。
        reader_origin = csv.reader(base64.b64decode(csv_files).decode(errors='ignore').split(sep='\r\n'))
        reader = []
        for row in reader_origin:
            reader.append(row)

        data = []
        keys = reader[0]
        values = reader[1:]
        for val in values:
            if val:
                d = {}
                i = 0
                for key in keys:
                    d[key] = val[i]
                    i += 1

                d['price'] = d.get('Sales Price', None)
                d['cost'] = d.get('Cost', None)
                d['category'] = d.get('PDL', None)
                d['ma_labs_list'] = d.get('Ma Labs List #', None)
                d['mfr_part'] = d.get('Mfr Part #', None)
                d['manufacturer'] = d.get('Manufacturer', None)
                d['unit'] = d.get('Unit', None)
                d['instant_rebate'] = d.get('Instant Rebate', None)
                d['length'] = d.get('Length', 0)
                d['item'] = d.get('item_no')
                d['instant_rebate_start'] = d.get('Instant Rebate Start', None)
                d['instant_rebate_end'] = d.get('Instant Rebate End', None)

                for selection in PACKAGE:
                    if selection[1] == d.get('Package', None):
                        d['package'] = selection[0]

                for key in (
                    'Cost',
                    'Instant Rebate',
                    'Instant Rebate End',
                    'Instant Rebate Start',
                    'Length',
                    'Ma Labs List #',
                    'Manufacturer',
                    'Mfr Part #',
                    'PDL',
                    'Package',
                    'Sales Price',
                    'Unit',
                    'item_no',
                ):
                    del d[key]

                if d.get('barcode', None):
                    data.append(d)
        return data


class GenericAdapter(AbstractComponent):
    _name = 'malabs.adapter'
    _inherit = ['malabs.crud.adapter']

    def search(self, filters=None):
        """ Search records according to some criterias
        and returns a list of ids

        :rtype: list
        """
        _logger.info(u'如果调用，肯定报错。')
        return self._call('%s.search' % self._woo_model,
                          [filters] if filters else [{}])

    def read(self, filters=None, from_date=None, to_date=None):
        """ Read records according to some criteria and return a
        list of records

        :rtype: list
        """
        if filters is None:
            filters = {}
        WOO_DATETIME_FORMAT = '%Y/%m/%d %H:%M:%S'
        dt_fmt = WOO_DATETIME_FORMAT
        if from_date is not None:
            # updated_at include the created records
            filters.setdefault('updated_at', {})
            filters['updated_at']['from'] = from_date.strftime(dt_fmt)
        if to_date is not None:
            filters.setdefault('updated_at', {})
            filters['updated_at']['to'] = to_date.strftime(dt_fmt)

        res = self._call(self.malabs.location)

        return res

    def search_read(self, filters=None):
        """ Search records according to some criterias
        and returns their information"""
        return self._call('%s.list' % self._woo_model, [filters])

    def create(self, data):
        """ Create a record on the external system """
        if data.get('woo_id_parent', None):
            data['parent'] = data.get('woo_id_parent')
            del data['woo_id_parent']

        res = self._call(method='POST', endpoint='%s' % self._woo_model, data=data)
        return res

    def write(self, id, data):
        """ Update records on the external system """
        res = self._call(method='PUT', endpoint='%s/%s' % (self._woo_model, int(id)), data=data)
        return res

    def delete(self, id):
        """ Delete a record on the external system """
        return self._call('%s.delete' % self._woo_model, [int(id)])
