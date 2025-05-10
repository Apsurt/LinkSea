from flask import Flask, render_template, request, redirect, url_for, abort
import uuid
import random
import string
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import os
from supabase import create_client, Client
from dotenv import load_dotenv
from datetime import datetime

app = Flask(__name__)

# Load environment variables
load_dotenv()
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

# Initialize Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


def generate_short_id(length=6):
    """Generates a random short ID."""
    characters = ''.join(c for c in string.ascii_uppercase + string.digits if c not in 'ILO0')
    return ''.join(random.choice(characters) for _ in range(length))


def fetch_title_and_favicon(url):
    """Fetches title and favicon, with improved favicon discovery."""
    title = url
    favicon_url = None
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'}
        response = requests.get(url, headers=headers, timeout=5)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        # Fetch title
        title_tag = soup.find('title')
        if title_tag and title_tag.string:
            full_title = title_tag.string.strip()
            parts = full_title.split(' · ')
            title = parts[0].strip() if parts else full_title

        # Fetch favicon
        parsed_url = urlparse(url)
        base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
        favicon_link = soup.find('link', rel='icon')
        if favicon_link and 'href' in favicon_link.attrs:
            favicon_href = favicon_link['href']
            if urlparse(favicon_href).netloc:  # If it's an absolute URL
                favicon_url = favicon_href
            else:  # If it's a relative URL, construct the absolute URL
                favicon_url = f"{base_url}{favicon_href}"
        elif parsed_url.netloc:
            favicon_url = f"{base_url}/favicon.ico"

        return title, favicon_url
    except requests.exceptions.RequestException:
        return url, None
    except Exception:
        return url, None


@app.route('/', methods=['GET', 'POST'])
def index():
    """Handles the home page:
    GET:  Displays the page to create a new group.
    POST: Creates a new group in the database and redirects to it.
    """
    if request.method == 'POST':
        group_name = request.form.get('group_name')
        if not group_name or group_name.strip() == "":
            group_name = "Unnamed Group"
        else:
            group_name = group_name.strip()

        group_id = generate_short_id()
        while True:  # Ensure unique ID (though DB should enforce this)
            response = supabase.table('groups').select('id').eq('id', group_id).execute()
            if not response.data:
                break
            group_id = generate_short_id()

        # Insert the new group into the database
        response = supabase.table('groups').insert({
            'id': group_id,
            'name': group_name,
            'last_accessed': datetime.now().isoformat()
        }).execute()

        # TODO I NEED TO COME BACK TO THIS
        # if response.error:
        #     print(f"Database error creating group: {response.error}")
        #     abort(500, "Failed to create group.")  # Internal Server Error

        return redirect(url_for('view_group', group_id=group_id))

    return render_template('index.html')


@app.route('/<group_id>', methods=['GET'])
def view_group(group_id):
    """Displays the links within a specific group."""

    # Fetch the group and its links from the database
    response = supabase.table('groups').select('*').eq('id', group_id).execute()
    group_data = response.data
    if not group_data:
        abort(404, description="Group not found.")

    group = group_data[0]  # Assuming only one group with this ID

    links_response = supabase.table('links').select('*').eq('group_id', group_id).order('order').execute() # Fetch links ordered by 'order'
    links = links_response.data

    # Update last_accessed timestamp
    supabase.table('groups').update({'last_accessed': datetime.now().isoformat()}).eq('id', group_id).execute()

    return render_template('group.html', group_id=group['id'], group_name=group['name'], links=links,
                           enumerate=enumerate)


@app.route('/<group_id>/rename', methods=['POST'])
def rename_group(group_id):
    """Renames the specified link group."""

    new_name = request.form.get('group_name').strip()
    if new_name:
        response = supabase.table('groups').update({'name': new_name}).eq('id', group_id).execute()
        # if response.error:
        #     print(f"Database error renaming group: {response.error}")
        #     abort(500, "Failed to rename group.")

    return redirect(url_for('view_group', group_id=group_id))


