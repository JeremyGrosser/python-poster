# -*- coding: utf-8 -*-
from unittest import TestCase
import mimetypes
import poster.encode
import StringIO

def unix2dos(s):
    return s.replace("\n", "\r\n")

class TestEncode_String(TestCase):
    def test_simple(self):
        expected = unix2dos("""--XXXXXXXXX
Content-Disposition: form-data; name="foo"
Content-Type: text/plain; charset=utf-8
Content-Length: 3

bar
""")
        self.assertEqual(expected,
                poster.encode.encode_string("XXXXXXXXX", "foo", "bar"))

    def test_quote_name(self):
        expected = unix2dos("""--XXXXXXXXX
Content-Disposition: form-data; name="foo+baz"
Content-Type: text/plain; charset=utf-8
Content-Length: 3

bar
""")
        self.assertEqual(expected,
                poster.encode.encode_string("XXXXXXXXX", "foo baz", "bar"))

    def test_quote_value(self):
        expected = unix2dos("""--XXXXXXXXX
Content-Disposition: form-data; name="foo"
Content-Type: text/plain; charset=utf-8
Content-Length: 11

bar baz@bat
""")
        self.assertEqual(expected,
                poster.encode.encode_string("XXXXXXXXX", "foo", "bar baz@bat"))

    def test_boundary(self):
        expected = unix2dos("""--ABC+DEF
Content-Disposition: form-data; name="foo"
Content-Type: text/plain; charset=utf-8
Content-Length: 3

bar
""")
        self.assertEqual(expected,
                poster.encode.encode_string("ABC DEF", "foo", "bar"))

    def test_unicode(self):
        expected = unix2dos("""--XXXXXXXXX
Content-Disposition: form-data; name="foo"
Content-Type: text/plain; charset=utf-8
Content-Length: 4

b\xc3\xa1r
""")
        self.assertEqual(expected,
                poster.encode.encode_string("XXXXXXXXX", "foo", u"bár"))


class TestEncode_File(TestCase):
    def test_simple(self):
        expected = unix2dos("""--XXXXXXXXX
Content-Disposition: form-data; name="foo"
Content-Type: text/plain; charset=utf-8
Content-Length: 42

""")
        self.assertEqual(expected,
                poster.encode.encode_file_header("XXXXXXXXX", "foo", 42))

    def test_content_type(self):
        expected = unix2dos("""--XXXXXXXXX
Content-Disposition: form-data; name="foo"
Content-Type: text/html
Content-Length: 42

""")
        self.assertEqual(expected,
                poster.encode.encode_file_header("XXXXXXXXX", "foo", 42, filetype="text/html"))

    def test_filename_simple(self):
        expected = unix2dos("""--XXXXXXXXX
Content-Disposition: form-data; name="foo"; filename="test.txt"
Content-Type: text/plain; charset=utf-8
Content-Length: 42

""")
        self.assertEqual(expected,
                poster.encode.encode_file_header("XXXXXXXXX", "foo", 42,
                    "test.txt"))

    def test_quote_filename(self):
        expected = unix2dos("""--XXXXXXXXX
Content-Disposition: form-data; name="foo"; filename="test file.txt"
Content-Type: text/plain; charset=utf-8
Content-Length: 42

""")
        self.assertEqual(expected,
                poster.encode.encode_file_header("XXXXXXXXX", "foo", 42,
                    "test file.txt"))

        expected = unix2dos("""--XXXXXXXXX
Content-Disposition: form-data; name="foo"; filename="test\\"file.txt"
Content-Type: text/plain; charset=utf-8
Content-Length: 42

""")
        self.assertEqual(expected,
                poster.encode.encode_file_header("XXXXXXXXX", "foo", 42,
                    "test\"file.txt"))

    def test_unicode_filename(self):
        expected = unix2dos("""--XXXXXXXXX
Content-Disposition: form-data; name="foo"; filename="&#9731;.txt"
Content-Type: text/plain; charset=utf-8
Content-Length: 42

""")
        self.assertEqual(expected,
                poster.encode.encode_file_header("XXXXXXXXX", "foo", 42,
                    u"\N{SNOWMAN}.txt"))

class TestEncodeAndQuote(TestCase):
    def test(self):
        self.assertEqual("foo+bar", poster.encode.encode_and_quote("foo bar"))
        self.assertEqual("foo%40bar", poster.encode.encode_and_quote("foo@bar"))
        self.assertEqual("%28%C2%A9%29+2008",
                poster.encode.encode_and_quote(u"(©) 2008"))

class TestMultiparam(TestCase):
    def test_from_params(self):
        fp = open("tests/test_encode.py")
        expected = [poster.encode.MultipartParam("foo", "bar"),
                    poster.encode.MultipartParam("baz", fileobj=fp,
                        filename=fp.name,
                        filetype=mimetypes.guess_type(fp.name)[0])]

        self.assertEqual(poster.encode.MultipartParam.from_params(
            [("foo", "bar"), ("baz", fp)]), expected)

        self.assertEqual(poster.encode.MultipartParam.from_params(
            (("foo", "bar"), ("baz", fp))), expected)

        self.assertEqual(poster.encode.MultipartParam.from_params(
            {"foo": "bar", "baz": fp}), expected)

        self.assertEqual(poster.encode.MultipartParam.from_params(
            [expected[0], expected[1]]), expected)

    def test_simple(self):
        p = poster.encode.MultipartParam("foo", "bar")
        boundary = "XYZXYZXYZ"
        expected = unix2dos("""--XYZXYZXYZ
Content-Disposition: form-data; name="foo"
Content-Type: text/plain; charset=utf-8
Content-Length: 3

bar
--XYZXYZXYZ--
""")
        self.assertEqual(p.encode(boundary), expected[:-len(boundary)-6])
        self.assertEqual(p.get_size(boundary), len(expected)-len(boundary)-6)
        self.assertEqual(poster.encode.get_body_size([p], boundary),
                len(expected))
        self.assertEqual(poster.encode.get_headers([p], boundary),
                {'Content-Length': len(expected),
                 'Content-Type': 'multipart/form-data; boundary=%s' % boundary})

        datagen, headers = poster.encode.multipart_encode([p], boundary)
        self.assertEqual(headers, {'Content-Length': len(expected),
                 'Content-Type': 'multipart/form-data; boundary=%s' % boundary})
        self.assertEqual("".join(datagen), expected)

    def test_multiple_leys(self):
        params = poster.encode.MultipartParam.from_params(
                [("key", "value1"), ("key", "value2")])
        boundary = "XYZXYZXYZ"
        datagen, headers = poster.encode.multipart_encode(params, boundary)
        encoded = "".join(datagen)

        expected = unix2dos("""--XYZXYZXYZ
Content-Disposition: form-data; name="key"
Content-Type: text/plain; charset=utf-8
Content-Length: 6

value1
--XYZXYZXYZ
Content-Disposition: form-data; name="key"
Content-Type: text/plain; charset=utf-8
Content-Length: 6

value2
--XYZXYZXYZ--
""")
        self.assertEqual(encoded, expected)


    def test_stringio(self):
        fp = StringIO.StringIO("file data")
        params = poster.encode.MultipartParam.from_params( [("foo", fp)] )
        boundary = "XYZXYZXYZ"
        datagen, headers = poster.encode.multipart_encode(params, boundary)
        encoded = "".join(datagen)

        expected = unix2dos("""--XYZXYZXYZ
Content-Disposition: form-data; name="foo"
Content-Type: text/plain; charset=utf-8
Content-Length: 9

file data
--XYZXYZXYZ--
""")
        self.assertEqual(encoded, expected)
