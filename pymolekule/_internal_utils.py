"""
pymolekule._internal_utils
~~~~~~~~~~~~~~
Provides utility functions that are consumed internally by PyMolekule
"""

import re
import hmac
import hashlib
from datetime import datetime
from urllib.parse import urlparse

import requests


def make_signature(key, msg):
    return hmac.new(key, msg.encode("utf-8"), hashlib.sha256).digest()


def get_signature_key(key, date_stamp, regionName, serviceName):
    kDate = make_signature(('AWS4' + key).encode('utf-8'), date_stamp)
    kRegion = make_signature(kDate, regionName)
    kService = make_signature(kRegion, serviceName)
    kSigning = make_signature(kService, 'aws4_request')
    return kSigning


def stealth_email(email: str = None):
    if email:
        pattern = r"(?!^|.$)[^@]"
        s = re.search(pattern, email)
        if s:
            return re.sub(pattern, '*', email)
    return None


def extract_region(identity_id: str = None):
    if identity_id:
        pattern = r"^[^:]+"
        s = re.search(pattern, identity_id)
        if s:
            return s.group(0)
    return None


def make_configuration(endpoint: str, security_token: str, aws_access_key_id: str, aws_secret_key: str, goal_region: str, lang: str = 'fr'):
    now = datetime.utcnow()
    amzdate = now.strftime('%Y%m%dT%H%M%SZ')
    datestamp = now.strftime('%Y%m%d')

    # ************* TASK 1: CREATE A CANONICAL REQUEST *************
    # http://docs.aws.amazon.com/general/latest/gr/sigv4-create-canonical-request.html

    method = 'GET'
    service = 'execute-api'
    parsed_endpoint = urlparse(endpoint)
    host = parsed_endpoint.netloc
    contentType = 'application/json'
    request_parameters = f'country={lang}'

    canonical_uri = '/'

    canonical_querystring = request_parameters

    payload_hash = hashlib.sha256(('').encode('utf-8')).hexdigest()

    canonical_headers = 'content-type:' + contentType + '\n' + 'host:' + host + '\n' + 'x-amz-content-sha256:' + \
        payload_hash + '\n' + 'x-amz-date:' + amzdate + '\n' + \
        'x-amz-security-token:' + security_token + '\n'

    signed_headers = 'content-type;host;x-amz-content-sha256;x-amz-date;x-amz-security-token'

    canonical_request = method + '\n' + canonical_uri + '\n' + canonical_querystring + \
        '\n' + canonical_headers + '\n' + signed_headers + '\n' + payload_hash

    # ************* TASK 2: CREATE THE STRING TO SIGN*************
    algorithm = 'AWS4-HMAC-SHA256'
    credential_scope = datestamp + '/' + goal_region + \
        '/' + service + '/' + 'aws4_request'
    string_to_sign = algorithm + '\n' + amzdate + '\n' + credential_scope + \
        '\n' + \
        hashlib.sha256(canonical_request.encode('utf-8')).hexdigest()

    # ************* TASK 3: CALCULATE THE SIGNATURE *************
    # Create the signing key using the function defined above.
    signing_key = get_signature_key(
        aws_secret_key, datestamp, goal_region, service)

    # Sign the string_to_sign using the signing_key
    signature = hmac.new(signing_key, (string_to_sign).encode(
        'utf-8'), hashlib.sha256).hexdigest()

    # ************* TASK 4: ADD SIGNING INFORMATION TO THE REQUEST *************
    authorization_header = algorithm + ' ' + 'Credential=' + aws_access_key_id + '/' + \
        credential_scope + ', ' + 'SignedHeaders=' + \
        signed_headers + ', ' + 'Signature=' + signature

    headers = {'x-amz-date': amzdate,
               'Authorization': authorization_header, 'Content-Type': contentType, 'x-amz-security-token': security_token, 'x-amz-content-sha256': payload_hash}

    return requests.get(endpoint + '?' + canonical_querystring, headers=headers)


def create_access(endpoint: str, security_token: str, aws_access_key_id: str, aws_secret_key: str, goal_region: str, amzn_iot: str):
    # Create a date for headers and the credential string
    now = datetime.utcnow()
    amzdate = now.strftime('%Y%m%dT%H%M%SZ')
    # Date w/o time, used in credential scope
    datestamp = now.strftime('%Y%m%d')

    # ************* TASK 1: CREATE A CANONICAL REQUEST *************
    # http://docs.aws.amazon.com/general/latest/gr/sigv4-create-canonical-request.html

    method = 'PUT'
    service = 'execute-api'
    parsed_endpoint = urlparse(endpoint)
    host = parsed_endpoint.netloc
    contentType = 'application/x-amz-json-1.0'
    user_agent = 'aws-sdk-iOS/2.12.1 iOS/15.4.1 en_FR'

    payload_hash = hashlib.sha256(('{}').encode('utf-8')).hexdigest()

    canonical_headers = 'content-type:' + contentType + '\n' + \
        'host:' + host + '\n' + \
        'user-agent:' + user_agent + '\n' + \
        'x-amz-date:' + amzdate + '\n' + \
        'x-amz-security-token:' + security_token + '\n' + \
        'x-amzn-iot-principal:' + amzn_iot + '\n'

    signed_headers = 'content-type;host;user-agent;x-amz-date;x-amz-security-token;x-amzn-iot-principal'

    canonical_request = method + '\n' + parsed_endpoint.path + '\n\n' + \
        canonical_headers + '\n' + signed_headers + '\n' + payload_hash

    # ************* TASK 2: CREATE THE STRING TO SIGN*************
    algorithm = 'AWS4-HMAC-SHA256'
    credential_scope = datestamp + '/' + goal_region + \
        '/' + service + '/' + 'aws4_request'
    string_to_sign = algorithm + '\n' + amzdate + '\n' + credential_scope + \
        '\n' + \
        hashlib.sha256(canonical_request.encode('utf-8')).hexdigest()

    # ************* TASK 3: CALCULATE THE SIGNATURE *************
    # Create the signing key using the function defined above.
    signing_key = get_signature_key(
        aws_secret_key, datestamp, goal_region, service)

    # Sign the string_to_sign using the signing_key
    signature = hmac.new(signing_key, (string_to_sign).encode(
        'utf-8'), hashlib.sha256).hexdigest()

    # ************* TASK 4: ADD SIGNING INFORMATION TO THE REQUEST *************
    authorization_header = algorithm + ' ' + 'Credential=' + aws_access_key_id + '/' + \
        credential_scope + ', ' + 'SignedHeaders=' + \
        signed_headers + ', ' + 'Signature=' + signature

    headers = {'x-amz-date': amzdate,
               'Authorization': authorization_header,
               'Content-Type': contentType,
               'x-amz-security-token': security_token,
               'x-amz-content-sha256': payload_hash,
               'x-amzn-iot-principal': amzn_iot,
               'User-Agent': user_agent}

    return requests.put(endpoint, headers=headers, json={})
