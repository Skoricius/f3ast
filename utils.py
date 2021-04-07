import hjson


def load_settings(file_path='settings.hjson'):
    with open(file_path, 'r') as f:
        settings = hjson.load(f)
    return settings
