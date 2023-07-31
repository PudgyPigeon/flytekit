import logging
import typing
from dataclasses import dataclass

import keyring as _keyring
from keyring.errors import NoKeyringError


@dataclass
class Credentials(object):
    """
    Stores the credentials together
    """

    access_token: str
    refresh_token: str = "na"
    for_endpoint: str = "flyte-default"
    expires_in: typing.Optional[int] = None


class KeyringStore:
    """
    Methods to access Keyring Store.
    """

    _access_token_key = "access_token"
    _refresh_token_key = "refresh_token"

    @staticmethod
    def store(credentials: Credentials) -> Credentials:
        try:
            _keyring.set_password(
                credentials.for_endpoint,
                KeyringStore._refresh_token_key,
                credentials.refresh_token,
            )
            _keyring.set_password(
                credentials.for_endpoint,
                KeyringStore._access_token_key,
                credentials.access_token,
            )
        except NoKeyringError as e:
            logging.debug(f"KeyRing not available, tokens will not be cached. Error: {e}")
        return credentials

    @staticmethod
    def retrieve(for_endpoint: str) -> typing.Optional[Credentials]:
        logging.warning("ATTEMPTING TO INITIALIZE KEYRING STORE")
        try:
            logging.warning("TRYING TO RUN KEYRING PACKAGE METHODS")
            refresh_token = _keyring.get_password(for_endpoint, KeyringStore._refresh_token_key)
            logging.warning("REFRESH TOKEN: ")
            logging.warning(refresh_token)
            logging.warning("RUNNING ACCESSTOKEN METHOD AFTER REFRESH TOKEN")
            access_token = _keyring.get_password(for_endpoint, KeyringStore._access_token_key)
        except NoKeyringError as e:
            logging.warning(f"KeyRing not available, tokens will not be cached. Error: {e}")
            return None

        if not access_token:
            logging.warning("NO ACCESS TOKEN, RETURNING NONE")
            return None

        logging.warning("RETURNING CREDENTIALS DATACLASS OBJECT")
        return Credentials(access_token, refresh_token, for_endpoint)

    @staticmethod
    def delete(for_endpoint: str):
        try:
            _keyring.delete_password(for_endpoint, KeyringStore._access_token_key)
            _keyring.delete_password(for_endpoint, KeyringStore._refresh_token_key)
        except NoKeyringError as e:
            logging.debug(f"KeyRing not available, tokens will not be cached. Error: {e}")
