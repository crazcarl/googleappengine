from handlers.base import AppHandler


class CSSHandler(AppHandler):
    def get(self, css_name):
        css_dir = os.path.join(os.path.dirname(__file__), 'css')
		
        with open(os.path.join(css_dir, css_name)) as css_file:
            self.response.headers['Content-Type'] = 'text/css'
            self.response.out.write(css_file.read())