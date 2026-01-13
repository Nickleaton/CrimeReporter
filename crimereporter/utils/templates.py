from jinja2 import Environment, FileSystemLoader, select_autoescape

# Create the environment once
env = Environment(
    loader=FileSystemLoader("templates"),
    autoescape=select_autoescape(["html", "xml"]),
    cache_size=0,
)
