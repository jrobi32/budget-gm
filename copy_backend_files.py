import shutil
import os

# Files to copy
files_to_copy = [
    'team_builder.py',
    'team_simulator.py',
    'player_pool.py',
    'player_pool.json',
    'models.py',
    'app.py',
    'wsgi.py',
    'season_simulator.py'
]

# Copy each file
for file in files_to_copy:
    if os.path.exists(file):
        shutil.copy2(file, f'budget-gm-backend/{file}')
        print(f'Copied {file} to budget-gm-backend/')
    else:
        print(f'Warning: {file} not found')

# Create templates directory if it doesn't exist
templates_dir = 'budget-gm-backend/templates'
os.makedirs(templates_dir, exist_ok=True)

# Create a basic index.html template
index_html = '''<!DOCTYPE html>
<html>
<head>
    <title>Budget GM</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body>
    <div id="root"></div>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>'''

with open(f'{templates_dir}/index.html', 'w') as f:
    f.write(index_html)
print('Created index.html template') 