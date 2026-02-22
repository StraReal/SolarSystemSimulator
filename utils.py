import webbrowser

def interpolate_colors(col1, col2):
    col3 = ((col1[0]+col2[0])/2, (col1[1]+col2[1])/2, (col1[2]+col2[2])/2,)
    return col3
def open_url(target_url): #ONLY USED TO OPEN GITHUB REPO LINK
    """Launch the default browser to target_url."""
    webbrowser.open_new(target_url)