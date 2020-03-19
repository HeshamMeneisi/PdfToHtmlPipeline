"""
    pdf2html is a light wrapper for the poppler-utils tools that can convert your
    PDFs into html file(s) and is originally a fork of pdf2image
"""

import os
import re
import platform
import tempfile
import string
import random
import shutil
import pathlib
import base64

from subprocess import Popen, PIPE

PDFINFO_CONVERT_TO_INT = ["Pages"]


def convert_from_path(
    pdf_path,
    output_folder=None,
    output_file=None,
    poppler_path=None,
    strict=False,
    title=None,
    title_from_file_name=False,
    embed_images=False,
    center_pages=False,
    first_page=None,
    last_page=None,
    dotpdf_to_link=None,
    complex_styles=None,
    single_file=None,
    no_images=None,
    no_frames=None,
    zoom=None,
    xml=None,
    no_coord_rounding=None,
    output_encoding=None,
    ownerpw=None,
    userpw=None,
    include_hidden=None,
    image_fmt=None,
    no_paragraph_merge=None,
    override_drm=None,
    word_break=None,
    use_font_full_name=None
):
    """
        Description: Convert PDF to Image will throw whenever one of the condition is reached
        Parameters:
            pdf_path -> Path to the PDF that you want to convert
            output_folder -> Write the resulting images to a folder (instead of directly in memory)
            first_page -> First page to process
            last_page -> Last page to process before stopping
            fmt -> Output image format
            userpw -> PDF's password
            use_cropbox -> Use cropbox instead of mediabox
            strict -> When a Syntax Error is thrown, it will be raised as an Exception
            transparent -> Output with a transparent background instead of a white one.
            single_file -> Uses the -singlefile option from pdftohtml
            output_file -> What is the output filename or generator
            poppler_path -> Path to look for poppler binaries
            grayscale -> Output grayscale image(s)
            size -> Size of the resulting image(s), uses the Pillow (width, height) standard
            paths_only -> Don't load image(s), return paths instead (requires output_folder)
    """

    # We make sure that if passed arguments are Path objects, they're converted to strings
    if isinstance(pdf_path, pathlib.PurePath):
        pdf_path = pdf_path.as_posix()

    if isinstance(output_folder, pathlib.PurePath):
        output_folder = output_folder.as_posix()

    if isinstance(poppler_path, pathlib.PurePath):
        poppler_path = poppler_path.as_posix()

    if embed_images and not single_file:
        print("embed_images currently only supported for single_file")
        embed_images = False

    page_count = pdfinfo_from_path(pdf_path, userpw, poppler_path=poppler_path)["Pages"]

    final_extension = "html"
    if xml:
        final_extension = "xml"

    if first_page is None:
        first_page = 1

    if last_page is None or last_page > page_count:
        last_page = page_count

    if first_page > last_page:
        return []

    auto_temp_dir = False

    temp_output_folder = tempfile.mkdtemp()

    # Recalculate page count based on first and last page
    page_count = last_page - first_page + 1

    args = [_get_command_path("pdftohtml", poppler_path)]

    file_name = ".".join(os.path.basename(pdf_path).split('.')[:-1])
    temp_pdf_path = os.path.abspath(os.path.join(temp_output_folder, file_name)) + ".pdf"

    shutil.copyfile(pdf_path, temp_pdf_path)

    args = _build_command(
        args,
        temp_pdf_path,
        first_page,
        last_page,
        dotpdf_to_link,
        complex_styles,
        single_file,
        no_images,
        no_frames,
        zoom,
        xml,
        no_coord_rounding,
        output_encoding,
        ownerpw,
        userpw,
        include_hidden,
        image_fmt,
        no_paragraph_merge,
        override_drm,
        word_break,
        use_font_full_name,
    )
    # Add poppler path to LD_LIBRARY_PATH
    env = os.environ.copy()
    if poppler_path is not None:
        env["LD_LIBRARY_PATH"] = poppler_path + ":" + env.get("LD_LIBRARY_PATH", "")

    # Spawn the process and save its uuid
    process = Popen(args, env=env, stdout=PIPE, stderr=PIPE)

    data, err = process.communicate()

    if err and strict:
        raise PDFPopplerError()

    ignore_pattern = "(.+\\.pdf)"

    output_html = os.path.join(temp_output_folder, file_name + "-html.html")

    if embed_images:
        ignore_pattern += "|(.+\\.png)|(.+\\.jpg)"
        for file in os.listdir(temp_output_folder):
            if file.lower().endswith(".png") or file.lower().endswith(".jpg"):
                embed_image_into_html(os.path.join(temp_output_folder, file), output_html)

    if center_pages:
        replace_in_file(output_html, "<head>",
            "<head>"
            "\n<!-- PDF2HTML STYLE START -->\n"
            "<style>body > * {margin: auto;}</style>\n"
            "<!-- PDF2HTML STYLE END -->")

    if title_from_file_name:
        title = file_name

    if title is not None:
        replace_in_file(output_html, "<title>{0}</title>".format(output_html), "<title>{0}</title>".format(title))

    if output_file:
        output_file_dir = os.path.dirname(output_file)
        copy_tree(temp_output_folder, output_file_dir, ignore_pattern)
        if single_file:
            os.rename(os.path.join(output_file_dir, file_name+"-html.html"), output_file)

    if output_folder:
        copy_tree(temp_output_folder, output_folder, ignore_pattern)

    if temp_pdf_path:
        os.remove(temp_pdf_path)

    shutil.rmtree(temp_output_folder)


