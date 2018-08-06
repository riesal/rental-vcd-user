# lets built
import os, json, requests
from flask import Flask, make_response
from werkzeug.exceptions import NotFound, ServiceUnavailable

# addon
def root_dir():
    """ Returns root director for this project """
    #return os.path.dirname(os.path.realpath(__file__ + '/..'))
    return os.path.dirname(os.path.realpath(__file__ + '/'))

def nice_json(arg):
    response = make_response(json.dumps(arg, sort_keys = True, indent=4))
    response.headers['Content-type'] = "application/json"
    return response
# end-addon

app = Flask(__name__)

with open("{}/user.json".format(root_dir()), "r") as f:
    users = json.load(f)


@app.route("/", methods=['GET'])
def hello():
    return nice_json({
        "uri": "/",
        "subresource_uris": {
            "users": "/users",
            "user": "/users/<username>",
            "bookings": "/users/<username>/bookings",
            "suggested": "/users/<username>/suggested"
        }
    })


@app.route("/customers", methods=['GET'])
def customers_list():
    return nice_json(users)

@app.route("/admin", methods=['GET'])
def admin():
    return nice_json(users)

@app.route("/users", methods=['GET'])
def users_list():
    return nice_json(users)


@app.route("/users/<username>", methods=['GET'])
def user_record(username):
    if username not in users:
        raise NotFound

    return nice_json(users[username])


@app.route("/users/<username>/bookings", methods=['GET'])
def user_bookings(username):
    """
    Gets booking information from the 'Bookings Service' for the user, and
     movie ratings etc. from the 'Movie Service' and returns a list.
    :param username:
    :return: List of Users bookings
    """
    if username not in users:
        raise NotFound("User '{}' not found.".format(username))

    try:
        users_bookings = requests.get("http://internal-docker-test-internal-alb-1335550888.ap-southeast-1.elb.amazonaws.com/bookings/{}".format(username))
    except requests.exceptions.ConnectionError:
        raise ServiceUnavailable("The Bookings service is unavailable.")

    if users_bookings.status_code == 404:
        raise NotFound("No bookings were found for {}".format(username))

    users_bookings = users_bookings.json()

    # For each booking, get the rating and the movie title
    result = {}
    for date, movies in users_bookings.iteritems():
        result[date] = []
        for movieid in movies:
            try:
                movies_resp = requests.get("http://react-ecs.orami.co.id/movies/{}".format(movieid))
            except requests.exceptions.ConnectionError:
                raise ServiceUnavailable("The Movie service is unavailable.")
            movies_resp = movies_resp.json()
            result[date].append({
                "title": movies_resp["title"],
                "rating": movies_resp["rating"],
                "uri": movies_resp["uri"]
            })

    return nice_json(result)


@app.route("/users/<username>/suggested", methods=['GET'])
def user_suggested(username):
    """
    Returns movie suggestions. The algorithm returns a list of 3 top ranked
    movies that the user has not yet booked.
    :param username:
    :return: Suggested movies
    """
    raise NotImplementedError()


if __name__ == "__main__":
    """app.run(debug=True, host='0.0.0.0', port=6004, use_reloader=True)"""
    app.run(debug=True, host='0.0.0.0', port=8080, use_reloader=True)