@app.route('/<group_id>/add', methods=['POST'])
def add_link(group_id):
    """Adds a new link to the specified group."""

    url = request.form.get('url')
    note = request.form.get('note', '').strip()

    if not url:
        return redirect(url_for('view_group', group_id=group_id, error="URL is required."))

    if not url.startswith(('http://', 'https://')):
        url = 'http://' + url

    link_id = str(uuid.uuid4())
    title, favicon_url = fetch_title_and_favicon(url)

    # Determine the next available order
    order_response = supabase.table('links').select('order').eq('group_id', group_id).order('order', desc=True).limit(1).execute()
    next_order = 0
    if order_response.data:
        next_order = order_response.data[0]['order'] + 1

    response = supabase.table('links').insert({
        'id': link_id,
        'group_id': group_id,
        'url': url,
        'note': note,
        'title': title,
        'favicon': favicon_url,
        'order': next_order  # Add the order here
    }).execute()

    # if response.error:
    #     print(f"Database error adding link: {response.error}")
    #     abort(500, "Failed to add link.")

    return redirect(url_for('view_group', group_id=group_id))


@app.route('/<group_id>/remove/<link_id>', methods=['POST'])
def remove_link(group_id, link_id):
    """Removes a specific link from a group."""

    response = supabase.table('links').delete().eq('id', link_id).execute()
    # if response.error:
    #     print(f"Database error removing link: {response.error}")
    #     abort(500, "Failed to remove link.")

    return redirect(url_for('view_group', group_id=group_id))


@app.route('/<group_id>/reorder/<link_id>', methods=['POST'])
def reorder_link(group_id, link_id):
    """Reorders a link within a group (moves it up or down)."""

    direction = request.args.get('direction')
    if direction not in ['up', 'down']:
        abort(400, description="Invalid reorder direction.")

    # Fetch all links for the group, ordered by 'order'
    links_response = supabase.table('links').select('id, order').eq('group_id', group_id).order('order').execute()
    links = links_response.data

    if not links:
        abort(404, description="No links found in this group.")

    link_index = -1
    for i, link in enumerate(links):
        if link['id'] == link_id:
            link_index = i
            break

    if link_index == -1:
        abort(404, description="Link not found in this group.")

    if direction == 'up':
        if link_index > 0:
            # Swap 'order' values with the previous link
            links[link_index]['order'], links[link_index - 1]['order'] = links[link_index - 1]['order'], links[link_index]['order']
    elif direction == 'down':
        if link_index < len(links) - 1:
            # Swap 'order' values with the next link
            links[link_index]['order'], links[link_index + 1]['order'] = links[link_index + 1]['order'], links[link_index]['order']

    # Bulk update the 'order' values in the database
    for link in links:
        response = supabase.table('links').update({'order': link['order']}).eq('id', link['id']).execute()
        # if response.error:
        #     print(f"Database error reordering link {link['id']}: {response.error}")
        #     abort(500, "Failed to reorder links.")

    return redirect(url_for('view_group', group_id=group_id))


@app.route('/<group_id>/edit/<link_id>', methods=['POST'])
def edit_link(group_id, link_id):
    """Edits the title of a specific link."""

    new_title = request.form.get('title').strip()
    if not new_title:
        return redirect(url_for('view_group', group_id=group_id, error="Title cannot be empty."))

    response = supabase.table('links').update({'title': new_title}).eq('id', link_id).execute()
    # if response.error:
    #     print(f"Database error editing link: {response.error}")
    #     abort(500, "Failed to edit link.")

    return redirect(url_for('view_group', group_id=group_id))


# Custom 404 error page
@app.errorhandler(404)
def page_not_found(e):
    """Handles 404 errors with a custom page."""
    return render_template('404.html', error=e), 404


if __name__ == '__main__':
    app.run()
