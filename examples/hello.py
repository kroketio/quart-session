# -*- coding: utf-8 -*-
"""
    Hello
    ~~~~~

    Quart-Session demo.

    :copyright: (c) 2020 by dsc.
    :license: BSD, see LICENSE for more details.
"""
from quart import Quart, session
from quart_session import Session


SESSION_TYPE = 'redis'


app = Quart(__name__)
app.config.from_object(__name__)
Session(app)


@app.route('/set/')
def set():
    session['key'] = 'value'
    return 'ok'


@app.route('/get/')
def get():
    return session.get('key', 'not set')


if __name__ == "__main__":
    app.run(debug=True)
