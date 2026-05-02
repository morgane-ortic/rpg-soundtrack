# Convert integer in milliseconds into a hh:mm:ss string
def format_duration(milliseconds):
    h = 0
    m = 0
    total_seconds = milliseconds // 1000
    h, rem = divmod(total_seconds, 3600)
    m, s = divmod(rem, 60)
        
    if h > 0:
        duration = f'{h:02d}:{m:02d}:{s:02d}'
    else :
        duration = f'{m:02d}:{s:02d}'

    return duration