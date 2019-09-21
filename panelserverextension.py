from subprocess import Popen

def load_jupyter_server_extension(nbapp):
    """serve the notebook with bokeh server"""
    Popen(["panel", "serve", "1_panel_bokeh_dashboard.ipynb", "--allow-websocket-origin=*"])
