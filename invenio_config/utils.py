# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2018 CERN.
# Copyright (C) 2024 KTH Royal Institute of Technology.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Default configuration loader usable by e.g. Invenio-Base."""

from __future__ import absolute_import, print_function

import os

from .default import InvenioConfigDefault
from .entrypoint import InvenioConfigEntryPointModule
from .env import InvenioConfigEnvironment
from .folder import InvenioConfigInstanceFolder
from .module import InvenioConfigModule


def create_config_loader(config=None, env_prefix="APP"):
    """Create a default configuration loader.

    A configuration loader takes a Flask application and keyword arguments and
    updates the Flask application's configuration as it sees fit.

    This default configuration loader will load configuration in the following
    order:

        1. Load configuration from ``invenio_config.module`` entry points
           group, following the alphabetical ascending order in case of
           multiple entry points defined.
           For example, the config of an app with entry point name ``10_app``
           will be loaded after the config of an app with entry point name
           ``00_app``.
        2. Load configuration from ``config`` module if provided as argument.
        3. Load configuration from the instance folder:
           ``<app.instance_path>/<app.name>.cfg``.
        4. Load configuration keyword arguments provided.
        5. Load configuration from environment variables with the prefix
           ``env_prefix``.

    If no secret key has been set a warning will be issued.

    :param config: Either an import string to a module with configuration or
        alternatively the module itself.
    :param env_prefix: Environment variable prefix to import configuration
        from.
    :return: A callable with the method signature
        ``config_loader(app, **kwargs)``.

    .. versionadded:: 1.0.0
    """

    def _config_loader(app, **kwargs_config):
        InvenioConfigEntryPointModule(app=app)
        if config:
            InvenioConfigModule(app=app, module=config)
        InvenioConfigInstanceFolder(app=app)
        app.config.update(**kwargs_config)
        InvenioConfigEnvironment(app=app, prefix="{0}_".format(env_prefix))
        InvenioConfigDefault(app=app)

    return _config_loader


def create_conf_loader(*args, **kwargs):  # pragma: no cover
    """Create a default configuration loader.

    .. deprecated:: 1.0.0b1
       Use :func:`create_config_loader` instead. This function will be removed
       in version 1.0.1.
    """
    import warnings

    warnings.warn(
        '"create_conf_loader" has been renamed to "create_config_loader".',
        DeprecationWarning,
    )
    return create_config_loader(*args, **kwargs)


def _get_env_var(prefix, keys):
    """Retrieve environment variables with a given prefix."""
    return {k: os.environ.get(f"{prefix}_{k.upper()}") for k in keys}


def build_db_uri():
    """
    Build database URI from environment variables or use default.

    Priority order:
    1. INVENIO_SQLALCHEMY_DATABASE_URI
    2. SQLALCHEMY_DATABASE_URI
    3. INVENIO_DB_* specific environment variables
    4. Default URI

    Note: For option 3, to assert that the INVENIO_DB_* settings take effect,
    you need to set SQLALCHEMY_DATABASE_URI="" in your environment.
    """
    default_uri = "postgresql+psycopg2://invenio-app-rdm:invenio-app-rdm@localhost/invenio-app-rdm"

    uri = os.environ.get("INVENIO_SQLALCHEMY_DATABASE_URI") or os.environ.get(
        "SQLALCHEMY_DATABASE_URI"
    )
    if uri:
        return uri

    db_params = _get_env_var(
        "INVENIO_DB", ["user", "password", "host", "port", "name", "protocol"]
    )
    if all(db_params.values()):
        uri = f"{db_params['protocol']}://{db_params['user']}:{db_params['password']}@{db_params['host']}:{db_params['port']}/{db_params['name']}"
        return uri

    return default_uri


def build_broker_url():
    """
    Build broker URL from environment variables or use default.

    Priority order:
    1. INVENIO_BROKER_URL
    2. BROKER_URL
    3. INVENIO_BROKER_* specific environment variables
    4. Default URL
    """
    default_url = "amqp://guest:guest@localhost:5672/"

    uri = os.environ.get("INVENIO_BROKER_URL") or os.environ.get("BROKER_URL")
    if uri:
        return uri

    broker_params = _get_env_var(
        "INVENIO_BROKER", ["user", "password", "host", "port", "protocol"]
    )
    if all(broker_params.values()):
        vhost = f"{os.environ.get("INVENIO_BROKER_VHOST").lstrip("/")}"
        return f"{broker_params['protocol']}://{broker_params['user']}:{broker_params['password']}@{broker_params['host']}:{broker_params['port']}/{vhost}"

    return default_url


def build_redis_url(db=None):
    """
    Build Redis URL from environment variables or use default.

    Priority order:
    1. BROKER_URL (Redis-based)
    2. INVENIO_REDIS_URL
    3. INVENIO_REDIS_* specific environment variables
    4. Default URL
    """
    db = db if db is not None else 0
    default_url = f"redis://localhost:6379/{db}"

    uri = os.environ.get("BROKER_URL")
    if uri and uri.startswith(("redis://", "rediss://", "unix://")):
        return uri

    uri = os.environ.get("INVENIO_REDIS_URL")
    if uri:
        return uri

    redis_params = _get_env_var(
        "INVENIO_REDIS", ["host", "port", "password", "protocol"]
    )
    redis_params["protocol"] = redis_params.get("protocol") or "redis"

    if redis_params["host"] and redis_params["port"]:
        password = (
            f":{redis_params['password']}@" if redis_params.get("password") else ""
        )
        return f"{redis_params['protocol']}://{password}{redis_params['host']}:{redis_params['port']}/{db}"

    return default_url
