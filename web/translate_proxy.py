"""
极简翻译代理 - 本地运行，转发请求到腾讯云 TMT API
启动方式: python translate_proxy.py
监听地址: http://127.0.0.1:8765
"""
import json
import http.server
import urllib.request

PORT = 8765
TARGET = 'https://tmt.tencentcloudapi.com'


class ProxyHandler(http.server.BaseHTTPRequestHandler):

    def do_OPTIONS(self):
        self.send_response(200)
        self._cors()
        self.end_headers()

    def do_POST(self):
        length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(length)

        req = urllib.request.Request(TARGET, data=body, method='POST')

        # 原样转发 TC3 签名所需的全部 Header
        for h in ('Content-Type', 'X-TC-Action', 'X-TC-Version',
                  'X-TC-Timestamp', 'X-TC-Region', 'Authorization'):
            v = self.headers.get(h)
            if v:
                req.add_header(h, v)

        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = resp.read()
                self.send_response(resp.status)
                self._cors()
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.end_headers()
                self.wfile.write(data)
        except urllib.error.HTTPError as e:
            # 腾讯云 API 即使出错也返回 JSON body，原样透传
            err_body = e.read()
            self.send_response(e.code)
            self._cors()
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.end_headers()
            self.wfile.write(err_body)
        except Exception as e:
            self.send_response(502)
            self._cors()
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.end_headers()
            self.wfile.write(json.dumps({
                'Response': {'Error': {'Code': 'ProxyError', 'Message': str(e)}}
            }).encode('utf-8'))

    def _cors(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', '*')

    def log_message(self, fmt, *args):
        print('[%s]' % self.log_date_time_string(), fmt % args)


if __name__ == '__main__':
    print(f'翻译代理已启动 → http://127.0.0.1:{PORT}')
    print('按 Ctrl+C 停止')
    http.server.HTTPServer(('127.0.0.1', PORT), ProxyHandler).serve_forever()
