#!/usr/bin/env python3

from models import db, Activity, Camper, Signup
from flask_restful import Api, Resource
from flask_migrate import Migrate
from flask import Flask, make_response, jsonify, request
import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE = os.environ.get("DB_URI", f"sqlite:///{os.path.join(BASE_DIR, 'app.db')}")


app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.json.compact = False

migrate = Migrate(app, db)

db.init_app(app)
api = Api(app)


@app.route("/")
def home():
    return ""


class Campers(Resource):
    def get(self):
        campers = Camper.query.all()
        camper_dict = [
            camper.to_dict(rules=("-signups", "-activities")) for camper in campers
        ]
        return make_response(camper_dict, 200)

    def post(self):
        camper_json = request.get_json()
        camper = Camper()
        try:
            for key in camper_json:
                if hasattr(camper, key):
                    setattr(camper, key, camper_json[key])
            db.session.add(camper)
            db.session.commit()
            return make_response(camper.to_dict(rules=("-signups", "-activities")), 200)
        except ValueError:
            return make_response({"errors": ["validation errors"]}, 400)


class CamperById(Resource):
    def get(self, id):
        camper = db.session.get(Camper, id)
        if camper:
            return make_response(
                camper.to_dict(
                    rules=(
                        "-activities",
                        "-signups.activity.signups",
                        "-signups.camper",
                    )
                ),
                200,
            )
        return make_response({"error": "Camper not found"}, 404)

    def patch(self, id):
        camper = db.session.get(Camper, id)
        if camper:
            try:
                camper_json = request.get_json()
                for key in camper_json:
                    if hasattr(camper, key):
                        setattr(camper, key, camper_json[key])
                db.session.commit()
                return make_response(
                    camper.to_dict(rules=("-signups", "-activities")), 202
                )
            except ValueError:
                return make_response({"errors": ["validation errors"]}, 400)
        return make_response({"error": "Camper not found"}, 404)


class Activities(Resource):
    def get(self):
        activities = Activity.query.all()
        activities_dict = [
            activity.to_dict(rules=("-signups", "-campers")) for activity in activities
        ]
        return make_response(activities_dict, 200)


class ActivityById(Resource):
    def delete(self, id):
        activity = db.session.get(Activity, id)
        if activity:
            db.session.delete(activity)
            db.session.commit()
            return make_response("", 204)
        return make_response({"error": "Activity not found"}, 404)


class Signups(Resource):
    def post(self):
        signup_json = request.get_json()
        signup = Signup()
        try:
            for key in signup_json:
                if hasattr(signup, key):
                    setattr(signup, key, signup_json[key])
            db.session.add(signup)
            db.session.commit()
            return make_response(
                signup.to_dict(rules=("-activity.signups", "-camper.signups")), 200
            )
        except ValueError:
            return make_response({"errors": ["validation errors"]}, 400)


api.add_resource(Campers, "/campers")
api.add_resource(CamperById, "/campers/<int:id>")
api.add_resource(Activities, "/activities")
api.add_resource(ActivityById, "/activities/<int:id>")
api.add_resource(Signups, "/signups")

if __name__ == "__main__":
    app.run(port=5555, debug=True)
