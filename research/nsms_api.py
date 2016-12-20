#! /usr/bin/env python
# -*- coding: utf-8 -*-

from flask import Flask, request, jsonify, make_response, Response, abort
from flask_restful import Resource, Api
from flask_httpauth import HTTPBasicAuth
import thriftpy
import thriftpy.protocol.json as proto
from pymongo import MongoClient
from bson import json_util
import scrypt
import os

nsms_thrift = thriftpy.load('nsms_api_1_0.thrift',
                            module_name='nsms_api_thrift')

api_url = '/nsms/api/v1.0'
app = Flask(__name__)
api = Api(app)
auth = HTTPBasicAuth()
client = MongoClient('mongodb://localhost:27017/')
db = client['nsms-api-db']
companies = db.companies
users = db.users


@auth.error_handler
def unauthorized():
    return make_response(jsonify({'error': 'Unauthorized access'}), 401)


def get_hash(salt, username, password):
    pass_hash = scrypt.hash(username, salt)
    return scrypt.encrypt(pass_hash, password, maxtime=0.5)


@auth.verify_password
def verify_pw(username, password):
    company = companies.find_one({'company_name':
                                  request.view_args['company_name']})
    try:
        user = next(x for x in company['users'] if x['login_name'] == username)
        scrypt.decrypt(user['password_hash'], password,
                       maxtime=0.5, encoding=None)
    except StopIteration:
        return False
    except scrypt.error:
        return False

    return True


def create_user_info(u, base_url=None, url=None):
    if url is not None:
        out_url = url
    elif base_url is not None:
        out_url = base_url+'/users/'+u['login_name']
    else:
        raise ValueError

    new_user = nsms_thrift.User()
    for i in (k for k in u.keys() if k in new_user.__dict__.keys()):
        new_user.__dict__[i] = u[i]
    new_user.url = out_url

    return new_user


class Company(Resource):
    @auth.login_required
    def get(self, company_name):
        company = companies.find_one({'company_name': company_name})
        username = request.authorization.username
        user = next(x for x in company['users'] if x['login_name'] == username)
        if not user['admin']:
            abort(401)
        if company is not None:
            company_info = nsms_thrift.GetCompanyResponse
            company_info.company_name = company_name
            company_info.subscription_plan = company['plan']
            company_info.users = [create_user_info(u, request.base_url)
                                  for u in company['users']]
            return jsonify(proto.struct_to_json(company_info))
        else:
            return None


class User(Resource):
    @auth.login_required
    def get(self, company_name, user_name):
        company = companies.find_one({'company_name': company_name})
        try:
            user = next(x for x in company['users'] if x['login_name'] == user_name)
        except StopIteration:
            return None
        user_info = create_user_info(user, url=request.url)
        return jsonify(proto.struct_to_json(user_info))

    @auth.login_required
    def put(self, company_name, user_name):
        company = companies.find_one({'company_name': company_name})
        try:
            user = next(x for x in company['users'] if x['login_name'] == user_name)
        except StopIteration:
            return None

        return jsonify({})

api.add_resource(Company,
                 api_url+'/org/<string:company_name>')
api.add_resource(User,
                 api_url+'/org/<string:company_name>/users/<string:user_name>')


@app.route(api_url+'/org', methods=['GET'])
def get_orgs():
    return Response(response=json_util.dumps(companies.find()),
                    content_type='application/json')


@app.route(api_url+'/org', methods=['POST'])
def register_new_company():
    reg_info = nsms_thrift.RegisterRequest()
    proto.struct_to_obj(request.get_json(), reg_info)

    # TODO: validate request

    reg_answer = nsms_thrift.RegisterResponse()
    if companies.find_one({'company_name': reg_info.company_name}):
        reg_answer.result = 'error'
        reg_answer.error_description = 'already registered'
        return jsonify(proto.struct_to_json(reg_answer))

    user_salt = os.urandom(64)
    company_secret = os.urandom(32)
    companies.insert_one({
        'company_name': reg_info.company_name,
        'plan': reg_info.subscription_plan,
        'company_secret': company_secret,
        'users': [
            {
                'login_name': reg_info.admin_name,
                'full_name': reg_info.admin_fullname,
                'password_hash': get_hash(user_salt,
                                          reg_info.admin_name,
                                          reg_info.admin_password),
                'password_salt': user_salt,
                'admin': True,
                'email': reg_info.admin_email,
            }
        ]
    })

    reg_answer.result = 'ok'
    reg_answer.company_info = nsms_thrift.CompanyInfo(reg_info.company_name,
                                                      company_secret)
    return jsonify(proto.struct_to_json(reg_answer))


if __name__ == '__main__':
    app.run(debug=True, host='192.168.56.101')