def embed_image_into_html(image_path, html_path):
    data_uri = base64.b64encode(open(image_path, 'rb').read()).decode('utf-8')
    image_name = os.path.basename(image_path)
    image_ext = image_name.split(".")[-1]
    src = 'src="data:image/{0};base64,{1}"'.format(image_ext, data_uri)
    replace_in_file(html_path, 'src="{0}"'.format(image_name), src)


def replace_in_file(file_path, old, new):
    fin = open(file_path, "rt")
    data = fin.read()
    data = data.replace(old, new)
    fin.close()

    fin = open(file_path, "wt")
    fin.write(data)
    fin.close()


def copy_tree(source, dest, ignore_pattern):
    for name in os.listdir(source):
        if re.match(ignore_pattern, name):
            continue
        path = os.path.join(source, name)
        dest_path = os.path.join(dest, name)
        if os.path.isdir(path):
            copy_tree(path, dest_path)
        else:
            shutil.copyfile(path, dest_path)


def convert_from_bytes(
    pdf_file,
    output_folder=None,
    output_file=None,
    poppler_path=None,
    strict=False,
    title=None,
    title_from_file_name=False,
    embed_images=False,
    center_pages=False,
    first_page=None,
    last_page=None,
    dotpdf_to_link=None,
    complex_styles=None,
    single_file=None,
    no_images=None,
    no_frames=None,
    zoom=None,
    xml=None,
    no_coord_rounding=None,
    output_encoding=None,
    ownerpw=None,
    userpw=None,
    include_hidden=None,
    image_fmt=None,
    no_paragraph_merge=None,
    override_drm=None,
    word_break=None,
    use_font_full_name=None
):
    """
        Description: Convert PDF to Image will throw whenever one of the condition is reached
        Parameters:
            pdf_file -> Bytes representing the PDF file
            output_folder -> Write the resulting images to a folder (instead of directly in memory)
            first_page -> First page to process
            last_page -> Last page to process before stopping
            fmt -> Output image format
            userpw -> PDF's password
            strict -> When a Syntax Error is thrown, it will be raised as an Exception
            single_file -> Uses the -singlefile option from pdftohtml
            output_file -> What is the output filename or generator
            poppler_path -> Path to look for poppler binaries
    """

    fh, temp_filename = tempfile.mkstemp()
    try:
        with open(temp_filename, "wb") as f:
            f.write(pdf_file)
            f.flush()
            return convert_from_path(
                f.name,
                output_folder,
                output_file,
                poppler_path,
                strict,
                title,
                title_from_file_name,
                embed_images,
                center_pages,
                first_page,
                last_page,
                dotpdf_to_link,
                complex_styles,
                single_file,
                no_images,
                no_frames,
                zoom,
                xml,
                no_coord_rounding,
                output_encoding,
                ownerpw,
                userpw,
                include_hidden,
                image_fmt,
                no_paragraph_merge,
                override_drm,
                word_break,
                use_font_full_name
            )
    finally:
        os.close(fh)
        os.remove(temp_filename)


