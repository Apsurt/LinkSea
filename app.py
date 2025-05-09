from flask import Flask, render_template, request, redirect, url_for, abort
import uuid
import random
import string
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse

app = Flask(__name__)

# In-memory store for link groups.
link_groups = {}

def generate_short_id(length=6):
    """Generates a random short ID of specified length using letters and digits."""
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))

def fetch_title_and_favicon(url):
    """Fetches the title and constructs the favicon URL from a given URL."""
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}
        response = requests.get(url, headers=headers, timeout=5)
        response.raise_for_status()  # Raise an exception for bad status codes
        soup = BeautifulSoup(response.text, 'html.parser')
        title_tag = soup.find('title')
        title = title_tag.string.strip() if title_tag and title_tag.string else url
        parsed_url = urlparse(url)
        favicon_url = f"{parsed_url.scheme}://{parsed_url.netloc}/favicon.ico"
        return title, favicon_url
    except requests.exceptions.RequestException:
        return url, None
    except Exception:
        return url, None

@app.route('/', methods=['GET', 'POST'])
def index():
    """
    Handles the home page.
    GET: Displays the page to create a new group.
    POST: Creates a new group with a short alphanumeric ID and redirects to it.
    """
    if request.method == 'POST':
        group_id = generate_short_id()
        while group_id in link_groups:
            group_id = generate_short_id()
        group_name = request.form.get('group_name', 'Untitled Group').strip()
        link_groups[group_id] = {"name": group_name, "links": []}
        return redirect(url_for('view_group', group_id=group_id))
    return render_template('index.html')

@app.route('/<group_id>', methods=['GET'])
def view_group(group_id):
    """
    Displays the links within a specific group and the rename form.
    """
    group = link_groups.get(group_id)
    if not group:
        abort(404, description="Group not found. This LinkSea group ID is invalid or has expired.")
    return render_template('group.html', group_id=group_id, group_name=group['name'], links=group['links'], enumerate=enumerate)

@app.route('/<group_id>/rename', methods=['POST'])
def rename_group(group_id):
    """
    Renames the specified link group.
    """
    group = link_groups.get(group_id)
    if not group:
        abort(404, description="Group not found. Cannot rename.")
    new_name = request.form.get('group_name').strip()
    if new_name:
        group['name'] = new_name
    return redirect(url_for('view_group', group_id=group_id))

@app.route('/<group_id>/add', methods=['POST'])
def add_link(group_id):
    """
    Adds a new link to the specified group, fetching its title and favicon.
    """
    group = link_groups.get(group_id)
    if not group:
        abort(404, description="Group not found. Cannot add link.")

    url = request.form.get('url')
    note = request.form.get('note', '').strip()

    if not url:
        return redirect(url_for('view_group', group_id=group_id, error="URL is required."))

    if not url.startswith(('http://', 'https://')):
        url = 'http://' + url

    link_id = str(uuid.uuid4())
    title, favicon_url = fetch_title_and_favicon(url)
    group['links'].append({"id": link_id, "url": url, "note": note, "title": title, "favicon": favicon_url})

    return redirect(url_for('view_group', group_id=group_id))

@app.route('/<group_id>/remove/<link_id>', methods=['POST'])
def remove_link(group_id, link_id):
    """
    Removes a specific link from a group.
    """
    group = link_groups.get(group_id)
    if not group:
        abort(404, description="Group not found. Cannot remove link.")

    group['links'] = [link for link in group['links'] if link['id'] != link_id]

    return redirect(url_for('view_group', group_id=group_id))

@app.route('/<group_id>/reorder/<link_id>', methods=['POST'])
def reorder_link(group_id, link_id):
    """
    Reorders a link within a group (moves it up or down).
    """
    group = link_groups.get(group_id)
    if not group:
        abort(404, description="Group not found. Cannot reorder link.")

    direction = request.args.get('direction')
    if direction not in ['up', 'down']:
        abort(400, description="Invalid reorder direction.")

    current_links = group['links']
    link_index = -1
    for i, link_item in enumerate(current_links):
        if link_item['id'] == link_id:
            link_index = i
            break

    if link_index == -1:
        abort(404, description="Link not found in this group.")

    if direction == 'up':
        if link_index > 0:
            current_links[link_index], current_links[link_index - 1] = current_links[link_index - 1], current_links[link_index]
    elif direction == 'down':
        if link_index < len(current_links) - 1:
            current_links[link_index], current_links[link_index + 1] = current_links[link_index + 1], current_links[link_index]

    return redirect(url_for('view_group', group_id=group_id))

# Custom 404 error page
@app.errorhandler(404)
def page_not_found(e):
    """
    Handles 404 errors with a custom page.
    """
    return render_template('404.html', error=e), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
