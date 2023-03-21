import requests
from flask import (
  Flask,
  jsonify as flask_jsonify,
  request,
  Response
)
from werkzeug.datastructures import MultiDict
from helpers import (
  get_dict,
  status_code
)
from utils import weighted_choice

app = Flask(__name__)

def jsonify(*args, **kwargs):
    response = flask_jsonify(*args, **kwargs)
    if not response.data.endswith(b"\n"):
        response.data += b"\n"
    return response

@app.route("/")
def python_echo():
    return "<p>Python Echo!</p>"

@app.route("/headers")
def view_headers():
    """Return the incoming request's HTTP headers.
    ---
    tags:
      - Request inspection
    produces:
      - application/json
    responses:
      200:
        description: The request's headers.
    """

    return jsonify(get_dict('headers'))

@app.route("/get", methods=("GET",))
def view_get():
    """The request's query parameters.
    ---
    tags:
      - HTTP Methods
    produces:
      - application/json
    responses:
      200:
        description: The request's query parameters.
    """

    return jsonify(get_dict("url", "args", "headers", "origin"))

@app.route("/post", methods=("POST",))
def view_post():
    """The request's POST parameters.
    ---
    tags:
      - HTTP Methods
    produces:
      - application/json
    responses:
      200:
        description: The request's POST parameters.
    """

    return jsonify(
        get_dict("url", "args", "form", "data", "origin", "headers", "files", "json")
    )

@app.route("/put", methods=("PUT",))
def view_put():
    """The request's PUT parameters.
    ---
    tags:
      - HTTP Methods
    produces:
      - application/json
    responses:
      200:
        description: The request's PUT parameters.
    """

    return jsonify(
        get_dict("url", "args", "form", "data", "origin", "headers", "files", "json")
    )

@app.route(
    "/status/<codes>", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "TRACE"]
)
def view_status_code(codes):
    """Return status code or random status code if more than one are given
    ---
    tags:
      - Status codes
    parameters:
      - in: path
        name: codes
    produces:
      - text/plain
    responses:
      100:
        description: Informational responses
      200:
        description: Success
      300:
        description: Redirection
      400:
        description: Client Errors
      500:
        description: Server Errors
    """

    if "," not in codes:
        try:
            code = int(codes)
        except ValueError:
            return Response("Invalid status code", status=400)
        return status_code(code)

    choices = []
    for choice in codes.split(","):
        if ":" not in choice:
            code = choice
            weight = 1
        else:
            code, weight = choice.split(":")

        try:
            choices.append((int(code), float(weight)))
        except ValueError:
            return Response("Invalid status code", status=400)

    code = weighted_choice(choices)

    return status_code(code)

@app.route("/response-headers", methods=["GET", "POST"])
def response_headers():
    """Returns a set of response headers from the query string.
    ---
    tags:
      - Response inspection
    parameters:
      - in: query
        name: freeform
        explode: true
        allowEmptyValue: true
        schema:
          type: object
          additionalProperties:
            type: string
        style: form
    produces:
      - application/json
    responses:
      200:
        description: Response headers
    """
    # Pending swaggerUI update
    # https://github.com/swagger-api/swagger-ui/issues/3850
    headers = MultiDict(request.args.items(multi=True))
    response = jsonify(list(headers.lists()))

    while True:
        original_data = response.data
        d = {}
        for key in response.headers.keys():
            value = response.headers.get_all(key)
            if len(value) == 1:
                value = value[0]
            d[key] = value
        response = jsonify(d)
        for key, value in headers.items(multi=True):
            response.headers.add(key, value)
        response_has_changed = response.data != original_data
        if not response_has_changed:
            break
    return response


@app.route("/external", methods=["GET"])
def external_call():
  # Make sure to keep the URL Updates
  json = requests.get('https://api.jsonbin.io/v3/qs/641989e0c0e7653a058bc04d')
  return {"data":json.json()}