def _build_command(
    args,
    pdf_path,
    first_page=None,
    last_page=None,
    dotpdf_to_link=None,
    complex_styles=None,
    single_file=None,
    no_images=None,
    no_frames=None,
    zoom=None,
    xml=None,
    no_coord_rounding=None,
    output_encoding=None,
    ownerpw=None,
    userpw=None,
    include_hidden=None,
    image_fmt=None,
    no_paragraph_merge=None,
    override_drm=None,
    word_break=None,
    use_font_full_name=None,
):
    args.append(pdf_path)

    if first_page is not None:
        args.extend(["-f", str(first_page)])

    if last_page is not None:
        args.extend(["-l", str(last_page)])

    if last_page is not None:
        args.extend(["-l", str(last_page)])

    if dotpdf_to_link:
        args.append("-p")

    if complex_styles:
        args.append("-c")

    if single_file:
        args.append("-s")

    if no_images:
        args.append("-i")

    if no_frames:
        args.append("-noframes")

    if zoom is not None:
        args.extend(["-zoom", zoom])

    if xml:
        args.append("-xml")

    if no_coord_rounding:
        args.append("-noRoundedCoordinates")

    if output_encoding is not None:
        args.extend(["-enc", output_encoding])

    if ownerpw is not None:
        args.extend(["-opw", ownerpw])

    if userpw is not None:
        args.extend(["-opw", ownerpw])

    if include_hidden:
        args.append("-hidden")

    if image_fmt is not None:
        args.extend(["-fmt", image_fmt])

    if no_paragraph_merge:
        args.append("-nomerge")

    if override_drm:
        args.append("-nodrm")

    if word_break is not None:
        args.extend(["-wbt", word_break])

    if use_font_full_name:
        args.append("-fontfullname")

    return args


def _get_command_path(command, poppler_path=None):
    if platform.system() == "Windows":
        command = command + ".exe"

    if poppler_path is not None:
        command = os.path.join(poppler_path, command)

    return command


def _get_poppler_version(command, poppler_path=None):
    command = [_get_command_path(command, poppler_path), "-v"]

    env = os.environ.copy()
    if poppler_path is not None:
        env["LD_LIBRARY_PATH"] = poppler_path + ":" + env.get("LD_LIBRARY_PATH", "")
    proc = Popen(command, env=env, stdout=PIPE, stderr=PIPE)

    out, err = proc.communicate()

    try:
        # TODO: Make this more robust
        return int(
            err.decode("utf8", "ignore").split("\n")[0].split(" ")[-1].split(".")[1]
        )
    except:
        # Lowest version that includes pdftocairo (2011)
        return 17


def pdfinfo_from_path(pdf_path, userpw=None, poppler_path=None):
    try:
        command = [_get_command_path("pdfinfo", poppler_path), pdf_path]

        if userpw is not None:
            command.extend(["-upw", userpw])

        # Add poppler path to LD_LIBRARY_PATH
        env = os.environ.copy()
        if poppler_path is not None:
            env["LD_LIBRARY_PATH"] = poppler_path + ":" + env.get("LD_LIBRARY_PATH", "")
        proc = Popen(command, env=env, stdout=PIPE, stderr=PIPE)

        out, err = proc.communicate()

        d = {}
        for field in out.decode("utf8", "ignore").split("\n"):
            sf = field.split(":")
            key, value = sf[0], ":".join(sf[1:])
            if key != "":
                d[key] = (
                    int(value.strip())
                    if key in PDFINFO_CONVERT_TO_INT
                    else value.strip()
                )

        if "Pages" not in d:
            raise ValueError

        return d

    except OSError:
        raise PDFInfoNotInstalledError(
            "Unable to get page count. Is poppler installed and in PATH?"
        )
    except ValueError:
        raise PDFPageCountError(
            "Unable to get page count.\n%s" % err.decode("utf8", "ignore")
        )


def pdfinfo_from_bytes(pdf_file):
    fh, temp_filename = tempfile.mkstemp()
    try:
        with open(temp_filename, "wb") as f:
            f.write(pdf_file)
            f.flush()
        return pdfinfo_from_path(temp_filename)
    finally:
        os.close(fh)
        os.remove(temp_filename)


def generate_random_string(stringLength=10):
    """Generate a random string of fixed length """
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for i in range(stringLength))


"""
    Define exceptions specific to pdf2html
"""


class PopplerNotInstalledError(Exception):
    """Happens when poppler is not installed"""

    pass


class PDFInfoNotInstalledError(PopplerNotInstalledError):
    """Happens when pdfinfo is not installed"""

    pass


class PDFPageCountError(Exception):
    """Happens when the pdfinfo was unable to retrieve the page count"""

    pass


class PDFSyntaxError(Exception):
    """Syntax error was thrown during rendering"""

    pass


class PDFPopplerError(Exception):
    """Poppler error stream not clean"""

    pass
