"""Entry point. The game itself lives in src/pambaram/ - this just puts
that package on the path and hands off to it, so `python main.py` keeps
working unchanged from the project root."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))

from pambaram.main import main

if __name__ == "__main__":
    main()
