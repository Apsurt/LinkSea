from flask import Flask, render_template, request, redirect, url_for, abort
import uuid # Still used for link IDs, but not group IDs
import random
import string

app = Flask(__name__)

# In-memory store for link groups.
link_groups = {}

def generate_short_id(length=6):
    """Generates a random short ID of specified length using letters and digits."""
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))

@app.route('/', methods=['GET', 'POST'])
def index():
    """
    Handles the home page.
    GET: Displays the page to create a new group.
    POST: Creates a new group with a short alphanumeric ID and redirects to it.
    """
    if request.method == 'POST':
        group_id = generate_short_id()
        # Ensure the generated ID is unique (highly unlikely to collide with 6 chars, but good practice)
        while group_id in link_groups:
            group_id = generate_short_id()

        link_groups[group_id] = {"links": []} # Initialize the group
        return redirect(url_for('view_group', group_id=group_id))
    return render_template('index.html')

@app.route('/<group_id>', methods=['GET'])
def view_group(group_id):
    """
    Displays the links within a specific group.
    """
    group = link_groups.get(group_id)
    if not group:
        abort(404, description="Group not found. This LinkSea group ID is invalid or has expired.")
    # Pass the enumerate function to the template to get index for reordering
    return render_template('group.html', group_id=group_id, links=group['links'], enumerate=enumerate)

@app.route('/<group_id>/add', methods=['POST'])
def add_link(group_id):
    """
    Adds a new link to the specified group.
    """
    group = link_groups.get(group_id)
    if not group:
        abort(404, description="Group not found. Cannot add link.")

    url = request.form.get('url')
    note = request.form.get('note', '') # Optional note

    if not url:
        # Basic validation: URL is required
        return redirect(url_for('view_group', group_id=group_id, error="URL is required."))

    # Add http:// prefix if missing
    if not url.startswith(('http://', 'https://')):
        url = 'http://' + url

    link_id = str(uuid.uuid4()) # Link IDs can remain UUIDs for uniqueness within a group
    group['links'].append({"id": link_id, "url": url, "note": note})

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
    for i, link_item in enumerate(current_links): # Renamed 'link' to 'link_item' to avoid conflict
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
