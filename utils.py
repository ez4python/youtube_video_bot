def format_size(size_in_bytes):
    size_mb = size_in_bytes / (1024 * 1024)
    return f"{size_mb:.2f} MB"


def format_view(views):
    views = int(views)
    if 0 < views < 1000:
        return views
    elif 1000 <= views <= 999999:
        views = float(views) / 1000
        return f'{views:.1f}K'
    elif 1000000 <= views <= 999999999:
        views = float(views) / 1000000
        return f'{views:.1f}M'
    elif views >= 1000000000:
        views = float(views) / 1000000000
        return f'{views:.1f}B'


def format_duration(seconds):
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    if hours > 0:
        return f"{hours:02}:{minutes:02}:{seconds:02}"
    else:
        return f"{minutes:02}:{seconds:02}"
