#! /usr/bin/env python
# vim: set fileencoding=utf-8 :
# -*- coding: utf-8 -*-

from flask import Flask, request, jsonify, make_response, Response, abort, render_template_string
from flask_restful import Resource, Api
from flask_httpauth import HTTPTokenAuth
#from ldap3 import utils
import base64


class HTTPNTLMAuth(HTTPTokenAuth):
    token = ''

    def __init__(self, scheme='NTLM', realm=None):
        super(HTTPNTLMAuth, self).__init__(scheme, realm)

        self.verify_token_callback = None

    def verify_token(self, f):
        self.verify_token_callback = f
        return f

    def authenticate(self, auth, stored_password):
        if auth:
            token = auth['token']
        else:
            token = ""
        if self.verify_token_callback:
            return self.verify_token_callback(token)
        return False

    def authenticate_header(self):
        return '{0}'.format(self.scheme)

api_url = '/roc/api/v1'
app = Flask(__name__)
api = Api(app)
auth = HTTPNTLMAuth()


@auth.error_handler
def unauthorized():
    response = make_response(render_template_string('<html><body>authentication required</body></html>'), 401)
    return response


@auth.verify_token
def verify_token(token):
    if token != '':
        auth.token = token
        return True
    return False


@app.route(api_url+'/me', methods=['GET'])
@auth.login_required
def get_me_info():
    str = base64.b64decode(auth.token)
    return render_template_string('<html><body><b>your token:</b> {}<br/><b>decoded:</b> {}</body></html>'.format(auth.token, str))


class Company(Resource):
    @auth.login_required
    def get(self, company_id):
        return company_id


if __name__ == '__main__':
    api.add_resource(Company, api_url + 'company/<string:company_name>')
    app.run(debug=True, host='192.168.56.102', port=8888)