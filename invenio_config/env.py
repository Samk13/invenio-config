# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Invenio environment configuration."""

from __future__ import absolute_import, print_function

import ast
import os
from functools import cached_property, lru_cache


class InvenioConfigEnvironment(object):
    """Load configuration from environment variables.

    .. versionadded:: 1.0.0
    """

    def __init__(self, app=None, prefix="INVENIO_"):
        """Initialize extension."""
        self.prefix = prefix
        if app:
            self.init_app(app)

    def init_app(self, app):
        """Initialize Flask application."""
        prefix_len = len(self.prefix)
        for varname, value in os.environ.items():
            if not varname.startswith(self.prefix):
                continue

            # Prepare values
            varname = varname[prefix_len:]
            value = value or app.config.get(varname)

            # Evaluate value
            try:
                value = ast.literal_eval(value)
            except (SyntaxError, ValueError):
                pass

            # Set value
            app.config[varname] = value


class InvenioConfigURLBuilder:
    """Build URLs for various Invenio services from environment variables."""

    def _get_env_vars(self, prefix, keys):
        """Retrieve environment variables with the given prefix and keys."""
        return {key: os.getenv(f"{prefix}_{key.upper()}") for key in keys}

    @cached_property
    def db_uri(self):
        """Build database URI from environment variables."""
        default_uri = "postgresql+psycopg2://invenio-app-rdm:invenio-app-rdm@localhost/invenio-app-rdm"

        uri = os.getenv("INVENIO_SQLALCHEMY_DATABASE_URI") or os.getenv(
            "SQLALCHEMY_DATABASE_URI"
        )
        if uri:
            return uri

        db_params = self._get_env_vars(
            "INVENIO_DB", ["user", "password", "host", "port", "name", "protocol"]
        )
        if all(db_params.values()):
            return (
                f"{db_params['protocol']}://{db_params['user']}:{db_params['password']}@"
                f"{db_params['host']}:{db_params['port']}/{db_params['name']}"
            )

        return default_uri

    @cached_property
    def broker_url(self):
        """Build broker URL from environment variables."""
        default_url = "amqp://guest:guest@localhost:5672/"

        uri = os.getenv("INVENIO_BROKER_URL") or os.getenv("BROKER_URL")
        if uri:
            return uri

        broker_params = self._get_env_vars(
            "INVENIO_BROKER", ["user", "password", "host", "port", "protocol"]
        )
        if all(broker_params.values()):
            vhost = os.getenv("INVENIO_BROKER_VHOST", "").lstrip("/")
            return (
                f"{broker_params['protocol']}://{broker_params['user']}:{broker_params['password']}@"
                f"{broker_params['host']}:{broker_params['port']}/{vhost}"
            )

        return default_url

    @lru_cache(maxsize=128)
    def get_redis_url(self, db=0):
        """Build Redis URL with optional db parameter."""
        db = db if db is not None else 0
        default_url = f"redis://localhost:6379/{db}"

        uri = os.getenv("BROKER_URL")
        if uri and uri.startswith(("redis://", "rediss://", "unix://")):
            return uri

        uri = os.getenv("INVENIO_REDIS_URL")
        if uri:
            return uri

        redis_params = self._get_env_vars(
            "INVENIO_REDIS", ["host", "port", "password", "protocol"]
        )
        redis_params["protocol"] = redis_params.get("protocol") or "redis"

        if redis_params["host"] and redis_params["port"]:
            password = (
                f":{redis_params['password']}@" if redis_params.get("password") else ""
            )
            return f"{redis_params['protocol']}://{password}{redis_params['host']}:{redis_params['port']}/{db}"

        return default_url


def build_db_uri():
    """Build database URI from environment variables."""
    return InvenioConfigURLBuilder().db_uri


def build_broker_url():
    """Build broker URL from environment variables."""
    return InvenioConfigURLBuilder().broker_url


def build_redis_url(db=None):
    """Build Redis URL from environment variables."""
    return InvenioConfigURLBuilder().get_redis_url(db)
