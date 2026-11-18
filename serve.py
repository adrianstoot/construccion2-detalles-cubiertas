"""
Local development server for d:\C2 with strict ES module, GLTF/CAD MIME types, and HTTP Range support for MP4 video.
"""
import functools
import http.server
import os
import re
import socketserver


class ArchitecturalHandler(http.server.SimpleHTTPRequestHandler):
    extensions_map = {
        **http.server.SimpleHTTPRequestHandler.extensions_map,
        ".js": "application/javascript; charset=utf-8",
        ".mjs": "application/javascript; charset=utf-8",
        ".css": "text/css; charset=utf-8",
        ".html": "text/html; charset=utf-8",
        ".json": "application/json; charset=utf-8",
        ".svg": "image/svg+xml",
        ".glb": "model/gltf-binary",
        ".gltf": "model/gltf+json",
        ".pdf": "application/pdf",
        ".dxf": "application/dxf",
        ".blend": "application/octet-stream",
        ".png": "image/png",
        ".mp4": "video/mp4",
    }

    def end_headers(self):
        self.send_header("Accept-Ranges", "bytes")
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def send_head(self):
        path = self.translate_path(self.path)
        if os.path.isfile(path) and "Range" in self.headers:
            ctype = self.guess_type(path)
            size = os.path.getsize(path)
            m = re.match(r"bytes=(\d*)-(\d*)", self.headers.get("Range", ""))
            if m:
                start = int(m.group(1)) if m.group(1) else 0
                end = int(m.group(2)) if m.group(2) else size - 1
                end = min(end, size - 1)
                if 0 <= start <= end < size:
                    f = open(path, "rb")
                    f.seek(start)
                    self.send_response(206)
                    self.send_header("Content-Type", ctype)
                    self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
                    self.send_header("Content-Length", str(end - start + 1))
                    self.end_headers()
                    self._range_file = (f, end - start + 1)
                    return f
        self._range_file = None
        return super().send_head()

    def copyfile(self, source, outputfile):
        if getattr(self, "_range_file", None):
            f, remaining = self._range_file
            bufsize = 64 * 1024
            while remaining > 0:
                chunk = f.read(min(bufsize, remaining))
                if not chunk:
                    break
                outputfile.write(chunk)
                remaining -= len(chunk)
        else:
            super().copyfile(source, outputfile)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8080"))
    handler = functools.partial(ArchitecturalHandler, directory=r"d:\C2")
    socketserver.ThreadingTCPServer.allow_reuse_address = True
    with socketserver.ThreadingTCPServer(("127.0.0.1", port), handler) as httpd:
        print(f"Serving d:\\C2 at http://127.0.0.1:{port}/", flush=True)
        httpd.serve_forever()
