import json
import os
import sqlalchemy
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, send_file, make_response, \
    Response, jsonify,session
import threading
from . import LOG, APP

bp = Blueprint('view', __name__, url_prefix='/crest_global', template_folder="./templates", static_folder="./static")


@bp.route('/', methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template('login.html')

