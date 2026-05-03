from jinja2 import Template, Environment

env = Environment()
t = env.from_string("""
{% macro inner(a, b=2, c=3) %}{{ a }} {{ b }} {{ c }}{% endmacro %}
{% macro outer() %}{{ inner(*varargs, **kwargs) }}{% endmacro %}
{{ outer(1, b=5, c=6) }}
""")
print(t.render())
