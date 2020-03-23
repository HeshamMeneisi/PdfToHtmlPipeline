#!/usr/bin/env python
# coding: utf-8

from helpers.pdf2html import convert_from_path
import os
import tempfile
from shutil import rmtree
from zipfile import ZipFile
from bs4 import BeautifulSoup
import re


def process_file(fname, dest_dir):
    ext = os.path.splitext(fname)[-1]
    file_name = '.'.join(os.path.splitext(os.path.split(fname)[-1])[:-1])
    temp_dir = tempfile.gettempdir()
    if ext.lower() == '.zip':
        yield "Unzipping file..."
        temp_unzip_dir = os.path.join(temp_dir, file_name)
        try:
            rmtree(temp_unzip_dir)
        except:
            pass
        os.mkdir(temp_unzip_dir)
        with ZipFile(fname, 'r') as zipObj:
            zipObj.extract(temp_unzip_dir)
            files = [os.path.join(temp_unzip_dir, f) for f in os.listdir(temp_unzip_dir)]
    elif ext.lower() == '.pdf':
        files = [fname]
    else:
        raise Exception(
            "Unsupported file format (%s) accepted formats are: .pdf, .zip(containing pdf files)" % ext)

    client_data = {}

    for file in files:
        yield "Converting file [%s] ..." % file
        ext = os.path.splitext(file)[-1]
        file_name = '.'.join(os.path.splitext(os.path.split(fname)[-1])[:-1])
        output_file = os.path.join(dest_dir, file_name + ".html")
        if os.path.exists(output_file):
            raise Exception("Output target (%s) already exists. Please delete or rename current file before upload.")
        if ext.lower() == ".pdf":
            convert_from_path(file,
                              single_file=True,
                              output_file=output_file,
                              # complex_styles=True,
                              # embed_images=True,
                              no_frames=True,
                              no_images=True,
                              center_pages=True,
                              no_bg_color=True,
                              # title_from_file_name=True
                              )
            yield "Detecting h# tags in " + output_file
            detect_tags(output_file)
        else:
            raise Exception("Unsupported file type (%s) please only include [.pdf, .zip] files." % ext)


def detect_tags(html_file):
    soup = BeautifulSoup(open(html_file), "html.parser")

    def get_page(el):
        parent = el.parent
        while parent.parent.name != "body":
            parent = parent.parent
        return parent["id"]

    candidates = []

    for p in soup.find_all('p'):
        children = list(p.children)
        if len(children) != 1:
            continue
        child = children[0]
        if child.name != "b":
            continue
        style = p["style"]
        mx = re.findall("left:([0-9]+)", style)
        my = re.findall("top:([0-9]+)", style)
        x = y = None
        if len(mx):
            x = mx[0]
        if len(my):
            y = my[0]
        candidates.append({
            "p": p,
            "b": child,
            "pos": (x, y),
            "page": get_page(p)
        })

    merged_candidates = {}

    for c in candidates:
        key = c['page'] + '_' + c['pos'][1]
        if key not in merged_candidates:
            merged_candidates[key] = []
        merged_candidates[key].append(c)

    headers = []
    for key, group in merged_candidates.items():
        text = group[0]["p"].text
        pattern = re.sub("[0-9]+", "*", text)
        num = re.sub("[^0-9]+", "", text)
        header = {"group": group, 'generic': False}

        if num != pattern and re.match("^[0-9].+", text):
            header['num'] = num
            header['pattern'] = pattern
        elif re.match("^([^\\w\\s][\\w\\s][^\\w\\s]*)|([^\\w\\s]*[\\w\\s][^\\w\\s])", pattern):
            m = re.findall("^([^\\w\\s][\\w\\s][^\\w\\s]*)|([^\\w\\s]*[\\w\\s][^\\w\\s])", pattern)[0]
            text = m[0] if m[0] else m[1]
            header['pattern'] = re.sub("[\\w\\s]", "*", text)
            header['alpha'] = re.sub("[^\\w\\s]", "", text)
            # print(header['pattern'], header['alpha'])
        elif re.match("^[A-Z]", group[0]['p'].text):
            header['pattern'] = "NONUM"
            header['generic'] = True
        else:
            continue
        headers.append(header)

    pattern_state = {}
    current_level = 0
    current_pattern = None

    def delete_higher_than(thresh):
        to_del = []
        for p, l in pattern_state.items():
            if l > thresh:
                to_del.append(p)
        for p in to_del:
            del pattern_state[p]

    for header in headers:
        pattern = header['pattern']

        if pattern not in pattern_state:
            current_level += 1
            current_pattern = pattern
            pattern_state[pattern] = current_level
        else:
            current_pattern = pattern
            current_level = pattern_state[pattern]
            delete_higher_than(current_level)

        htag = soup.new_tag("h" + str(current_level))
        g0 = header['group'][0]
        htag['style'] = "all: unset;"
        for g in header['group']:
            g['p'].wrap(htag)

    with open(html_file, "w") as f:
        f.write(str(soup))
