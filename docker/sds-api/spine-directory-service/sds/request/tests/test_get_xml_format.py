from unittest import TestCase

from lxml import etree

from request.xml_formatter import get_xml_format


class TestGetXmlFormat(TestCase):

    def test_get_xml_format(self):
        print('---------------------------------- test: ')
        print(get_xml_format())
        # tree = etree.parse(get_xml_format())
        root = etree.fromstring(get_xml_format())
        attributes = root.attrib
        print(attributes)
        print(list(root))
        print(etree.tostring(root, pretty_print=True))
