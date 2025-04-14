import os
import sys

# Add the parent directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from jobsonTwo.web.app import app

if __name__ == '__main__':
    app.run(port=3001) 