from flask import jsonify

class APIResponse:
    @staticmethod
    def respond(data=None, status=200, headers=None):
        return jsonify({"data": data}), status, headers

    @staticmethod
    def error(message, status=400, error='BadRequest'):
        return jsonify({"message": message, "error": error}), status