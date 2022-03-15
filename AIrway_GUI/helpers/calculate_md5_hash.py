import copy
import hashlib


def get_md5_hash(path):
    """
    Calculates the md5 hash for a specific file.
    """
    md5_hash = hashlib.md5()
    md5_hash.update(open(path, 'rb').read())
    return md5_hash.hexdigest()
