from application.error import CaseworkFrontEndError
import requests


# Boring routines to stop writing the same if 500, raise error

def http_get(url, **kwargs):
    response = requests.get(url, **kwargs)
    if response.status_code == 500:
        raise CaseworkFrontEndError(response.text)
    return response


def http_delete(url, **kwargs):
    response = requests.delete(url, **kwargs)
    if response.status_code == 500:
        raise CaseworkFrontEndError(response.text)
    return response


def http_post(url, data=None, **kwargs):
    response = requests.post(url, data=data, **kwargs)
    if response.status_code == 500:
        raise CaseworkFrontEndError(response.text)
    return response


def http_put(url, data=None, **kwargs):
    response = requests.put(url, data=data, **kwargs)
    if response.status_code == 500:
        raise CaseworkFrontEndError(response.text)
    return response