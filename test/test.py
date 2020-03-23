from processors.conversion import process_file
import os
import shutil
from bs4 import BeautifulSoup
import re

d = os.path.dirname(__file__)
t = d + "/temp"

if os.path.exists(t):
    shutil.rmtree(t)
os.mkdir(t)

for line in process_file(d + "/test.pdf", t):
    pass
