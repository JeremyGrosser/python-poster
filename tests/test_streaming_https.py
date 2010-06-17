# -*- coding: utf-8 -*-
from unittest import TestCase
import poster
import webob
from paste import httpserver
import urllib2
import threading, time
import sys

from OpenSSL import SSL

poster.streaminghttp.register_openers()

port = 5124

request = None
params = None

def app(environ, start_response):
    global params, request
    start_response("200 OK", [("Content-Type", "text/plain")])
    request = webob.Request(environ)
    # We need to look at the request's parameters to force webob
    # to consume the POST body
    # The cat is alive
    params = request.params
    return "OK"

class TestStreaming(TestCase):
    def setUp(self):
        self.server = httpserver.serve(app, port=port, ssl_pem="*", start_loop=False)
        self.server_thread = threading.Thread(target = self.server.handle_request)
        self.server_thread.start()
        self._opened = True

    def tearDown(self):
        if not self._opened:
            self._open("/foo")
        self.server.server_close()
        self.server_thread.join()

    def _open(self, url, params=None, headers=None):
        if headers is None:
            headers = {}
        req = urllib2.Request("https://localhost:%i/%s" % (port, url), params,
                headers)
        return urllib2.urlopen(req)

    def test_basic(self):
        response = self._open("testing123")

        self.assertEqual(response.read(), "OK")
        self.assertEqual(request.path, "/testing123")

        response.close()

    def test_basic2(self):
        response = self._open("testing?foo=bar")

        self.assertEqual(response.read(), "OK")
        self.assertEqual(request.path, "/testing")
        self.assertEqual(params.get("foo"), "bar")

        response.close()

    def test_nonstream_uploadfile(self):
        datagen, headers = poster.encode.multipart_encode([
            poster.encode.MultipartParam.from_file("file", __file__),
            poster.encode.MultipartParam("foo", "bar")])

        data = "".join(datagen)

        response = self._open("upload", data, headers)
        self.assertEqual(params.get("file").file.read(),
                open(__file__).read())
        self.assertEqual(params.get("foo"), "bar")

    def test_stream_uploadfile(self):
        datagen, headers = poster.encode.multipart_encode([
            poster.encode.MultipartParam.from_file("file", __file__),
            poster.encode.MultipartParam("foo", "bar")])

        response = self._open("upload", datagen, headers)
        self.assertEqual(params.get("file").file.read(),
                open(__file__).read())
        self.assertEqual(params.get("foo"), "bar")

    def test_stream_upload_generator_no_len(self):
        def data():
            yield ""

        self.assertRaises(ValueError, self._open, "upload", data(), {})
