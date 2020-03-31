# Dash

Repository of DASH data viz apps

## Structure

- `main.py`: Run the debug/dev server.

The directory `viz` contains the source code.
  
- `app.py`: Global configuration.
- `uswgi.py`: Run the production server.
- `models/<name>/`: Each directory represents the model as python module. For example, the directory economic is the models.economic and it represents the economic model.
- `models/<name>/__init__.py`: Code the python module.
- `data/`: Data directory
- `index.py`: Imports the module and expose it as a path on the webserver. For example, the module models.economic is exposed as /economic.
- `assets/`: The assets director for static files.

## How to run

### Production

```bash
docker-compose up -d
```

The app is running at <http://localhost:10000>

### Development

```bash
pip install -r requirements.txt
python main.py
```

The app is running at <http://localhost:8050>
