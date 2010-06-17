# -*- coding: utf-8 -*-
from unittest import TestCase
import httplib
import poster
import webob
from paste import httpserver
import urllib2, urllib
import threading, time
import sys
import os

poster.streaminghttp.register_openers()

port = 5123

class TestStreaming(TestCase):
    def setUp(self):
        # Disable HTTPS support for these tests to excercise the non-https code
        # HTTPS is tested in test_streaming_https.py
        if hasattr(httplib, "HTTPS"):
            self.https = getattr(httplib, "HTTPS")
            delattr(httplib, "HTTPS")
            reload(poster.streaminghttp)
        else:
            self.https = None

        self.request = None
        self._opened = True

        def app(environ, start_response):
            self.request = webob.Request(environ)
            if self.request.path == '/redirect':
                start_response("301 MOVED", [("Location", "/foo")])
                self.params = self.request.params
                # Start up another thread to handle things
                self.server_thread.join()
                self.server_thread = threading.Thread(target = self.server.handle_request)
                self.server_thread.start()
                return ""

            start_response("200 OK", [("Content-Type", "text/plain")])
            # We need to look at the request's parameters to force webob
            # to consume the POST body
            # The cat is alive
            self.params = self.request.params
            return "OK"

        self.server = httpserver.WSGIServer(app, ("localhost", port), httpserver.WSGIHandler)

        self.server_thread = threading.Thread(target = self.server.handle_request)
        self.server_thread.start()

    def tearDown(self):
        if self.https:
            setattr(httplib, "HTTPS", self.https)
        if not self._opened:
            self._open("/foo")
        self.server.server_close()
        self.server_thread.join()

    def _open(self, url, params=None, headers=None):
        try:
            if headers is None:
                headers = {}
            req = urllib2.Request("http://localhost:%i/%s" % (port, url), params,
                    headers)
            return urllib2.urlopen(req)
        except:
            self._opened = False
            raise

    def test_basic(self):
        response = self._open("testing123")

        self.assertEqual(response.read(), "OK")
        self.assertEqual(self.request.path, "/testing123")

    def test_basic2(self):
        response = self._open("testing?foo=bar")

        self.assertEqual(response.read(), "OK")
        self.assertEqual(self.request.path, "/testing")
        self.assertEqual(self.params.get("foo"), "bar")

    def test_nonstream_uploadfile(self):
        datagen, headers = poster.encode.multipart_encode([
            poster.encode.MultipartParam.from_file("file", __file__),
            poster.encode.MultipartParam("foo", "bar")])

        data = "".join(datagen)

        response = self._open("upload", data, headers)
        self.assertEqual(self.params.get("file").file.read(),
                open(__file__).read())
        self.assertEqual(self.params.get("foo"), "bar")

    def test_stream_upload_generator(self):
        datagen, headers = poster.encode.multipart_encode([
            poster.encode.MultipartParam.from_file("file", __file__),
            poster.encode.MultipartParam("foo", "bar")])

        response = self._open("upload", datagen, headers)
        self.assertEqual(self.params.get("file").file.read(),
                open(__file__).read())
        self.assertEqual(self.params.get("foo"), "bar")

    def test_stream_upload_file(self):
        data = open("poster/__init__.py")
        headers = {"Content-Length": os.path.getsize("poster/__init__.py")}

        response = self._open("upload", data, headers)

        request_body = self.request.body_file.read()
        request_body = urllib.unquote_plus(request_body)
        data = open("poster/__init__.py").read()
        self.assertEquals(request_body, data)

    def test_stream_upload_file_no_len(self):
        data = open(__file__)
        self.assertRaises(ValueError, self._open, "upload", data, {})

    def test_stream_upload_generator_no_len(self):
        def data():
            yield ""

        self.assertRaises(ValueError, self._open, "upload", data(), {})

    def test_redirect(self):
        response = self._open("redirect")

        self.assertEqual(response.read(), "OK")
        self.assertEqual(self.request.path, "/foo")
